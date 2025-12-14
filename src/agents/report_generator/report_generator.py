from typing import List, Dict, Any, Tuple
import asyncio
import os
import re
import copy
import subprocess
import numpy as np
import docx2pdf
from src.agents.base_agent import BaseAgent
from src.agents import DeepSearchAgent
from src.tools import ToolResult, get_tool_categories, get_tool_by_name
from src.agents.report_generator.report_class import Report, Section
from src.utils.helper import extract_markdown, get_md_img
from src.utils.index_builder import IndexBuilder
from src.utils.figure_helper import draw_kline_chart
class ReportGenerator(BaseAgent):
    AGENT_NAME = 'report_generator'
    AGENT_DESCRIPTION = 'a agent that can generate report from the data'
    NECESSARY_KEYS = ['task']
    def __init__(
        self,
        config,
        tools = [],
        use_llm_name: str = "deepseek-chat",
        use_embedding_name: str = "qwen3-embedding",
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
        # Load prompts based on language and target type settings
        from src.utils.prompt_loader import get_prompt_loader
        
        target_language = self.config.config.get('language', 'zh')
        language_mapping = {
            'zh': 'Chinese (中文)',
            'en': 'English'
        }
        target_language_name = language_mapping.get(target_language, target_language)
        self.target_language_name = target_language_name
        target_type = self.config.config.get('target_type', 'general')
        
        
        # Load prompts using the new YAML-based loader
        self.prompt_loader = get_prompt_loader('report_generator', report_type=target_type)
        
        # Store prompts as instance attributes for easy access
        self.SECTION_WRITING_PROMPT = self.prompt_loader.get_prompt('section_writing')
        self.SECTION_WRITING_WO_CHART_PROMPT = self.prompt_loader.get_prompt('section_writing_wo_chart')
        self.FINAL_POLISH_PROMPT = self.prompt_loader.get_prompt('final_polish')
        
        # For general reports, use outline_draft; for financial, use outline_draft as well
        # (both YAML files have 'outline_draft' key)
        self.DRAFT_GENERATOR_PROMPT = self.prompt_loader.get_prompt('outline_draft')
        
        self.CRITIQUE_PROMPT = self.prompt_loader.get_prompt('outline_critique')
        self.REFINEMENT_PROMPT = self.prompt_loader.get_prompt('outline_refinement')
        
        # used for adding abstract and title
        self.TITLE_PROMPT = self.prompt_loader.get_prompt('title_generation')
        self.ABSTRACT_PROMPT = self.prompt_loader.get_prompt('abstract')

        # used for cover page
        self.TABLE_BEAUTIFY_PROMPT = self.prompt_loader.get_prompt('table_beautify')
        
        self.use_embedding_name = use_embedding_name
        # Phase checkpoints: outline → sections → post_process
        self._phase: str = 'outline'
        # Section-level progress counter
        self._section_index_done: int = 0
        # Post-process sub-stages: 0-image, 1-abstract/title, 2-cover, 3-reference, 4-render
        self._post_stage: int = 0
        

    def _set_default_tools(self):
        """
        Attach the default tools/agents required by the report generator.
        """
        tool_list = []
        # Attach the deep-search agent (sharing the same memory)
        tool_list.append(DeepSearchAgent(config=self.config, use_llm_name=self.use_llm_name, memory=self.memory))
        for tool in tool_list:
            self.memory.add_dependency(tool.id, self.id)
        self.tools = tool_list
    
    async def _prepare_executor(self):
        """
        Prepare the code executor with data access functions for section writing.
        """
        current_task_data = self.current_task_data
        tool_list = self.tools
        collect_data_list = self.memory.get_collect_data(exclude_type='search')
        analysis_result_list = self.memory.get_analysis_result()
        
        def _get_data(data_id: int):
            """Get dataset by index"""
            if 0 <= data_id < len(collect_data_list):
                return collect_data_list[data_id].data
            else:
                raise ValueError(f"Invalid data_id: {data_id}. Available range: 0-{len(collect_data_list)-1}")
        
        def _get_analysis_result(data_id: int):
            """Get analysis results matching the query"""
            # Use LLM-based selection to find relevant analysis results
            if 0 <= data_id < len(analysis_result_list):
                return str(analysis_result_list[data_id])[:3000]
            else:
                raise ValueError(f"Invalid data_id: {data_id}. Available range: 0-{len(analysis_result_list)-1}")
        
        def _get_deepsearch_result(query: str):
            """Call deep search agent"""
            ds_agent = tool_list[0]
            output = asyncio.run(ds_agent.async_run(input_data={
                'task': current_task_data.get('task', ''),
                'query': query
            }))
            return output['final_result']
        
        self.code_executor.set_variable("get_data", _get_data)
        self.code_executor.set_variable("get_analysis_result", _get_analysis_result)
        self.code_executor.set_variable("get_data_from_deep_search", _get_deepsearch_result)
        
    
    async def _prepare_init_prompt(self, input_data: dict) -> list[dict]:
        task = input_data.get('task')
        section_outline = input_data.get('section_outline')
        max_iterations = input_data.get('max_iterations', 10)
        if not task:
            raise ValueError("Input data must contain a 'task' key.")
        
        # Get data API description from prompts
        data_api_description = self.prompt_loader.get_prompt('data_api')
        
        # Prepare data information for the agent
        collect_data_list = self.memory.get_collect_data(exclude_type='search')
        analysis_result_list = self.memory.get_analysis_result()
        data_info = "\n\n## Available Datasets\n\n"
        for idx, item in enumerate(collect_data_list):
            data_info += f"**Data ID {idx}:**\n{item.brief_str()}\n\n"
        data_info += "\nYou can access these datasets using `get_data(data_id)` in your code.\n"
        data_info += "\n\n## Available Analysis Reports\n\n"
        for idx, item in enumerate(analysis_result_list):
            data_info += f"**Analysis Report ID {idx}:**\n{item.brief_str()}\n\n"
        data_info += "\nYou can access these analysis reports using `get_analysis_result(analysis_result_id)` in your code.\n"
        
        if self.enable_chart:
            return [{
                "role": "user",
                "content": self.SECTION_WRITING_PROMPT.format(
                    task=task,
                    report_theme=input_data.get('task'),
                    section_description=section_outline,
                    data_api=data_api_description,
                    data_info=data_info,
                    max_iterations=max_iterations,
                    target_language=self.target_language_name
                )
            }]
        else:
            return [{
                "role": "user",
                "content": self.SECTION_WRITING_WO_CHART_PROMPT.format(
                    task=task,
                    report_theme=input_data.get('task'),
                    section_description=section_outline,
                    data_api=data_api_description,
                    data_info=data_info,
                    max_iterations=max_iterations,
                    target_language=self.target_language_name
                )
            }]

    async def _handle_search_action(self, action_content: str):
        search_result = await self.tools[0].async_run(input_data={'query': action_content})
        return {
            'action': 'search',
            'action_content': action_content,
            'result': search_result['final_result'],
            'continue': True,
        }
    
    async def _handle_report_action(self, action_content: str):
        """Handle a 'final/report' action."""
        return {
            "action": "report",
            "action_content": action_content,
            "result": action_content,
            "continue": False,
        }
    async def _handle_outline_action(self, action_content: str):
        """Handle a 'outline' action."""
        return {
            "action": "outline",
            "action_content": action_content,
            "result": action_content,
            "continue": False,
        }
    
    async def _handle_draft_action(self, action_content: str):
        """Handle a 'outline' action."""
        return {
            "action": "draft",
            "action_content": action_content,
            "result": action_content,
            "continue": False,
        }
    
    async def _final_polish(self, section_input_data, draft_section: str):
        all_analysis_result = self.memory.get_analysis_result()
        all_image_list = []
        for analysis_result in all_analysis_result:
            all_image_list.extend(analysis_result.get_all_img())
        reference_image = '\n'.join(all_image_list)
        
        final_prompt = self.FINAL_POLISH_PROMPT.format(
            draft_report = draft_section,
            reference_image = reference_image,
            target_language = self.target_language_name
        )
        
        final_message = [{"role": "user", "content": final_prompt}]
        output = await self.llm.generate(messages = final_message)
        final_section = extract_markdown(output)
        return final_section
    
    async def _replace_image_path(self, report):
        """
        Replace placeholder image references in the report with actual local paths.
        """
        # If charts are disabled, simply remove @import placeholders
        if not self.enable_chart:
            for section in report.sections:
                section_new_content = []
                for p_paragraph in section._content:
                    # Replace @import.* with empty string
                    p_paragraph = re.sub(r'@import.*', '', p_paragraph, flags=re.DOTALL)
                    section_new_content.append(p_paragraph)
                section._content = section_new_content
            return report
        
        def remove_suffix(name: str):
            return name.replace(".png", "").replace(".jpg", "").replace(".jpeg", "").replace(".md", "")
        def is_image_file(name: str):
            return name.endswith(".png") or name.endswith(".jpg") or name.endswith(".jpeg") or name.endswith(".md")
        all_analysis_result = self.memory.get_analysis_result()
        img_captions = []
        img_paths = []
        for analysis_result in all_analysis_result:
            short2long = {}
            img_dicts = {} # caption: abs_path 
            chart_name_mapping = analysis_result.chart_name_mapping
            for long_name, short_name in chart_name_mapping.items():
                short2long[remove_suffix(short_name)] = remove_suffix(long_name)
            image_save_dir = analysis_result.image_save_dir
            for image_name in os.listdir(image_save_dir):
                if is_image_file(image_name):
                    img_path = os.path.join(image_save_dir, image_name)
                    img_name = remove_suffix(image_name)
                    long_image_name = short2long.get(img_name, "")
                    if long_image_name != "":
                        img_dicts[long_image_name] = img_path
            img_captions.extend(list(img_dicts.keys()))
            img_paths.extend(list(img_dicts.values()))
        if len(img_captions) == 0:
            self.logger.warning("No image captions found, skip image path replacement")
            return report
        self.logger.info(f"Building index for {len(img_captions)} images")
        index = IndexBuilder(config=self.config, embedding_model=self.use_embedding_name, working_dir=self.working_dir)
        await index._build_index(img_captions)

        used_img_list = []
        figure_idx = 1
        for section in report.sections:
            section_new_content = []
            for p_paragraph in section._content:
                match = re.findall(r'@import.*', p_paragraph,flags=re.DOTALL)
                try:
                    self.logger.debug(f"Section image placeholders: {len(match)}")
                except Exception:
                    pass
                if match and len(match) > 0:
                    for img_name in match:
                        # img_name is the short placeholder string
                        most_similar_idx = (await index.search(img_name))[0]['id']
                        detect_img_name = img_captions[most_similar_idx]
                        detect_img_path = img_paths[most_similar_idx]
                        
                        if len(img_captions) == 1:
                            # No images left to map
                            self.logger.warning("Available images are exhausted; stop replacing images.")
                            # directly delete the image placeholder
                            p_paragraph = p_paragraph.replace(img_name, "")
                            continue
                        del img_captions[most_similar_idx]
                        del img_paths[most_similar_idx]
                        # Rebuild the index after consuming this caption
                        await index._build_index(img_captions)

                        new_string = get_md_img(detect_img_path, remove_suffix(os.path.basename(detect_img_path)), figure_idx)
                        figure_idx += 1
                        used_img_list.append(detect_img_name)
                        p_paragraph = p_paragraph.replace(img_name, new_string)

                section_new_content.append(p_paragraph)
            section._content = section_new_content
        return report

    
    async def _add_abstract(self, input_data, report):
        """
        Add an abstract and update the title.
        """
        abstract_prompt = self.ABSTRACT_PROMPT
        title_prompt = self.TITLE_PROMPT


        response_content = await self.llm.generate(
            messages = [
            {
                'role': 'user',
                'content': abstract_prompt.format(target_language=self.target_language_name, report_content=report.content)
            }
        ])
        response_content = extract_markdown(response_content)
        report.abstract = response_content
        
        new_title = await self.llm.generate(
            messages = [
            {
                'role': 'user',
                'content': title_prompt.format(target_language=self.target_language_name, report_content=report.content)
            }
        ])
        new_title = new_title.replace("#","").strip()
        report._content = f"# {new_title}\n\n"

        return report

    async def _add_cover_page(self, input_data, report):
        pipeline_type = input_data.get('target_type', 'company')
        if pipeline_type != 'company':
            return report
        stock_code = input_data.get('stock_code', '')
        if stock_code == "":
            return report

        output_str = "\n\n## Company Fundamentals\n\n"
        # Three statements + shareholder profile
        collect_data_list = self.memory.get_collect_data()
        table_configs = [
            ("Income statement", "Income Statement"),
            ("Balance sheet", "Balance Sheet"),
            ("Cash-flow statement", "Cash-Flow Statement"),
            ("Shareholding structure", "Shareholder Structure"),
        ]
        for keyword, display_name in table_configs:
            target_item_list = [item for item in collect_data_list if keyword in item.name and stock_code in item.name]
            if len(target_item_list) == 0:
                print(f"No {display_name} data found")
                continue
            else:
                table_data = target_item_list[0].data
                if table_data is None:
                    print(f"{display_name} data is empty, skip formatting")
                    continue
                    
                if keyword in ["Income statement", "Balance sheet", "Cash-flow statement"]:
                    if 'Category' in table_data.columns:
                        table_data.rename(columns={'Category': 'Line item (RMB mn)'}, inplace=True)
                prompt = self.TABLE_BEAUTIFY_PROMPT.format(table_name=display_name, table_data=table_data.to_markdown(index=False))
                response = await self.llm.generate(
                    messages = [
                        {"role": "user", "content": prompt}
                    ]
                )
                table_string = "\n".join([line for line in response.split("\n") if line.strip() != ""])

                output_str += f'\n\n### {display_name}\n\n'
                output_str += table_string
                
                output_str += '\n\n'
        
        # Render stock-price chart
        try:
            self.logger.info("Rendering stock-price chart for cover page")
            target_item_list = [item for item in collect_data_list if 'candlestick' in item.name.lower() and stock_code in item.name]
            if len(target_item_list) != 0:
                kline_data = target_item_list[0].data
                if kline_data is None:
                    self.logger.warning("Candlestick data is empty; skip price visualization")
                else:
                    if isinstance(kline_data, list) and len(kline_data) == 1:
                        kline_data = kline_data[0]
                    if 'date' not in kline_data.columns:
                        if '\u65e5\u671f' in kline_data.columns:
                            kline_data.rename(columns={'\u65e5\u671f': 'date'}, inplace=True)
                        if '\u6536\u76d8' in kline_data.columns:
                            kline_data.rename(columns={'\u6536\u76d8': 'close'}, inplace=True)
                    fig_path = draw_kline_chart(kline_data, self.working_dir)
                    output_str += f'\n\n### Share Price Trend\n\n'
                    output_str += f'![Trailing price performance]({fig_path})\n\n'
        except Exception as e:
            self.logger.error(f"Failed to draw price trend: {e}", exc_info=True)
            pass

        first_section = Section('Company Fundamentals', output_str)
        first_section.set_content(output_str)
        report.sections = [first_section] + report.sections

        return report
    

    async def _add_reference(self, report):
        """
        Append the reference-data section and replace placeholder citations.
        """
        collect_data_list = self.memory.get_collect_data() # only use data, without analysis result
        all_data = []
        for item in collect_data_list:
            # TODO: directly set these keys in ToolResult
            name = item.name + '\n' + item.description # used for index
            content = item.source # used for display citation
            # content = item.name + '\n' + item.link  # used for display citation
            if content not in [ii['content'] for ii in all_data]:
                all_data.append({
                    'name': name,
                    'content': content 
                })
        self.logger.info(f"Total data for reference: {len(all_data)}")
        
        total_corpus = [item['name'] for item in all_data]
        index = IndexBuilder(config=self.config, embedding_model=self.use_embedding_name, working_dir=self.working_dir)
        await index._build_index(total_corpus)

        total_cited_dict = {}
        for section in report.sections:
            # Optional: log section length
            try:
                self.logger.debug(f"Processing section, content length={len(section.content)}")
            except Exception:
                pass
            section_new_content = []
            for p_paragraph in section._content:
                content = p_paragraph
                print(content)
                # Locate citation placeholders
                match_list = re.findall(r'\[[Ss]ource[：:]\s*(.*?)\]',content)
                self.logger.debug(f"Match list: {match_list}")
                for match_item in match_list:
                    # Use BM25/embedding search
                    search_result = await index.search(match_item, top_k=5)
                    score_list = [item['score'] for item in search_result]
                    id_list = [item['id'] for item in search_result]  # Get actual data indices
                    self.logger.debug(f"Score list: {score_list}")
                    self.logger.debug(f"ID list: {id_list}")
                    print(search_result)
                    # Sort by score (descending) and get corresponding indices
                    sorted_idx = np.argsort(score_list)[::-1]
                    score_list = np.array(score_list)
                    score_list = np.exp(score_list) / np.sum(np.exp(score_list))

                    cite_list = []
                    for pos in sorted_idx:
                        pos = int(pos)
                        actual_idx = id_list[pos]  # Get the actual data index
                        if score_list[pos] > 0.2 and len(cite_list) < 5:
                            cite_list.append(actual_idx)
                    if len(cite_list) == 0:
                        # If no item meets threshold, use the top result
                        cite_list.append(id_list[sorted_idx[0]])
                    new_cite_list = []
                    for idx in cite_list:
                        if idx not in total_cited_dict:
                            total_cited_dict[idx] = len(total_cited_dict) + 1
                    new_cite_list = [total_cited_dict[idx] for idx in cite_list]
                    # Build the regex for replacement
                    pattern_to_replace = r'\[[Ss]ource[：:]\s*' + re.escape(match_item) + r'\]'
                    content = re.sub(pattern_to_replace, f'[{",".join([str(item) for item in new_cite_list])}]', content)

                section_new_content.append(content)
            section._content = section_new_content


        reference_str = "## Reference Data Sources\n\n"
        for old_index, new_index in total_cited_dict.items():
            content = all_data[old_index]['content']
            content = content.replace("\n", " ").replace("[PDF]", "")
            reference_str += f"{new_index}. {content}\n"
        new_section = Section('Reference Data Sources', reference_str)
        new_section.set_content(reference_str)
        report.sections.append(new_section)
        return report

        

    async def post_process_report(self, input_data, report):
        """
        Post-process the report while saving progress between sub-stages:
          0: replace image paths
          1: add abstract and title
          2: add cover/basic data page
          3: add reference data section
          4: render to docx
        """
        current_state = {
            'phase': 'post_process',
            'post_stage': self._post_stage,
            'report_obj': report,
        }
        # 0 Replace image paths
        if self._post_stage <= 0:
            self.logger.info("[Phase2] Step 0: replace image paths")
            report = await self._replace_image_path(report)
            self._post_stage = 1
            current_state['report_obj_stage1'] = copy.deepcopy(report)
            current_state['report_obj'] = report
            current_state['post_stage'] = self._post_stage
            await self.save(state=current_state, checkpoint_name='report_latest.pkl')
            self.logger.info("[Phase2] Step 0 done, checkpoint saved")

        # 1 Add abstract/title (conditional based on add_introduction setting)
        if self._post_stage <= 1:
            if getattr(self, 'add_introduction', True):
                self.logger.info("[Phase2] Step 1: add abstract and title")
                report = await self._add_abstract(input_data, report)
            else:
                self.logger.info("[Phase2] Step 1: skipping abstract/introduction (add_introduction=False for general reports)")
                # Still generate a better title
                new_title = await self.llm.generate(
                    messages = [
                    {
                        'role': 'user',
                        'content': self.TITLE_PROMPT.format(target_language=self.target_language_name, report_content=report.content)
                    }
                ])
                new_title = new_title.replace("#","").strip()
                report._content = f"# {new_title}\n\n"
            self._post_stage = 2
            current_state['report_obj_stage2'] = copy.deepcopy(report)
            current_state['report_obj'] = report
            current_state['post_stage'] = self._post_stage
            await self.save(state=current_state, checkpoint_name='report_latest.pkl')
            self.logger.info("[Phase2] Step 1 done, checkpoint saved")

        # 2 Add cover/basic data page
        if self._post_stage <= 2:
            self.logger.info("[Phase2] Step 2: add cover/basic data page")
            report = await self._add_cover_page(input_data, report)
            self._post_stage = 3
            current_state['report_obj_stage3'] = copy.deepcopy(report)
            current_state['report_obj'] = report
            current_state['post_stage'] = self._post_stage
            await self.save(state=current_state, checkpoint_name='report_latest.pkl')
            self.logger.info("[Phase2] Step 2 done, checkpoint saved")

        # 3 Add references (conditional based on add_reference_section setting)
        if self._post_stage <= 3:
            if getattr(self, 'add_reference_section', True):
                self.logger.info("[Phase2] Step 3: add references")
                report = await self._add_reference(report)
            else:
                self.logger.info("[Phase2] Step 3: skipping reference section (add_reference_section=False)")
            self._post_stage = 4
            current_state['report_obj_stage4'] = copy.deepcopy(report)
            current_state['report_obj'] = report
            current_state['post_stage'] = self._post_stage
            await self.save(state=current_state, checkpoint_name='report_latest.pkl')
            self.logger.info("[Phase2] Step 3 done, checkpoint saved")

        # 4 Render to docx
        if self._post_stage <= 4:
            self.logger.info("[Phase2] Step 4: render report to docx")
            working_dir = self.config.config['working_dir']
            md_path = os.path.join(working_dir, f'{report.title}.md')
            docx_path = os.path.join(working_dir, f'{report.title}.docx')
            content = report.content
            content = content.replace("```markdown", "").replace("```", "")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(content)
            media_dir = os.path.join(working_dir, "media")
            reference_doc = self.config.config['reference_doc_path']
            pandoc_cmd = [
                "pandoc",
                md_path,
                "-o",
                docx_path,
                "--standalone",
                "--toc",
                "--toc-depth=3",
                f"--resource-path={working_dir}",
                f"--reference-doc={reference_doc}"
            ]
            if os.path.exists(media_dir):
                pandoc_cmd.append(f"--extract-media={media_dir}")
            print(" ".join(pandoc_cmd))
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            subprocess.run(pandoc_cmd, check=True, capture_output=True, text=True, encoding='utf-8', env=env)
            
            pdf_path = docx_path.replace(".docx", ".pdf")
            try:
                docx2pdf.convert(docx_path, pdf_path)
            except Exception as e:
                self.logger.error(f"Failed to convert docx to pdf: {e}", exc_info=True)
            self._post_stage = 5
            current_state['rendered_md'] = md_path
            current_state['rendered_docx'] = docx_path
            current_state['finished'] = True
            await self.save(state=current_state, checkpoint_name='report_latest.pkl')
            self.logger.info(f"[Phase2] Step 4 done, rendered files: md={md_path}, docx={docx_path}, pdf={pdf_path}")
        return report

    def _get_persist_extra_state(self) -> Dict[str, Any]:
        """
        Provide extra state so parent persistence can restore the pipeline stages.
        """
        return {
            'phase': getattr(self, '_phase', 'outline'),
            'section_index': getattr(self, '_section_index_done', 0),
            'post_stage': getattr(self, '_post_stage', 0),
        }

    def _load_persist_extra_state(self, state: Dict[str, Any]):
        """
        Restore stage metadata from a checkpoint.
        """
        # Recover from the extra field populated by _get_persist_extra_state
        extra = state.get('extra', {})
        
        phase = extra.get('phase') or state.get('phase')
        if isinstance(phase, str):
            self._phase = phase
        
        section_index = extra.get('section_index') or state.get('section_index')
        if section_index is not None:
            try:
                self._section_index_done = int(section_index)
            except Exception:
                pass
        
        post_stage = extra.get('post_stage') or state.get('post_stage')
        if post_stage is not None:
            try:
                self._post_stage = int(post_stage)
            except Exception:
                pass
        
        enable_chart = extra.get('enable_chart') or state.get('enable_chart')
        if enable_chart is not None:
            try:
                self.enable_chart = bool(enable_chart)
            except Exception:
                pass
        else:
            self.enable_chart = True
    
    async def _prepare_outline_prompt(self, input_data):
        max_iterations = input_data.get('max_iterations', 10)
        outline_template_path = self.config.config.get('outline_template_path', None)
        
        if outline_template_path is None or not os.path.exists(outline_template_path):
            outline_template = ""
        else:
            with open(outline_template_path, 'r', encoding='utf-8') as f:
                outline_template = f.read()
        # Prepare data API description and available analysis info
        data_api_description = self.prompt_loader.get_prompt('data_api_outline')
        analysis_result_list = self.memory.get_analysis_result()
        
        data_info = "You have access to the following analysis results:\n\n"
        for idx, result in enumerate(analysis_result_list):
            data_info += f"**Analysis Report ID {idx}:**\n{result.brief_str()}\n\n"
        data_info += "\nYou can retrieve detailed content using `get_analysis_result(analysis_id)` in your code.\n"
        
        initial_prompt = self.DRAFT_GENERATOR_PROMPT.format(
            task=input_data['task'],
            report_requirements=outline_template,
            data_api=data_api_description,
            data_info=data_info,
            max_iterations=max_iterations,
            target_language=self.target_language_name
        )
        return [{"role": "user", "content": initial_prompt}]

    async def generate_outline(
        self, 
        input_data, 
        max_iterations: int = 10,
        stop_words: list[str] = [],
        echo=False,
        resume: bool = True,
        checkpoint_name: str = 'outline_latest.pkl'
    ):
        """
        Generate the report outline via agentic workflow.

        Args:
            input_data: Dict containing task metadata.
            max_iterations: Maximum number of interaction rounds.

        Returns:
            Report object populated with outline sections.
        """
       
        # Prepare executor for outline generation
        await self._prepare_executor()

        self.logger.info(f"[Outline] Starting agentic outline generation (max {max_iterations} rounds)")
        
        # Create input data for outline generation
        outline_input_data = {
            'task': input_data['task'],
            'max_iterations': max_iterations
        }
        self.current_task_data = outline_input_data

        outline_result = await super().async_run(
            input_data=outline_input_data,
            max_iterations=max_iterations,
            stop_words=stop_words,
            echo=echo,
            resume=resume,
            checkpoint_name=checkpoint_name,
            prompt_function=self._prepare_outline_prompt,
        )
    
        outline_content = extract_markdown(outline_result['final_result'])
        
        return Report(outline_content) if outline_content else Report("# Error: Could not generate outline")



    async def async_run(
        self, 
        input_data: dict, 
        max_iterations: int = 10,
        stop_words: list[str] = [],
        # stop_words: list[str] = ["</draft>", "</outline>", "</report>", "</execute>"],
        echo=False,
        resume: bool = True,
        checkpoint_name: str = 'report_latest.pkl',
        enable_chart = True,
        add_introduction: bool = None,  # None means auto-detect based on target_type
        add_reference_section: bool = True
    ) -> dict:
        """
        Three-stage execution flow for the report generator:
        Phase 0: outline creation
        Phase 1: per-section drafting
        Phase 2: post processing
        """
        # Initialize/restore stage state
        report = None
        start_index = 0
        self.enable_chart = enable_chart
        input_data['max_iterations'] = max_iterations
        
        # Configure post-processing options based on target_type
        target_type = self.config.config.get('target_type', 'general')
        
        # For general/deep-research reports, default to NO introduction (user specifies their own structure)
        # For company/financial reports, default to YES (standard report format)
        if add_introduction is None:
            self.add_introduction = target_type not in ['general']
        else:
            self.add_introduction = add_introduction
        
        self.add_reference_section = add_reference_section
        
        if resume:
            state = await self.load(checkpoint_name=checkpoint_name)
            if state is not None:
                # Restore extra metadata
                self._load_persist_extra_state(state)
                self.logger.info(f"[Resume] phase={getattr(self, '_phase', None)}, section_index={getattr(self, '_section_index_done', None)}, post_stage={getattr(self, '_post_stage', None)}")
                
                # If the workflow already finished, return the saved report
                if state.get('finished'):
                    restored_report = state.get('report_obj')
                    if restored_report:
                        self.logger.info("Report already completed, restoring from checkpoint")
                        return restored_report
                
                # Restore an in-progress report if available
                restored_report = state.get('report_obj')
                if restored_report is not None:
                    report = restored_report
                    start_index = self._section_index_done
                    self.logger.info(f"[Resume] Restored report object, will resume from section_index={start_index}")
        
        # Phase 0: outline generation
        if self._phase == 'outline' or report is None:
            self.logger.info("[Phase0] Generating Report Outline")
            report = await self.generate_outline(
                input_data, 
                max_iterations=max_iterations,
                stop_words=stop_words,
                echo=echo,
                resume=resume,
                checkpoint_name='outline_latest.pkl'
            )
            self._phase = 'sections'
            # Persist outline state
            await self.save(
                state={
                    'phase': self._phase,
                    'report_obj': report,
                    'input_data': input_data,
                    'enable_chart': self.enable_chart,
                },
                checkpoint_name=checkpoint_name,
            )
            self.memory.save()
            self.logger.info(f"[Phase0] Completed: outline sections={len(report.sections)}")

        
        # Phase 1: per-section generation
        if self._phase == 'sections':
            self.logger.info("[Phase1] Begin generating sections")
            # TODO: parallel generation of sections
            for idx, section in enumerate(report.sections):
                if idx < start_index:
                    continue
                section_input_data = input_data.copy()
                section_input_data['section_outline'] = section.outline
                self.logger.info(f"[Phase1] Section {idx+1}/{len(report.sections)} start")
                
                # Prepare executor with data access functions for agentic workflow
                await self._prepare_executor()
                
                # Each section run has its own checkpoint for resume support
                section_result = await super().async_run(
                    input_data=section_input_data,
                    max_iterations=max_iterations,
                    stop_words=stop_words,
                    echo=echo,
                    resume=resume and idx == start_index,
                    checkpoint_name=f'section_{idx}.pkl'
                )
                draft_section = section_result['final_result']
                self.logger.debug(f"[Phase1] Draft section length={len(draft_section)}")
                
                # Final polish for the section content
                final_section = await self._final_polish(section_input_data, draft_section)
                self.logger.debug(f"[Phase1] Final section length={len(final_section)}")
                self.memory.add_log(
                    id=self.id,
                    type=self.type,
                    input_data=section_input_data,
                    output_data=section_result,
                    error=False,
                    note=f"Report generator executed successfully"
                )
                section.set_content(final_section) 
                # Save global progress after each section to resume later
                await self.save(
                    state={
                        'phase': 'sections',
                        'section_index': idx + 1,
                        'report_obj': report,
                        'input_data': input_data,
                    },
                    checkpoint_name=checkpoint_name,
                )
                self.memory.save()
                # Update in-memory progress pointer
                self._section_index_done = idx + 1
                self.logger.info(f"[Phase1] Section {idx+1} done, checkpoint saved (section_index={self._section_index_done})")
            
            # Move to post-process stage once all sections are done
            self._phase = 'post_process'
            await self.save(
                state={
                    'phase': self._phase,
                    'section_index': self._section_index_done,
                    'post_stage': self._post_stage,
                    'report_obj': report,
                    'input_data': input_data,
                },
                checkpoint_name=checkpoint_name,
            )
            self.memory.save()
            self.logger.info("[Phase1] Completed: All sections generated")

        # Phase 2: post processing (resumable)
        if self._phase == 'post_process':
            self.logger.info("[Phase2] Begin post processing")
            report = await self.post_process_report(input_data, report)
            self.memory.save()
            self.logger.info("[Phase2] Completed post processing")

        return report
    
