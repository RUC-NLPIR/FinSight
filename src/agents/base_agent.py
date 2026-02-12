"""Base agent with save/load/run capabilities."""
from typing import Dict, Any, Union, Optional, Type
import sys
import os
import pickle
import dill
import uuid
import re
import asyncio
from datetime import datetime
from src.config import Config
from src.tools import list_tools, get_tool_by_name
from src.utils import AsyncCodeExecutor, get_logger
from src.tools.base import Tool


_AGENT_REGISTRY: Dict[str, Type['BaseAgent']] = {}

def register_agent_class(agent_class: Type['BaseAgent']):
    _AGENT_REGISTRY[agent_class.AGENT_NAME] = agent_class
    return agent_class

class BaseAgent:
    AGENT_NAME = 'base'
    AGENT_DESCRIPTION = 'base agent'
    NECESSARY_KEYS = ['task']
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, 'AGENT_NAME') and cls.AGENT_NAME != 'base':
            register_agent_class(cls)
    
    def __init__(
        self, 
        config: Config, 
        tools: list[Union[Tool, 'BaseAgent']],
        use_llm_name: str = "deepseek-chat",
        enable_code = True,
        memory = None,
        agent_id: str = None,
    ):
        self.config = config
        self.name = self.AGENT_NAME
        self.type = f'agent_{self.AGENT_NAME}'
        if agent_id is None:
            self.id = f'agent_{self.AGENT_NAME}_{uuid.uuid4().hex[:8]}'
        else:
            self.id = agent_id
        self.state = None
        self.working_dir = os.path.join(self.config.working_dir, 'agent_working', self.id)
        os.makedirs(self.working_dir, exist_ok=True)
        self.cache_dir = os.path.join(self.working_dir, '.cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.enable_code = enable_code
        if self.enable_code:
            self.executor_path = os.path.join(self.working_dir, '.executor_cache')
            os.makedirs(self.executor_path, exist_ok=True)
            self.code_executor = AsyncCodeExecutor(self.executor_path)
            self.executor_state_path = os.path.join(self.executor_path, 'state.dill')
        
        self.use_llm_name = use_llm_name
        self.llm = self.config.llm_dict[use_llm_name]
        self.memory = memory
        
        if tools is None or tools == []:
            self._set_default_tools()
        else:
            self.tools = tools
        for tool in self.tools:
            self.memory.add_dependency(tool.id, self.id)
        self.current_task_data = {}
        self.current_checkpoint = {}
        self._resume_state: Dict[str, Any] | None = None
        self.current_round = 0
        
        # Initialize logger and set agent context
        self.logger = get_logger()
        self.logger.set_agent_context(self.id, self.AGENT_NAME)
    
    def _set_default_tools(self):
        return []

    def _get_persist_extra_state(self) -> Dict[str, Any]:
        """Hook for subclasses to persist additional state."""
        return {}

    def _load_persist_extra_state(self, state: Dict[str, Any]):
        """Hook for subclasses to restore extra state."""
        return
    
    @classmethod
    async def from_checkpoint(
        cls,
        config: Config,
        memory,
        agent_id: str,
        checkpoint_name: str = 'latest.pkl',
        tools: Optional[list] = None,
        restored_agents: Optional[Dict[str, 'BaseAgent']] = None,
        **kwargs
    ) -> Optional['BaseAgent']:
        """Restore an agent from a checkpoint."""
        if restored_agents is None:
            restored_agents = {}
        
        # Return immediately if already restored
        if agent_id in restored_agents:
            return restored_agents[agent_id]
        
        # Build checkpoint path
        working_dir = os.path.join(config.working_dir, 'agent_working', agent_id)
        cache_dir = os.path.join(working_dir, '.cache')
        checkpoint_path = os.path.join(cache_dir, checkpoint_name)
        
        logger = get_logger()
        
        if not os.path.exists(checkpoint_path):
            # Try alternative checkpoints
            if not os.path.exists(cache_dir):
                logger.warning(
                    f"Cache directory not found for agent {agent_id}: {cache_dir}"
                )
                return None
            
            other_checkpoints = [f for f in os.listdir(cache_dir) if f.endswith('.pkl')]
            if other_checkpoints:
                checkpoint_path = os.path.join(cache_dir, other_checkpoints[0])
                logger.info(
                    f"Using alternative checkpoint for agent {agent_id}: "
                    f"{checkpoint_path} (requested: {checkpoint_name})"
                )
            else:
                logger.warning(
                    f"No checkpoint file found for agent {agent_id}: "
                    f"requested={checkpoint_name}, cache_dir={cache_dir}, "
                    f"available_files={os.listdir(cache_dir) if os.path.exists(cache_dir) else 'N/A'}"
                )
                return None
        
        # Load checkpoint
        try:
            with open(checkpoint_path, 'rb') as f:
                state = dill.load(f)
        except Exception as e1:
            try:
                with open(checkpoint_path, 'rb') as f:
                    state = pickle.load(f)
            except Exception as e2:
                logger.error(
                    f"Failed to load checkpoint for agent {agent_id}: "
                    f"path={checkpoint_path}, "
                    f"dill_error={type(e1).__name__}: {e1}, "
                    f"pickle_error={type(e2).__name__}: {e2}"
                )
                return None
        
        agent_name = state.get('agent_name')
        if not agent_name:
            logger.warning(
                f"Checkpoint for agent {agent_id} has no agent_name: "
                f"path={checkpoint_path}"
            )
            return None
        
        # Lookup agent class from registry
        agent_class = _AGENT_REGISTRY.get(agent_name)
        if not agent_class:
            logger.warning(
                f"Agent class not found in registry for agent {agent_id}: "
                f"agent_name={agent_name}, "
                f"available_agents={list(_AGENT_REGISTRY.keys())}"
            )
            return None
        
        # Restore dependent tools if not provided
        if tools is None:
            tools = await cls._restore_tools_from_checkpoint(
                config, memory, state, checkpoint_name, restored_agents, **kwargs
            )
        
        # Restore persisted parameters
        checkpoint_use_llm_name = state.get('use_llm_name', 'deepseek-chat')
        use_llm_name = kwargs.get('use_llm_name', checkpoint_use_llm_name)
        
        # Restore additional init kwargs
        init_params = state.get('init_params', {})
        for key, value in init_params.items():
            if key not in kwargs:
                kwargs[key] = value
        
        # Instantiate agent
        agent = agent_class(
            config=config,
            memory=memory,
            agent_id=agent_id,
            use_llm_name=use_llm_name,
            tools=tools,
            **{k: v for k, v in kwargs.items() if k != 'use_llm_name'}
        )
        
        # Restore runtime state
        agent._resume_state = state
        agent.current_checkpoint = state
        agent.current_task_data = state.get('current_task_data', {})
        
        # Ensure logger context is configured
        agent.logger.set_agent_context(agent.id, agent.AGENT_NAME)
        
        # Restore executor state
        if agent.enable_code and os.path.exists(agent.executor_state_path):
            try:
                with open(agent.executor_state_path, 'rb') as ef:
                    exec_state = ef.read()
                agent.code_executor.load_state(exec_state)
            except Exception as e:
                agent.logger.error(f"Failed to load code-executor state: {e}", exc_info=True)
        
        # Restore subclass-specific state
        agent._load_persist_extra_state(state)
        
        restored_agents[agent_id] = agent
        return agent
    
    @classmethod
    async def _restore_tools_from_checkpoint(
        cls,
        config: Config,
        memory,
        state: Dict[str, Any],
        checkpoint_name: str,
        restored_agents: Dict[str, 'BaseAgent'],
        **kwargs
    ) -> list:
        """Restore tools from checkpoint state."""
        from src.tools import get_tool_by_name
        
        tool_dependencies = state.get('tool_dependencies', [])
        restored_tools = []
        logger = get_logger()
        
        for dep in tool_dependencies:
            if dep['type'] == 'agent':
                # Recursively restore dependent agents
                # First, attempt to load the dependency's checkpoint to fetch init_params
                dep_agent_id = dep['agent_id']
                dep_working_dir = os.path.join(config.working_dir, 'agent_working', dep_agent_id)
                dep_cache_dir = os.path.join(dep_working_dir, '.cache')
                dep_checkpoint_path = os.path.join(dep_cache_dir, checkpoint_name)
                
                # If the specified checkpoint is missing, fall back to any available one
                if not os.path.exists(dep_checkpoint_path):
                    if os.path.exists(dep_cache_dir):
                        other_checkpoints = [f for f in os.listdir(dep_cache_dir) if f.endswith('.pkl')]
                        if other_checkpoints:
                            dep_checkpoint_path = os.path.join(dep_cache_dir, other_checkpoints[0])
                
                # Read dependency checkpoint to fetch its parameters
                dep_kwargs = {}
                if os.path.exists(dep_checkpoint_path):
                    try:
                        with open(dep_checkpoint_path, 'rb') as f:
                            dep_state = dill.load(f)
                        dep_init_params = dep_state.get('init_params', {})
                        # Only pass supported parameters; always forward use_llm_name (can be overridden)
                        dep_kwargs['use_llm_name'] = kwargs.get('use_llm_name', dep_init_params.get('use_llm_name'))
                        # Forward additional options if present in the dependency checkpoint
                        for key in ['use_vlm_name', 'use_embedding_name', 'enable_code']:
                            if key in dep_init_params:
                                dep_kwargs[key] = dep_init_params[key]
                    except Exception as e:
                        logger.warning(
                            f"Failed to load dependency agent checkpoint for {dep_agent_id}: {e}, "
                            f"using default kwargs"
                        )
                        # On failure, fall back to common kwargs
                        dep_kwargs['use_llm_name'] = kwargs.get('use_llm_name')
                else:
                    # Use generic kwargs if no checkpoint exists
                    dep_kwargs['use_llm_name'] = kwargs.get('use_llm_name')
                
                dep_agent = await cls.from_checkpoint(
                    config=config,
                    memory=memory,
                    agent_id=dep_agent_id,
                    checkpoint_name=checkpoint_name,
                    restored_agents=restored_agents,
                    **dep_kwargs
                )
                if dep_agent:
                    restored_tools.append(dep_agent)
            elif dep['type'] == 'tool':
                # Recreate tool instance
                tool_instance = get_tool_by_name(dep['tool_name'])()
                if tool_instance.id != dep['tool_id']:
                    tool_instance.id = dep['tool_id']
                restored_tools.append(tool_instance)
        
        return restored_tools

    async def save(self, state: Dict[str, Any] | None = None, checkpoint_name: str = 'latest.pkl'):
        """Persist the current agent state to a checkpoint."""
        # Capture tool dependencies (agent/tool identifiers)
        tool_dependencies = []
        for tool in self.tools:
            if isinstance(tool, BaseAgent):
                tool_dependencies.append({
                    'type': 'agent',
                    'agent_name': tool.AGENT_NAME,
                    'agent_id': tool.id,
                })
            elif isinstance(tool, Tool):
                tool_dependencies.append({
                    'type': 'tool',
                    'tool_name': tool.name,
                    'tool_id': tool.id,
                })
        
        # Persist relevant initialization parameters
        init_params = {}
        for key in ['use_llm_name', 'enable_code', 'use_vlm_name', 'use_embedding_name']:
            if hasattr(self, key):
                init_params[key] = getattr(self, key)
        
        checkpoint = {
            'agent_name': self.AGENT_NAME,
            'agent_id': self.id,
            'use_llm_name': self.use_llm_name,
            'current_time': self.current_time,
            'current_task_data': getattr(self, 'current_task_data', {}),
            'tool_dependencies': tool_dependencies,
            'init_params': init_params,
        }

        if state:
            self.current_checkpoint.update(state)
        checkpoint.update(self.current_checkpoint)
        target_path = os.path.join(self.cache_dir, checkpoint_name)
        tmp_path = target_path + '.tmp'
        try:
            with open(tmp_path, 'wb') as f:
                dill.dump(checkpoint, f)
            os.replace(tmp_path, target_path)
        except Exception:
            with open(tmp_path, 'wb') as f:
                pickle.dump(checkpoint, f)
            os.replace(tmp_path, target_path)

        # Save code-executor state
        if self.enable_code and hasattr(self, 'code_executor'):
            try:
                state_bytes = self.code_executor.save_state()
                with open(self.executor_state_path, 'wb') as ef:
                    ef.write(state_bytes)
            except Exception as e:
                self.logger.error(f"Failed to save code-executor state: {e}", exc_info=True)

    async def load(self, checkpoint_name: str = 'latest.pkl') -> Dict[str, Any] | None:
        """Load state from a checkpoint."""
        target_path = os.path.join(self.cache_dir, checkpoint_name)
        if not os.path.exists(target_path):
            return None
        try:
            with open(target_path, 'rb') as f:
                state = dill.load(f)
        except Exception:
            with open(target_path, 'rb') as f:
                state = pickle.load(f)
        self.state = state
        # Restore essential fields
        self.current_task_data = state.get('current_task_data', {})
        # Restore code-executor state
        if self.enable_code and hasattr(self, 'code_executor') and os.path.exists(self.executor_state_path):
            try:
                with open(self.executor_state_path, 'rb') as ef:
                    exec_state = ef.read()
                self.code_executor.load_state(exec_state)
                # Ensure helper functions are re-registered
                self.code_executor.set_variable("call_tool", self._agent_tool_function)
            except Exception as e:
                self.logger.error(f"Failed to load code-executor state: {e}", exc_info=True)
        return state

    async def _prepare_executor(self):
        if self.enable_code:
            self.code_executor.set_variable("call_tool", self._agent_tool_function)

    async def _prepare_init_prompt(self, input_data: dict) -> list[dict]:
        raise NotImplementedError
    

    def _agent_tool_function(self, tool_name: str = None, **kwargs):
        """Execute a tool by name.

        This function is injected into the code-executor's global namespace so
        that LLM-generated code can call tools synchronously via
        ``call_tool(tool_name='...', **kwargs)``.

        Because it runs inside ``exec()`` which is already nested in a running
        asyncio event loop, we must **not** call ``asyncio.run()`` (that would
        deadlock or raise ``RuntimeError``).  Instead we delegate to an
        ``AsyncBridge`` that owns a separate background event loop.
        """
        from src.utils.async_bridge import get_async_bridge

        if tool_name is None:
            raise ValueError("tool_name is required")
        target_tool = None
        for tool in self.tools:
            if isinstance(tool, Tool):
                if tool.name == tool_name:
                    target_tool = tool
                    break
            elif isinstance(tool, BaseAgent):
                if tool.AGENT_NAME == tool_name:
                    target_tool = tool
                    break
        if target_tool is None:
            self.logger.warning(f"No available tools for tool_name: {tool_name}")
            self.memory.add_log(self.id, None, kwargs, [], error=True, note=f"No available tools for tool_name: {tool_name}")
            return []

        bridge = get_async_bridge()

        try:
            if issubclass(type(target_tool), BaseAgent):
                if 'task' not in kwargs:
                    kwargs['task'] = self.current_task_data['task']
                response = bridge.run_async(target_tool.async_run(input_data=kwargs))
                response = response['final_result']
                self.memory.add_log(target_tool.id, target_tool.type, kwargs, response, error=False, note=f"Tool {target_tool.name} executed successfully")
                return response
            elif issubclass(type(target_tool), Tool):
                response = bridge.run_async(target_tool.api_function(**kwargs))
                sources = [item.source for item in response]
                data_list = [item.data for item in response]
                sources = "\n".join(sources)
                import sys
                display_note = f"[Tool Result Overview] Gather {len(response)} Tool Results.\n"
                for i, item in enumerate(response):
                    display_note += f"-{i}. Name: {item.name}\nSource: {item.source}\n"
                print(f"\n\n{display_note}\n\n", file=sys.stdout, flush=True)

                self.memory.add_log(target_tool.id, target_tool.type, kwargs, response, error=False, note=f"Tool {target_tool.name} executed successfully")
                return data_list
            else:
                self.logger.warning(f"Unknown tools: {tool_name}")
                self.memory.add_log(self.id, target_tool.type, kwargs, [], error=True, note=f"Unknown tools: {tool_name}")
                return []
        except Exception as e:
            self.logger.error(f"Tool {tool_name} execution failed: {e}", exc_info=True)
            self.memory.add_log(self.id, target_tool.type, kwargs, [], error=True, note=f"Tool {tool_name} executed failed: {e}")
            return []
    
    def _get_api_descriptions(self) -> str:
        desc = 'The usage of tool calling: `tool_result = call_tool(tool_name=\'tool_name\', **kwargs)`. (you can use custom variable names for the tool result)\n\n'
        desc += 'Below are the tools and their descriptions:\n\n'
        for tool in self.tools:
            if issubclass(type(tool), Tool):
                desc += f"- Tool: {tool.name}\nDescription: {tool.description}\nParameters: {tool.parameters}\n\nOutput: "
            elif issubclass(type(tool), BaseAgent):
                desc += f"- Tool: {tool.AGENT_NAME}\nDescription: {tool.AGENT_DESCRIPTION}\n\n"
        desc += 'The result of each tool is a varaible, please use `print` to print the result.'
        return desc
    
    def _check_necessary_data(self, input_data):
        check_keys = self.NECESSARY_KEYS
        for key in check_keys:
            if key not in input_data:
                self.logger.warning(f"{key} not in input_data")

    async def async_run(
        self, 
        input_data: dict, 
        max_iterations: int = 10,
        stop_words: list[str] = ["</execute>", "</final_result>"],
        echo=False,
        resume: bool = False,
        checkpoint_name: str = 'latest.pkl',
        prompt_function=None,
    ) -> dict:
        """Main execution loop."""
        # Ensure logger context is set (important for asyncio execution)
        self.logger.set_agent_context(self.id, self.AGENT_NAME)
        
        self._check_necessary_data(input_data)
        self.current_task_data = input_data
        await self._prepare_executor()

        # Restore or initialize conversation state
        conversation_history: list[dict]
        current_round: int
        if prompt_function is None:
            prompt_function = self._prepare_init_prompt
        if resume:
            state = await self.load(checkpoint_name=checkpoint_name)
            if state is not None:
                conversation_history = state.get('conversation_history', [])
                current_round = int(state.get('current_round', 0))
                if 'return_dict' in state:
                    return state['return_dict']
            else:
                conversation_history = await prompt_function(input_data)
                current_round = 0
        else:
            conversation_history = await prompt_function(input_data)
            current_round = 0
    
        while current_round < max_iterations+1:
            self.logger.info(f"Iteration {current_round + 1}")
            current_round += 1
            self.current_round = current_round
            response = await self.llm.generate(messages = conversation_history, stop=stop_words)
            action_type, action_content = self._parse_llm_response(response)
            if echo:
                self.logger.info(f"LLM response this step: {response}")
                self.logger.info("--------")
            # Execute asynchronously
            action_result = await self._execute_action(action_type, action_content)
            action_result['llm_response'] = response
            if echo:
                self.logger.info(f"Action result this step: {action_result['result']}")
                self.logger.info("--------")
            conversation_history.append({"role": "assistant", "content": action_result['llm_response']})
            conversation_history.append({"role": "user", "content": action_result['result']})
            self.logger.debug("--Begin of Execution Result--")
            self.logger.debug(action_result['result'])
            self.logger.debug("--End of Execution Result--")

            # Save each iteration to support resume
            current_state = {
                'conversation_history': conversation_history,
                'current_round': current_round,
                'input_data': input_data,
                'stop_words': stop_words,
            }
            current_state.update(self._get_persist_extra_state())
            self.state = current_state
            await self.save(
                state=current_state,
                checkpoint_name=checkpoint_name,
            )
            
            if not action_result['continue']:
                break
        
        return_dict = {}
        if current_round >= max_iterations and action_result['continue']:
            # Hit iteration limit; fall back to summary handler
            return_dict = await self._handle_max_round(conversation_history)
        else:
            return_dict = {
                'conversation_history': conversation_history,
                'final_result': action_result['result'],
            }
        return_dict['input_data'] = input_data
        return_dict['working_dir'] = self.working_dir
        # Save final state before exiting
        current_state = {
            'conversation_history': conversation_history,
            'current_round': current_round,
            'input_data': input_data,
            'stop_words': stop_words,
            'return_dict': return_dict,
        }
        current_state.update(self._get_persist_extra_state())
        await self.save(
            state=current_state,
            checkpoint_name=checkpoint_name,
        )
        self.memory.save()
        
        return return_dict

    async def _handle_max_round(self, conversation_history):
        return {'coversation_history': conversation_history, 'final_result': conversation_history[-1]['content']}

    def _parse_llm_response(self, response: str) -> tuple[str, str]:
        """Parse the LLM response to extract action tags."""
        response = response.replace("<thinking>", "\n").replace("</thinking>", "\n")
        response = response.replace("<think>", "\n").replace("</think>", "\n")
        pattern = re.compile(r"<([\w_]+)>(.*?)</\1>", re.DOTALL)
        matches = list(pattern.finditer(response))
        
        if not matches:
            return "final", response
        match = matches[-1]

        tag_name = match.group(1)
        if tag_name == 'execute':
            tag_name = 'code'
        if tag_name == 'final_result':
            tag_name = 'final'
        content_string = match.group(2).strip()  # Remove surrounding whitespace

        return tag_name, content_string

    
    async def _execute_action(self, action_type: str, action_content: str):
        handler_method_name = f"_handle_{action_type}_action"
        handler = getattr(self, handler_method_name, None)

        if handler and callable(handler):
            return await handler(action_content)
        else:
            return await self._handle_default_action(action_type, action_content)
    

    async def _handle_code_action(self, action_content: str):
        code_result = await self.code_executor.execute(code=action_content)
        code_result = self._format_execution_result(code_result)
        return {
            "action": "generate_code",
            "action_content": action_content,
            "result": code_result,
            "continue": True,
        }

    async def _handle_final_action(self, action_content: str):
        return {
            "action": "final_result",
            "action_content": action_content,
            "result": action_content,
            "continue": False,
        }

    async def _handle_default_action(self, action_type: str, action_content: str):
        return {
            "action": "invalid_response",
            "action_content": action_content,
            "result": f"Unknown action_type '{action_type}'. Please respond using the required XML tags.",
            "continue": True,
        }
     
        
    def _format_execution_result(self, result: Dict[str, Any]) -> str:
        feedback = []

        if result["error"] is False:
            feedback.append("Code execution: success\n")

            if result["stdout"]:
                feedback.append(f"Console output:\n{result['stdout']}\n\n")

            if result.get("variables"):
                feedback.append("New variables:")
                for var_name, var_info in result["variables"].items():
                    feedback.append(f"  - {var_name}: {var_info}")
            if result.get("additional_notes"):
                feedback.append(f"Additional notes: {result['additional_notes']}\n")
        else:
            feedback.append("Code execution: failed\n")
            if result["stderr"]:
                feedback.append(f"Error message: {result['stderr']}\n")
            if result["stdout"]:
                feedback.append(f"Partial output: {result['stdout']}\n")
        return "\n".join(feedback)    
        
        
        
