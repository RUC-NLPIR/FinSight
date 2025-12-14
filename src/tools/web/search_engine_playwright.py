"""
Search Engine APIs

This module contains various search engine implementations for web search functionality.
"""

from typing import List
import urllib.parse
import json
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from ..base import Tool, ToolResult
from .base_search import SearchResult, ImageSearchResult


class PlaywrightSearch(Tool):
    """
    Bing web-search helper implemented with Playwright to support dynamic pages.
    """

    def __init__(self):
        super().__init__(
            name="Bing web search (Playwright)",
            description="Browser-automation Bing search tool that returns result snippets for a query.",
            parameters=[{"name": "query", "type": "str", "description": "Keywords for the search", "required": True}],
        )
        self.backend = 'playwright'
        self.type = 'tool_search'
    
    async def api_function(self, query: str) -> List[ToolResult]:
        """
        Execute a Bing search via Playwright and return structured results.

        Args:
            query: Search keywords.

        Returns:
            List[ToolResult]: Search results list.
        """
        results = []
        async with async_playwright() as p:
            # Launch Chromium
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
                locale="zh-CN",
                viewport={'width': 2560, 'height': 1440}
            )
            page = await context.new_page()
                
            try:
                # Build the search URL
                search_url = f"https://cn.bing.com/search?q={urllib.parse.quote_plus(query)}"
                
                # Visit the results page
                print(f"Visiting: {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded")
                
                # Handle cookie prompt
                accept_button = page.locator("#bnp_btn_accept")
                try:
                    await accept_button.wait_for(state='visible', timeout=3000)
                    print("Cookie consent detected; accepting...")
                    await accept_button.click()
                except Exception:
                    print("No cookie prompt detected.")

                # Wait for results to load
                print("Waiting for search results to render...")
                await page.locator("#b_results").wait_for(state='visible', timeout=30000)
                print("Page ready, parsing results...")
                
                # Extract the result list
                result_items = await page.locator("li.b_algo").all()
                print(f"Found {len(result_items)} results.")

                # Gather result metadata
                for item in result_items:
                    title_element = item.locator("h2 > a")
                    snippet_element = item.locator(".b_caption p")

                    title = await title_element.inner_text() if await title_element.count() > 0 else ""
                    link = await title_element.get_attribute("href") if await title_element.count() > 0 else ""
                    description = await snippet_element.inner_text() if await snippet_element.count() > 0 else ""
                    
                    if title and link:
                        results.append({
                            'title': title,
                            'link': link,
                            'description': description
                        })
                        
            except Exception as e:
                print(f"An error occurred during the search: {e}")
            finally:
                print("Closing browser...")
                await browser.close()
                
        return [
            SearchResult(
                name=f"Bing search results (query: {query})",
                description=f"Search results, snippets, and links for {query}",
                data=results,
                source=f"Bing search. https://www.bing.com/search?q={query}"
            )
        ]



class InDomainSearch_Playwright(Tool):
    """
    Financial-site in-domain search implemented with Playwright.
    """

    def __init__(self):
        super().__init__(
            name="Financial site in-domain search (Playwright)",
            description="Searches pre-defined financial news domains (e.g., Sina, Caixin) for a given keyword.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )

        self.backend = 'playwright'
        self.type = 'tool_search'
        
        self.domain_list = [
            "https://finance.sina.com.cn/",
            "https://china.caixin.com/",
            "https://economy.gmw.cn/",
            "https://www.21jingji.com/",
            "https://www.eeo.com.cn/",
            "https://www.cls.cn/",
            "https://news.hexun.com/"
        ]
        self.searcher = PlaywrightSearch()

    async def api_function(self, query: str) -> List[ToolResult]:
        """
        Execute searches scoped to the configured financial domains.

        Args:
            query: Search keywords.

        Returns:
            List[ToolResult]: In-domain result sets.
        """
        final_result_list = []
        for domain in self.domain_list:
            domain_query = f"site:{domain} {query}"
            response = await self.searcher.api_function(domain_query)
            for item in response:
                final_result_list.append(SearchResult(
                    name=f"In-domain financial search: {query}",
                    description=f"Results for {query} within {domain}",
                    data=item.data[:5],
                    source=f"{domain}"
                ))
        return final_result_list