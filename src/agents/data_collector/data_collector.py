from typing import List, Dict, Any, Tuple
import asyncio
from src.agents.base_agent import BaseAgent
from src.agents import DeepSearchAgent
from src.tools import ToolResult, get_tool_categories, get_tool_by_name


class DataCollector(BaseAgent):
    AGENT_NAME = 'data_collector'
    AGENT_DESCRIPTION = 'a agent that can collect data from the internet and variable apis'
    NECESSARY_KEYS = ['task']
    def __init__(
        self,
        config,
        tools = [],
        use_llm_name: str = "deepseek-chat",
        enable_code = True,
        memory = None,
        agent_id: str = None
    ):
        super().__init__(
            config=config,
            tools=tools,
            use_llm_name=use_llm_name,
            enable_code=enable_code,
            memory=memory,
            agent_id=agent_id
        )
        # Load prompts using the new YAML-based loader
        from src.utils.prompt_loader import get_prompt_loader
        
        self.prompt_loader = get_prompt_loader('data_collector', report_type='general')
        self.DATA_COLLECT_PROMPT = self.prompt_loader.get_prompt('data_collect')
        
        self.collected_data_list: List[ToolResult] = []
        if self.tools == []:
            self._set_default_tools()
        

    def _set_default_tools(self):
        """
        Attach default tools (search agent + API wrappers).
        """
        tool_list = []
        # Include the deep-search agent (sharing the same memory)
        tool_list.append(DeepSearchAgent(config=self.config, use_llm_name=self.use_llm_name, memory=self.memory))
        # Attach other API tools
        for tool_type, tool_name_list in get_tool_categories().items():
            if tool_type == 'web':
                continue
            for tool_name in tool_name_list:
                tool_instance = get_tool_by_name(tool_name)()
                tool_list.append(tool_instance)
        for tool in tool_list:
            self.memory.add_dependency(tool.id, self.id)
        self.tools = tool_list
        try:
            self.logger.info(f"Initialized default tools: total {len(tool_list)} items")
        except Exception:
            pass
        

    async def _prepare_executor(self):
        # Expose helper functions to the code executor for LLM-generated code
        self.code_executor.set_variable("call_tool", self._agent_tool_function)
        self.code_executor.set_variable("save_result", self._save_result)

    def _save_result(self, var: Any, result_name: str, result_description: str, data_source: str):
        """Persist execution results into self.collected_data_list."""
        self.memory.add_data(ToolResult(
            name=result_name,
            description=result_description,
            data=var,
            source=data_source
        ))
        self.collected_data_list.append(ToolResult(
            name=result_name,
            description=result_description,
            data=var,
            source=data_source
        ))
        try:
            self.logger.info(f"Saved collect result: {result_name} (source={data_source})")
        except Exception:
            pass
    
    async def _prepare_init_prompt(self, input_data: dict) -> list[dict]:
        task = input_data.get('task')
        if not task:
            raise ValueError("Input data must contain a 'task' key.")
        
        # Get target language from config
        target_language = self.config.config.get('language', 'zh')
        language_mapping = {
            'zh': 'Chinese (中文)',
            'en': 'English'
        }
        target_language_name = language_mapping.get(target_language, target_language)
        
        # Extract research target from task
        target_name = self.config.config.get('target_name', '')
        stock_code = self.config.config.get('stock_code', '')
        research_target = f"{target_name} (ticker: {stock_code})" if stock_code else target_name
            
        return [{
            "role": "user",
            "content": self.DATA_COLLECT_PROMPT.format(
                api_descriptions=self._get_api_descriptions(),
                current_time=self.current_time,
                task=task,
                target_language=target_language_name,
                research_target=research_target
            )
        }]
    

    async def async_run(
        self, 
        input_data: dict, 
        max_iterations: int = 10,
        stop_words: list[str] = [],
        echo=False,
        resume: bool = True,
        checkpoint_name: str = 'latest.pkl',
        # stop_words: list[str] = ["</execute>", "</final_result>"]
    ) -> dict:
        # Reset collected-data cache for each run
        self.collected_data_list = []
        self.logger.info(f"DataCollector started: task={input_data.get('task','')} resume={resume}")
 
        run_result = await super().async_run(
            input_data=input_data,
            max_iterations=max_iterations,
            stop_words=stop_words,
            echo=echo,
            resume=resume,
            checkpoint_name=checkpoint_name,
        )
        run_result['collected_data_list'] = self.collected_data_list
        for item in self.collected_data_list:
            self.memory.add_data(item)
        self.logger.info(f"Successfully save {len(self.collected_data_list)} items to memory")
        self.memory.add_log(
            id=self.id,
            type=self.type,
            input_data=input_data,
            output_data=self.collected_data_list,
            error=False,
            note=f"DataCollector finished: collected={len(self.collected_data_list)} items"
        )
        self.logger.info(f"DataCollector finished: collected={len(self.collected_data_list)} items")
        self.memory.save()
        return run_result

    def _get_persist_extra_state(self) -> Dict[str, Any]:
        return {
            'collected_data_list': self.collected_data_list,
        }

    def _load_persist_extra_state(self, state: Dict[str, Any]):
        self.collected_data_list = state.get('collected_data_list', [])
