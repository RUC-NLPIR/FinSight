from typing import List, Dict, Any, Tuple

from src.agents.base_agent import BaseAgent
from src.tools.web.search_engine_requests import BingSearch, BochaSearch, SerperSearch
from src.tools.web.web_crawler import Click
from src.tools.base import ToolResult

class DeepSearchAgent(BaseAgent):
    AGENT_NAME = 'deepsearch agent'
    AGENT_DESCRIPTION = (
        "Tool: Deep Search\n"
        "Description: run comprehensive web searches (news, filings, research, etc.) "
        "to gather evidence for a given task.\n"
        "Parameters: query:str (describe exactly what information is needed; "
        "avoid loose keyword lists).\n"
    )
    NECESSARY_KEYS = ['task', 'query']
    def __init__(
        self,
        config,
        tools = None,
        use_llm_name: str = "deepseek-chat",
        enable_code = False,
        memory = None,
        agent_id: str = None
    ):
        # Use search + click tools directly; no code interpreter required
        if tools is None:
            tools = [SerperSearch(), Click()]
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
        
        self.prompt_loader = get_prompt_loader('search_agent', report_type='general')
        self.DEEP_SEARCH_PROMPT = self.prompt_loader.get_prompt('deep_search')
        self.link2name = {}
        
        # Track all valid links from search results for validation
        self.valid_links = {}  # {url: {title, description, query}}
        # Track sources actually used (clicked/browsed)
        self.used_sources = {}  # {url: {title, content_summary}}
    
    
    async def _prepare_init_prompt(self, input_data: dict) -> list[dict]:
        basic_task = input_data.get('task', '')
        query = input_data.get('query', None)
        max_iterations = input_data.get('max_iterations', 5)

        if not query:
            raise ValueError("Input data must contain a 'task' key.")
        
        # Get target language from config
        target_language = self.config.config.get('language', 'zh')
        language_mapping = {
            'zh': 'Chinese (中文)',
            'en': 'English'
        }
        target_language_name = language_mapping.get(target_language, target_language)
            
        return [{
            "role": "user",
            "content": self.DEEP_SEARCH_PROMPT.format(
                basic_task=basic_task,
                question=query,
                current_time=self.current_time,
                max_iterations=max_iterations,
                target_language=target_language_name
            )
        }]

    async def _handle_max_round(self, conversation_history):
        conversation_history = [item["content"] for item in conversation_history]
        analysis_info = "\n\n".join(conversation_history)
        prompt = f"You have reached the maximum number of running iterations. Directly give the summary of your search process based on the conversation history.\n\nConversation history: {analysis_info}\n\n"
        response = await self.llm.generate(
            messages = [
                {"role": "user", "content": prompt}
            ],
            response_format = {"type": "json_object"}
        )
        final_result = response
        return {'coversation_history': conversation_history, 'final_result': final_result}
    
    async def _handle_search_action(self, action_content):
        search_engine = [item for item in self.tools if 'search' in item.name.lower()][0]
        self.logger.info(f"Search action started: query={action_content}")
        try:
            search_result = await search_engine.api_function(action_content)
            search_result_list = []
            if len(search_result) == 0:
                result = f"Query `{action_content}` returned no results; please try again."
            else:
                result = f"Search results for `{action_content}`\n"
 
                for idx, item in enumerate(search_result):
                    title = item.name
                    link = item.link
                    description = item.description
                    search_result_list.append({
                        'query': action_content,
                        'title': title,
                        'link': link,
                        'description': description
                    })
                    self.link2name[link] = title
                    # Track this as a valid link for later validation
                    self.valid_links[link] = {
                        'title': title,
                        'description': description,
                        'query': action_content
                    }
                    result += 'Result ' + str(idx + 1) + ':\n'
                    result += f"Title: {title}\n"
                    result += f"Link: {link}\n"
                    result += f"Summary: {description}\n\n"
                    
            for search_item in search_result:
                self.memory.add_data(search_item)
            self.memory.add_log(
                id = search_engine.id, 
                type=search_engine.type,
                input_data = {'query': action_content}, 
                output_data = {'result': search_result_list}, 
                error=False, 
                note=f"Search engine {search_engine.name} executed successfully"
            )
            self.logger.info(f"Search action done: query={action_content}")
                
        except Exception as e:
            result = f"Query `{action_content}` failed with error: {str(e)}. Please retry."
            self.memory.add_log(
                id = search_engine.id, 
                type=search_engine.type,
                input_data = {'query': action_content}, 
                output_data = {"result": result}, 
                error=True, 
                note=f"Search engine {search_engine.name} executed failed: {str(e)}"
            )
            self.logger.error(f"Search action failed: query={action_content}, error={e}", exc_info=True)
        
        # On the last iteration, append available sources reminder
        if self.current_round >= (self.max_iterations - 1):
            result += "\n\n⚠️ You have reached the maximum number of running iterations. Please provide your final report now."
            result += self._build_available_sources_list()
        return {
            "action": "search",
            "action_content": action_content,
            "result": result,
            "continue": True
        }
    
    async def _handle_click_action(self, action_content):
        click_engine = [item for item in self.tools if 'content fetcher' in item.name.lower()][0]
        current_task = self.current_task_data.get('task', '')
        query = self.current_task_data.get('query', '')

        # Validate that the URL was from search results
        if action_content not in self.valid_links:
            self.logger.warning(f"Click rejected: URL not found in search results: {action_content}")
            # Provide available links as guidance
            available_links_hint = ""
            if self.valid_links:
                available_links_hint = "\n\nAvailable links from search results:\n"
                for idx, (url, info) in enumerate(list(self.valid_links.items())[:10], 1):
                    available_links_hint += f"{idx}. {info['title']}\n   URL: {url}\n"
            
            result = (
                f"ERROR: The URL '{action_content}' was not found in your search results. "
                f"You can ONLY click URLs that appeared in previous search results. "
                f"Please use one of the URLs from your search results, or perform a new search."
                f"{available_links_hint}"
            )
            return {
                "action": "click",
                "action_content": action_content,
                "result": result,
                "continue": True
            }

        try:
            self.logger.info(f"Click action started: url={action_content}")
            click_result = await click_engine.api_function([action_content], f'Research goal: {current_task}; query: {query}')
            if len(click_result) == 0:
                result = "Failed to fetch content for url: " + action_content
            else:
                result = click_result[0].data
                # Track this as a used source with content summary
                source_title = self.link2name.get(action_content, self.valid_links.get(action_content, {}).get('title', 'Unknown'))
                self.used_sources[action_content] = {
                    'title': source_title,
                    'content_preview': result[:500] if len(result) > 500 else result
                }
            # add to memory
            if click_result[0].link in self.link2name:
                click_result[0].name = self.link2name[click_result[0].link]
            if not ('error' in click_result[0].name.lower()):
                self.memory.add_data(click_result[0])
            self.memory.add_log(
                id = click_engine.id, 
                type=click_engine.type,
                input_data = {'url': action_content}, 
                output_data = {"result": result}, 
                error=False, 
                note=f"Click engine {click_engine.name} executed successfully"
            )
            self.logger.info(f"Click action done: url={action_content}")
            
        except Exception as e:
            result =  "Failed to fetch url: " + action_content + "\n"
            result += f'Error: {e}'
            self.memory.add_log(
                id = click_engine.id, 
                type=click_engine.type,
                input_data = {'url': action_content}, 
                output_data = {"result": result}, 
                error=True, 
                note=f"Click engine {click_engine.name} executed failed: {str(e)}"
            )
            self.logger.error(f"Click action failed: url={action_content}, error={e}", exc_info=True)
        
        # On the last iteration, append available sources reminder
        if self.current_round >= (self.max_iterations - 1):
            result += "\n\n⚠️ You have reached the maximum number of running iterations. Please provide your final report now."
            result += self._build_available_sources_list()
            
        return {
            "action": "click",
            "action_content": action_content,
            "result": result,
            "continue": True
        }

    def _build_available_sources_list(self) -> str:
        """Build a formatted list of all available sources from search results and browsed pages."""
        if not self.valid_links and not self.used_sources:
            return ""
        
        sources_text = "\n\n---\n**VERIFIED SOURCES AVAILABLE FOR CITATION:**\n"
        sources_text += "(You may ONLY use URLs from this list in your References section)\n\n"
        
        # First list browsed/used sources (highest quality)
        if self.used_sources:
            sources_text += "**Sources you have browsed (recommended for citation):**\n"
            for idx, (url, info) in enumerate(self.used_sources.items(), 1):
                sources_text += f"  {idx}. {info['title']}\n"
                sources_text += f"     URL: {url}\n"
        
        # Then list search results that weren't clicked
        unclicked_sources = {url: info for url, info in self.valid_links.items() 
                           if url not in self.used_sources}
        if unclicked_sources:
            sources_text += "\n**Additional sources from search results (snippets only):**\n"
            for idx, (url, info) in enumerate(unclicked_sources.items(), 1):
                sources_text += f"  {idx}. {info['title']}\n"
                sources_text += f"     URL: {url}\n"
                sources_text += f"     Summary: {info['description'][:200]}...\n" if len(info['description']) > 200 else f"     Summary: {info['description']}\n"
        
        sources_text += "\n---\n"
        return sources_text

    async def _handle_report_action(self, action_content: str):
        """Handle a 'final' action from the LLM."""
        return {
            "action": "final_report",
            "action_content": action_content,
            "result": action_content,
            "continue": False,
        }
    
    def _get_persist_extra_state(self) -> dict:
        """Persist valid_links and used_sources for resume support."""
        return {
            'valid_links': self.valid_links,
            'used_sources': self.used_sources,
            'link2name': self.link2name,
        }
    
    def _load_persist_extra_state(self, state: dict):
        """Restore valid_links and used_sources from checkpoint."""
        self.valid_links = state.get('valid_links', {})
        self.used_sources = state.get('used_sources', {})
        self.link2name = state.get('link2name', {})

    async def async_run(
        self, 
        input_data: dict, 
        max_iterations: int = 30,
        stop_words: list[str] = [],
        echo=False,
        resume: bool = True,
        checkpoint_name: str = 'deepsearch_latest.pkl',
        # stop_words: list[str] = ["</click>", "</search>", "</report>"]
    ) -> dict:
        input_data['max_iterations'] = max_iterations
        self.max_iterations = max_iterations
        await self._prepare_executor()
        run_result = await super().async_run(
            input_data=input_data,
            max_iterations=max_iterations,
            stop_words=stop_words,
            echo=echo,
            resume=resume,
            checkpoint_name=checkpoint_name,
        )
        agent_result = DeepSearchResult(
            query=input_data['query'], 
            name=f"Summary of the search process for {input_data['query']}", 
            description=run_result['final_result'],
            data=run_result['final_result'], 
            source=self.AGENT_NAME
        )
        self.memory.add_data(agent_result)
        return run_result
        
# TODO: add agentresult class
class DeepSearchResult(ToolResult):
    def __init__(self, query, name, description, data, source=""):
        super().__init__(name, description, data, source)
        self.query = query

    def __str__(self):
        format_output = f'Summary Search Result for {self.query}\n'
        format_output += f"Summary: {self.description}\n"
        return format_output

    def __repr__(self):
        return self.__str__()