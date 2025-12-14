import os
import re
import json
import json_repair
import dill
from typing import List, Dict, Any, Tuple
import asyncio
from threading import Semaphore
from src.agents.base_agent import BaseAgent
from src.agents import DeepSearchAgent
from src.tools import ToolResult
from src.utils import IndexBuilder
from src.utils import image_to_base64

# TODO: Break parameter passing into explicit arguments
# TODO: Standardize I/O structures as lightweight classes

class DataAnalyzer(BaseAgent):
    AGENT_NAME = 'data_analyzer'
    AGENT_DESCRIPTION = 'a agent that can analyze data and generate report'
    NECESSARY_KEYS = ['task', 'analysis_task']

    def __init__(
        self,
        config,
        tools = [],
        use_llm_name: str = "deepseek-chat",
        use_vlm_name: str = "qwen/qwen3-vl-235b-a22b-instruct",
        use_embedding_name: str = 'qwen/qwen3-embedding-0.6b',
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
        if self.tools == []:
            self._set_default_tools()

        # Load prompts using the new YAML-based loader
        from src.utils.prompt_loader import get_prompt_loader
        target_type = self.config.config['target_type']
        self.prompt_loader = get_prompt_loader('data_analyzer', report_type=target_type)
        
        # Store prompts as instance attributes for easy access
        self.DATA_ANALYSIS_PROMPT = self.prompt_loader.get_prompt('data_analysis')
        self.DATA_ANALYSIS_PROMPT_WO_CHART = self.prompt_loader.get_prompt('data_analysis_wo_chart')
        self.DATA_API_PROMPT = self.prompt_loader.get_prompt('data_api')
        self.REPORT_DRAFT_PROMPT = self.prompt_loader.get_prompt('report_draft')
        self.REPORT_DRAFT_PROMPT_WO_CHART = self.prompt_loader.get_prompt('report_draft_wo_chart')
        self.DRAW_CHART_PROMPT = self.prompt_loader.get_prompt('draw_chart')
        self.VLM_CRITIQUE_PROMPT = self.prompt_loader.get_prompt('vlm_critique')

        self.use_vlm_name = use_vlm_name
        self.vlm = self.config.llm_dict[use_vlm_name]
        self.use_embedding_name = use_embedding_name
        self.current_phase = 'phase1'
 
        self.image_save_dir = os.path.join(self.working_dir, "images")
        os.makedirs(self.image_save_dir, exist_ok = True)
    
    def _set_default_tools(self):
        """
        Attach the default tools needed by the analyzer (search agent, etc.).
        """
        tool_list = []
        tool_list.append(DeepSearchAgent(config=self.config, use_llm_name=self.use_llm_name, memory=self.memory))
        for tool in tool_list:
            self.memory.add_dependency(tool.id, self.id)
        self.tools = tool_list

    async def _prepare_executor(self):
        current_task_data = self.current_task_data
        tool_list = self.tools
        collect_data_list = self.memory.get_collect_data()
        def _get_existed_data(data_id: int):
            return collect_data_list[data_id].data
        def _get_deepsearch_result(query: str):
            ds_agent = tool_list[0]
            output =  asyncio.run(ds_agent.async_run(input_data={
                'task': current_task_data['task'],
                'query': query
            }))
            output = output['final_result']
            return output
        
        self.code_executor.set_variable("session_output_dir", self.image_save_dir)
        self.code_executor.set_variable("collect_data_list", [item.data for item in collect_data_list])
        self.code_executor.set_variable("get_data_from_deep_search", _get_deepsearch_result)
        self.code_executor.set_variable("get_existed_data", _get_existed_data)

        custom_palette = [
            "#8B0000",  # deep crimson
            "#FF2A2A",  # bright red
            "#FF6A4D",  # orange-red
            "#FFDAB9",  # pale peach
            "#FFF5E6",  # cream
            "#FFE4B5",  # beige
            "#A0522D",  # sienna
            "#5C2E1F",  # dark brown
        ]
        self.code_executor.set_variable("custom_palette", custom_palette)
        await self.code_executor.execute("import seaborn as sns\nsns.set_palette(custom_palette)")
    
    async def _prepare_init_prompt(self, input_data: dict) -> list[dict]:
        task = input_data['task']
        enable_chart = input_data['enable_chart']
        collect_data_list = self.memory.get_collect_data()
        analysis_task = f"Global Research Objective: {task}\n\nAnalysis Task: {input_data['analysis_task']}"
        data_info = await self._format_collect_data(analysis_task, collect_data_list)

        # Get target language from config
        target_language = self.config.config.get('language', 'zh')
        # Convert language code to full name for clarity in prompt
        language_mapping = {
            'zh': 'Chinese (中文)',
            'en': 'English'
        }
        target_language_name = language_mapping.get(target_language, target_language)

        if enable_chart:
            prompt = self.DATA_ANALYSIS_PROMPT.format(
                api_descriptions=self.DATA_API_PROMPT,
                data_info=data_info,
                current_time=self.current_time,
                user_query=analysis_task,
                target_language=target_language_name
            )
        else:
            prompt = self.DATA_ANALYSIS_PROMPT_WO_CHART.format(
                api_descriptions=self.DATA_API_PROMPT,
                data_info=data_info,
                current_time=self.current_time,
                user_query=analysis_task,
                target_language=target_language_name
            )
        return [{"role": "user", "content": prompt}]
    
    async def _format_collect_data(self, analysis_task, collect_data_list):
        """
        Format collected datasets into a readable string for the prompt.
        """
        # search_result = await self.memory.retrieve_relevant_data(analysis_task, top_k=10, embedding_model=self.use_embedding_name)
        # formatted_data = ""
        # if len(search_result) > 0:
        #     for idx,item in enumerate(search_result):
        #         formatted_data += f"Data (id:{idx}):\n{collect_data_list[idx].brief_str()}\n\n"
        # else:
        #     for idx,item in enumerate(collect_data_list):
        #         formatted_data += f"Data (id:{idx}):\n{item.brief_str()}\n\n"

        formatted_data = ""
        for idx,item in enumerate(collect_data_list):
            formatted_data += f"Data (id:{idx}):\n{item.brief_str()}\n\n"
            
        return formatted_data
    
    async def _handle_report_action(self, action_content: str):
        """Handle a 'final' action from the LLM."""
        return {
            "action": "final_report",
            "action_content": action_content,
            "result": action_content,
            "continue": False,
        }
    
    async def _handle_max_round(self, conversation_history):
        conversation_history = [item["content"] for item in conversation_history]
        analysis_info = "\n\n".join(conversation_history)
        
        # Get target language from config
        target_language = self.config.config.get('language', 'zh')
        language_mapping = {
            'zh': 'Chinese (中文)',
            'en': 'English'
        }
        target_language_name = language_mapping.get(target_language, target_language)
        
        if self.enable_chart:
            prompt = self.REPORT_DRAFT_PROMPT.format(
                current_time = self.current_time,
                analysis_info = analysis_info,
                target_language = target_language_name
            )
        else:
            prompt = self.REPORT_DRAFT_PROMPT_WO_CHART.format(
                current_time = self.current_time,
                analysis_info = analysis_info,
                target_language = target_language_name
            )
        response = await self.llm.generate(
            messages = [
                {"role": "user", "content": prompt}
            ],
            response_format = {"type": "json_object"}
        )
        match = re.search(r'```json([\s\S]*?)```', response)
        if match:
            response = match.group(1).strip()
        try:
            report = json_repair.loads(response)
            report_title = report["title"]
            report_content = report["content"]
            final_result = f'# {report_title}\n{report_content}'
        except Exception:
            final_result = response
        return {'coversation_history': conversation_history, 'final_result': final_result}
    
    def _parse_generated_report(self, response: str):
        basic_task = self.current_task_data['task']
        analysis_task = self.current_task_data['analysis_task']
        report_content = response
        report_title = f"{analysis_task}"

        try:
            split_report_content = report_content.split("\n")
            for idx, line in enumerate(split_report_content):
                if idx > 5:
                    continue
                if line.startswith("#"):
                    report_title = line.strip("#")
                    break
        except Exception:
            pass
        return report_title, report_content
    
    async def _draw_chart(self, input_data, run_data: dict, max_iterations: int = 3):
        report_content = run_data["report_content"]
        analysis_task = input_data['analysis_task']
        chart_names = re.findall(r'@import\s+"(.*?)"', report_content)
        current_variables = self.code_executor.get_environment_info()
        
        name_mapping = {}  # long chart name -> short filename
        name_description_mapping = {}  # long chart name -> description
        chart_code_mapping = {}  # long chart name -> code snippet
        
        # Concurrency control semaphore
        charts_completed = set()
        # Load chart-stage checkpoint if available
        charts_ckpt = await self.load(checkpoint_name='charts.pkl')
        if charts_ckpt is not None:
            charts_state = charts_ckpt.get('charts_state', {})
            charts_completed = set(charts_state.get('completed', []))
            name_mapping.update(charts_state.get('name_mapping', {}))
            name_description_mapping.update(charts_state.get('name_description_mapping', {}))
            chart_code_mapping.update(charts_state.get('chart_code_mapping', {}))

        for long_chart_name in chart_names:
            if long_chart_name in charts_completed:
                continue
            # TODO: Shared environments need isolation; temporarily limit concurrency to 1
            with Semaphore(1):
                new_chart_code, new_chart_name = await self._draw_single_chart(
                    task = analysis_task,
                    report_content = report_content,
                    chart_name = long_chart_name,
                    current_variables = current_variables, 
                    max_iterations = max_iterations
                )
                name_mapping[long_chart_name] = new_chart_name
                chart_code_mapping[long_chart_name] = new_chart_code
                charts_completed.add(long_chart_name)
                # Save progress after each completed chart (chart-specific checkpoint)
                await self.save(
                    state={
                        'charts_state': {
                            'completed': list(charts_completed),
                            'name_mapping': name_mapping,
                            'name_description_mapping': name_description_mapping,
                            'chart_code_mapping': chart_code_mapping,
                        }
                    },
                    checkpoint_name='charts.pkl',
                )
        
        for long_chart_name, new_chart_name in name_mapping.items():
            chart_des = await self._generate_description(new_chart_name)
            name_description_mapping[long_chart_name] = chart_des
            # Persist updated description mapping
            await self.save(
                state={
                    'charts_state': {
                        'completed': list(charts_completed),
                        'name_mapping': name_mapping,
                        'name_description_mapping': name_description_mapping,
                        'chart_code_mapping': chart_code_mapping,
                    }
                },
                checkpoint_name='charts.pkl',
            )

        return chart_code_mapping, name_mapping, name_description_mapping
    
    
    async def _generate_description(self, chart_name: str) -> str:
        chart_name_path = os.path.join(self.image_save_dir, chart_name)
        image_b64 = image_to_base64(chart_name_path)
        if not image_b64:
            return ""
        
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": "Give a short description  as the caption of this chart, explaining the key data points and takeaways. Your response should be less than 100 words. Don't output any other words."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ]}
        ]
        response = await self.vlm.generate(
            messages = messages
        )
        return response
    

    async def _draw_single_chart(
        self, 
        task: str,
        report_content: str,
        chart_name: str, 
        current_variables: str,
        max_iterations: int = 3
    ) -> str:
        """
        Run iterative “code generation → VLM critique” cycles for a single chart.
        """
        
        init_prompt = self.DRAW_CHART_PROMPT.format(
            task=task,
            content=report_content,
            chart_name=chart_name,
            data=current_variables       
        )
        
        conversation_history = [
            {"role": "user", "content": init_prompt}
        ]
        
        last_successful_code = ""
        last_successful_chart_path = ""
        self.logger.info(f"Start drawing chart: {chart_name}")
        
        # --- Main VLM evaluation loop ---
        for iteration in range(max_iterations):
            self.logger.info(f"Iteration {iteration + 1}")
            
            # --- Phase 1: generate/execute code (up to 3 retries) ---
            chart_code, chart_filepath = await self._generate_and_execute_code(
                conversation_history
            )
            self.logger.info(f"chart_code: {chart_code}")
            self.logger.info(f"chart_filepath: {chart_filepath}")
            if not chart_filepath:
                return last_successful_code, os.path.basename(last_successful_chart_path) if last_successful_chart_path else ""
            self.logger.info("Image generation succeeded")
            last_successful_code = chart_code
            last_successful_chart_path = chart_filepath

            # --- Phase 2: VLM evaluation ---
            image_b64 = image_to_base64(chart_filepath)
            if not image_b64:
                return last_successful_code, os.path.basename(last_successful_chart_path)
            critic_response = await self.vlm.generate(
                messages=[
                    {"role": "user", "content": self.VLM_CRITIQUE_PROMPT.format(
                        task=task,
                        content=report_content,
                        code_snippet=chart_code
                    )},
                    {"role": "user", "content": [
                        {"type": "text", "text": f"Here is the chart generated in iteration {iteration + 1}."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                    ]}
                ],
            )
            self.logger.info("Image critic succeeded")
            if 'FINISH' in critic_response:
                return last_successful_code, os.path.basename(last_successful_chart_path)
            
            conversation_history.append({"role": "assistant", "content": last_successful_code})
            feedback_for_llm = (
                "The chart above was produced from your previous code. A visualization expert shared the critique below:\n\n"
                f"{critic_response}\n\n"
                "Please write new Python code to address every issue and generate an improved chart. "
                f"Overwrite the previous file '{os.path.basename(last_successful_chart_path)}'."
            )
            conversation_history.append({"role": "user", "content": feedback_for_llm})

        return last_successful_code, os.path.basename(last_successful_chart_path)


    async def _generate_and_execute_code(self, conversation_history: list) -> tuple[str | None, str | None]:
        """
        Attempt (up to three times) to generate and execute the chart code.

        Returns:
            (llm_response, chart_filepath) on success; otherwise (None, None).
        """
        for _ in range(3):  # internal retries
            self.logger.info(f"Generating code, attempt {_ + 1}")
            llm_response = await self.llm.generate(
                messages=conversation_history,
                # stop=['</execute']
            )
            action_type, action_content = self._parse_llm_response(llm_response)
            self.logger.info("######################")
            self.logger.info(f"action_type: {action_type}")
            self.logger.info(f"action_content: {action_content}")

            if action_type != "code":
                conversation_history.append({"role": "assistant", "content": llm_response})
                conversation_history.append({"role": "user", "content": "Your reply did not include a valid <execute> code block. Please provide Python code that draws the chart."})
                continue  # retry

            code_result = await self.code_executor.execute(code=action_content)
            self.logger.info(f"code_result: {code_result}")
            if code_result['error']:
                conversation_history.append({"role": "assistant", "content": llm_response})
                error_feedback = (
                    "Your code failed to execute. Here is the error output:\n\n"
                    f"{code_result['stdout']}\n{code_result['stderr']}\n\nPlease fix the code and try again."
                )
                self.logger.info(error_feedback)
                conversation_history.append({"role": "user", "content": error_feedback})
                continue  # retry
            
            # Ensure the code saved a figure
            chart_filenames = re.findall(r"[\"']([^\"']+\.png)[\"']", action_content)
            if not chart_filenames:
                conversation_history.append({"role": "assistant", "content": llm_response}) 
                feedback = "Your code ran but did not save a PNG. Please add `plt.savefig('filename.png')`."
                self.logger.info(feedback)
                conversation_history.append({"role": "user", "content": feedback})
                continue  # retry

            # Confirm the file exists
            potential_chart_name = os.path.basename(chart_filenames[0])
            chart_filepath = os.path.join(self.image_save_dir, potential_chart_name) 

            if not os.path.exists(chart_filepath):
                conversation_history.append({"role": "assistant", "content": llm_response})
                feedback = f"The file '{potential_chart_name}' was not found in the output directory. Please ensure the `plt.savefig()` path is correct."
                self.logger.info(feedback)
                conversation_history.append({"role": "user", "content": feedback})
                continue  # retry
            
            return llm_response, chart_filepath

        # Bail out after three failed attempts
        return None, None
    
    def _get_persist_extra_state(self) -> Dict[str, Any]:
        return {'current_phase': self.current_phase}
    def _load_persist_extra_state(self, state: Dict[str, Any]):
        self.current_phase = state.get('current_phase', 'phase1')
        
    async def async_run(
        self, 
        input_data: dict, 
        max_iterations: int = 10,
        stop_words: list[str] = [],
        echo=False,
        resume: bool = True,
        checkpoint_name: str = 'latest.pkl',
        enable_chart: bool = True,
        # stop_words: list[str] = ["</execute>", "</report>"]
    ) -> dict:
        input_data['enable_chart'] = enable_chart
        self.enable_chart = enable_chart
        # Phase 1: conversational analysis (handled by BaseAgent)
        if self.current_phase == 'phase1':
            run_result = await super().async_run(
                input_data=input_data,
                max_iterations=max_iterations,
                stop_words=stop_words,
                echo=echo,
                resume=resume,
                checkpoint_name=checkpoint_name,
            )
            self.current_phase = 'phase2'
            await self.save(state={'finished': False, 'current_phase': self.current_phase, 'phase1_result': run_result}, checkpoint_name=checkpoint_name)
        else:
            run_result = self.current_checkpoint.get('phase1_result', {})
        final_result = run_result['final_result']
        
        # Parse the generated analysis report
        if self.current_phase == 'phase2':
            report_title, report_content = self._parse_generated_report(final_result)
            self.logger.info(f"report_title: {report_title}")
            self.current_phase = 'phase3'
            await self.save(state={'report_title': report_title, 'report_content': report_content, 'current_phase': self.current_phase}, checkpoint_name=checkpoint_name)
        else:
            report_title = self.current_checkpoint.get('report_title', '')
            report_content = self.current_checkpoint.get('report_content', '')
        run_result['report_title'] = report_title
        run_result['report_content'] = report_content


        # Phase 2: draw charts (separate checkpoint charts.pkl)
        if self.current_phase == 'phase3' and enable_chart:
            chart_code_mapping, name_mapping, name_description_mapping = await self._draw_chart(input_data, run_result)
            # Clean up/checkpoint bookkeeping once finished
            self.current_phase = 'phase4'
            await self.save(state={
                'current_phase': self.current_phase, 
                'chart_code_mapping': chart_code_mapping, 
                'chart_name_mapping': name_mapping, 
                'chart_name_description_mapping': name_description_mapping
            }, checkpoint_name=checkpoint_name)
        else:
            self.current_phase = 'phase4'
            chart_code_mapping = self.current_checkpoint.get('chart_code_mapping', {})
            name_mapping = self.current_checkpoint.get('chart_name_mapping', {})
            name_description_mapping = self.current_checkpoint.get('chart_name_description_mapping', {})

        run_result['chart_code_mapping'] = chart_code_mapping
        run_result['chart_name_mapping'] = name_mapping
        run_result['chart_name_description_mapping'] = name_description_mapping
        
        if self.current_phase == 'phase4':
            analysis_result = AnalysisResult(
                title=report_title,
                content=report_content,
                image_save_dir=self.image_save_dir,
                chart_code_mapping=chart_code_mapping,
                chart_name_mapping=name_mapping,
                chart_name_description_mapping=name_description_mapping
            )
            self.memory.add_data(analysis_result)
            self.memory.add_log(
                id=self.id,
                type=self.type,
                input_data=input_data,
                output_data=analysis_result,
                error=False,
                note=f"Analysis result generated successfully"
            )
            self.current_phase = 'done'
            await self.save(state={'current_phase': self.current_phase, 'analysis_result': analysis_result, 'finished': True}, checkpoint_name=checkpoint_name)
        self.memory.save()
        return run_result


class AnalysisResult:
    def __init__(
        self, 
        title: str, 
        content: str, 
        image_save_dir: str,
        chart_code_mapping: dict = None, 
        chart_name_mapping: dict = None, 
        chart_name_description_mapping: dict = None
    ):
        self.title = title
        self.content = content
        self.image_save_dir = image_save_dir
        self.chart_code_mapping = chart_code_mapping
        self.chart_name_mapping = chart_name_mapping
        self.chart_name_description_mapping = chart_name_description_mapping
    
    def __str__(self):
        # Replace placeholders with descriptive captions
        content = self._repalce_image_name()[1]
        return f"Report Title: {self.title}\nReport Content: {content}\n\n"

    def brief_str(self):
        # Replace placeholders with descriptive captions
        content = self._repalce_image_name()[1]
        return f"Report Title: {self.title}\nReport Content: {content[:300]}...(more content available)\n\n"
    
    def _repalce_image_name(self):
        image_name_list = []
        report_content = self.content
        img_list = re.findall("@import \"(.*?)\"", self.content)
        # Note: AnalysisResult is not an agent and has no logger; use prints or another mechanism if logging is needed.

        for img in img_list:
            if img in self.chart_name_description_mapping:
                new_img = self.chart_name_mapping[img]
                report_content = report_content.replace(
                    f"@import \"{img}\"",
                    f"@import \"{new_img}\"" + '\n(Description: ' + self.chart_name_description_mapping[img][:100] + ')'
                )
                image_name_list.append(new_img)
        return image_name_list, report_content
    
    def get_all_img(self):
        return self._repalce_image_name()[0]