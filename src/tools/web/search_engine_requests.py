"""
Legacy Search Implementations

This module contains commented-out legacy search implementations for reference.
These implementations are kept for historical purposes and potential future use.
"""

from typing import List
import urllib.parse
import httpx
import json
import os
from bs4 import BeautifulSoup

from ..base import Tool, ToolResult
from .base_search import SearchResult, ImageSearchResult


class BingSearch(Tool):
    """
    Legacy Bing search implementation that relies on HTTP requests with fixed cookies/headers.
    """

    def __init__(self):
        super().__init__(
            name="Bing Web Search (requests)",
            description="HTTP-based Bing search helper for retrieving result summaries.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )
 
        self.backend = 'requests'
        self.type = 'tool_search'
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            "Cookie": "MUID=1C948923B2A965190E139DB3B38764BB; ..."
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        """
        Run the legacy Bing search workflow.

        Args:
            query: Search keywords.

        Returns:
            A list of ToolResult entries built from the HTML response.
        """
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://cn.bing.com/search?q={encoded_query}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                result_list = []

                # Extract the primary search-result content
                for item in soup.find_all('li', class_='b_algo'):
                    try:
                        title = item.find('h2').text
                        description_tag = item.find('p')
                        description = description_tag.text if description_tag else "No description available"
                        link = item.find('a')['href']
                        result_list.append(SearchResult(
                            query=query,
                            name=title,
                            description=description,
                            link=link,
                            data=[{'title': title, 'description': description, 'link': link}],
                            source=f'{title}\n{link}'
                            # source=f"Bing. https://www.bing.com/search?q={query}"
                        ))
                    except Exception as e:
                        print(f"An error occurred while extracting search results: {str(e)}")

                return result_list
            else:
                print(f"Error: Request failed with status code {response.status_code}")
                return []


class BochaSearch(Tool):
    """
    Legacy Bocha search implementation powered by direct HTTP requests.
    """

    def __init__(self):
        super().__init__(
            name="Bocha web search",
            description="HTTP-based Bocha search helper for retrieving document snippets.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )

        self.backend = 'requests'
        self.type = 'tool_search'
        api_key = os.getenv("BOCHAAI_API_KEY", "")
        if not api_key:
            print("Warning: BOCHAAI_API_KEY is not set; BochaSearch requests may fail.")
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        """
        Execute the legacy Bocha search via its HTTP endpoint.

        Args:
            query: Search keywords.

        Returns:
            A list of ToolResult entries populated from the API payload.
        """
        async with httpx.AsyncClient() as client:
            url = "https://api.bochaai.com/v1/web-search"
            payload = json.dumps({
                "query": query,
                "summary": True,
                "count": 10
            })
            
            response = await client.post(url, headers=self.headers, data=payload)
            result = response.json()['data']['webPages']['value']
            result_list = []
            if len(result) > 0:
                for item in result:
                    if 'name' in item and 'url' in item and 'snippet' in item:
                        title = item['name']
                        link = item['url']
                        description = item['summary']
                        result_list.append(SearchResult(
                            query=query,
                            name=title,
                            description=description,
                            link=link,
                            data=[{'title': title, 'link': link, 'description': description}],
                            source=f'{title}\n{link}'
                            # source=f"Bocha Search Engine, https://api.bochaai.com/v1/web-search?query={query}"
                        ))
                return result_list
            else:
                print(f"Error: Request failed with status code {response.status_code}")
                return []



class SerperSearch(Tool):
    """
    Serper search implementation powered by direct HTTP requests.
    """

    def __init__(self):
        super().__init__(
            name="Google Search Engine",
            description="HTTP-based Google search helper for retrieving document snippets.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )

        self.backend = 'requests'
        self.type = 'tool_search'
        api_key = os.getenv("SERPER_API_KEY", "")
        if not api_key:
            print("Warning: SERPER_API_KEY is not set; SerperSearch requests may fail.")
        self.headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        """
        Execute the legacy Bocha search via its HTTP endpoint.

        Args:
            query: Search keywords.

        Returns:
            A list of ToolResult entries populated from the API payload.
        """
        async with httpx.AsyncClient() as client:
            url = "https://google.serper.dev/search"
            payload = json.dumps({
                "q": query,
            })
            
            response = await client.post(url, headers=self.headers, data=payload)
            result = response.json()['organic']
            result_list = []
            if len(result) > 0:
                for item in result:
                    
                    title = item['title']
                    link = item['link']
                    description = item['snippet']
                    result_list.append(SearchResult(
                        query=query,
                        name=title,
                        description=description,
                        link=link,
                        data=[{'title': title, 'link': link, 'description': description}],
                        source=f'{title}\n{link}'
                        # source=f"Google Search Engine, https://google.serper.dev/search?q={query}"
                    ))
                return result_list
            else:
                print(f"Error: Request failed with status code {response.status_code}")
                return []


class DuckDuckGoSearch(Tool):
    """
    Legacy DuckDuckGo search implementation based on raw HTTP requests.
    """

    def __init__(self):
        super().__init__(
            name="DuckDuckGo web search (requests)",
            description="DuckDuckGo-powered web search helper that fetches HTML results.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )
        self.backend = 'requests'
        self.type = 'tool_search'
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        """
        Run the DuckDuckGo HTML search flow.

        Args:
            query: Search keywords.

        Returns:
            List[ToolResult]: Search results packed into SearchResult entries.
        """
        URL = "https://duckduckgo.com/html/"
        params = {'q': query}

        print(f"Searching DuckDuckGo for '{query}'...")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(URL, headers=self.headers, params=params)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                results_container = soup.find_all('div', class_='result')
                
                if not results_container:
                    print("No results were found, or the page structure has changed.")
                    return []

                search_results = []
                for result in results_container:
                    title_element = result.find('a', class_='result__a')
                    if not title_element:
                        continue

                    title = title_element.text.strip()
                    raw_link = title_element.get('href', '')
                    
                    # Handle DuckDuckGo redirect links
                    if raw_link and 'uddg=' in raw_link:
                        from urllib.parse import unquote
                        link = unquote(raw_link.split('uddg=')[-1])
                    else:
                        link = raw_link

                    snippet_element = result.find('a', class_='result__snippet')
                    snippet = snippet_element.text.strip() if snippet_element else "..."

                    search_results.append(SearchResult(
                        query=query,
                        name=title,
                        description=snippet,
                        link=link,
                        data=[{'title': title, 'link': link, 'description': snippet}],
                        source=f'{title}\n{link}'
                        # source=f"DuckDuckGo. https://www.duckduckgo.com/html/?q={query}"
                    ))

                return search_results
        except Exception as e:
            print(f"Error: {e}")
            return []


class SogouSearch(Tool):
    """
    Legacy Sogou search implementation backed by the sogou_search library.
    """

    def __init__(self):
        super().__init__(
            name="Sogou web search",
            description="Sogou-powered search helper built on the sogou_search package.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )
        self.backend = 'requests'
        self.type = 'tool_search'

    async def api_function(self, query: str) -> List[ToolResult]:
        """
        Execute the Sogou search workflow.

        Args:
            query: Search keywords.

        Returns:
            List[ToolResult]: Search results packaged as SearchResult objects.
        """
        try:
            from sogou_search import sogou_search
            results = sogou_search(query, num_results=10)
            result_list = []
            for item in results:
                if isinstance(item, dict) and 'title' in item:
                    title = item.get('title', '')
                    description = item.get('description', item.get('snippet', ''))
                    link = item.get('link', item.get('url', ''))
                    result_list.append(SearchResult(
                        query=query,
                        name=title,
                        description=description,
                        link=link,
                        data=[{'title': title, 'description': description, 'link': link}],
                        source=f'{title}\n{link}'
                        # source=f"Sogou. https://www.sogou.com/web?query={query}"
                    ))
            return result_list
        except ImportError:
            print("Error: sogou_search library not available")
            return []


class InDomainSearch_Request(Tool):
    """
    Legacy in-domain financial news search implemented via HTTP requests.
    """

    def __init__(self):
        super().__init__(
            name="Financial site in-domain search (requests)",
            description="Queries pre-selected financial news domains for pages related to the given keywords.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )
        self.backend = 'requests'
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
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36 EdgA/123.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zsdch, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.bing.com/",
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        """
        Run in-domain searches across the configured financial news sites.

        Args:
            query: Search keywords.

        Returns:
            A list of SearchResult objects, one per domain that produced hits.
        """
        final_result_list = []
        async with httpx.AsyncClient() as client:
            for domain in self.domain_list[:2]:  # Limit the number of domains per call
                domain_query = f"site:{domain} {query}"
                params = {
                    "q": domain_query, 
                    "sc": "0-10", 
                    "ajaxnorecss": "1", 
                    "jsoncbid": "0", 
                    "qs": "n", 
                    "form": "QBRE", 
                    "sp": "-1"
                }
                url = "https://www.bing.com/search"
                response = await client.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    for item in soup.find_all('li', class_='b_algo'):
                        try:
                            title = item.find('h2').text
                            description_tag = item.find('p')
                            description = description_tag.text if description_tag else "No description available"
                            link = item.find('a')['href']
                            final_result_list.append(SearchResult(
                                query=query,
                                name=title,
                                description=description,
                                link=link,
                                data=[{'title': title, 'description': description, 'link': link}],
                                source=f'{title}\n{link}'
                                # source=f"{domain}"
                            ))
                        except Exception as e:
                            print(f"An error occurred while extracting search results: {str(e)}")
        return final_result_list


class BingImageSearch(Tool):
    """
    Legacy Bing image search helper built on direct HTTP requests.
    """

    def __init__(self):
        super().__init__(
            name="Bing image search",
            description="Image search helper that scrapes Bing image results for a query.",
            parameters=[
                {"name": "query", "type": "str", "description": "Keywords for the image search", "required": True}
            ],
        )
        self.backend = 'requests'
        self.type = 'tool_search'

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Connection": "keep-alive",
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        """
        Execute the Bing image search and return scraped results.

        Args:
            query: Search keywords.

        Returns:
            List[ToolResult]: Image result entries.
        """
        # Build the image-search URL
        url = f"https://www.bing.com/images/search?q={query}&form=HDRSC3&first=1"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url=url, headers=self.headers, timeout=10)
                response.raise_for_status()

                # Parse the HTML payload
                soup = BeautifulSoup(response.text, 'html.parser')
                result_list = []

                # Locate image metadata
                image_items = soup.find_all('a', class_='iusc')

                for item in image_items:
                    try:
                        # Parse the embedded JSON metadata
                        json_data = json.loads(item['m'])
                        
                        # Extract fields
                        title = json_data.get('t', "Untitled")
                        image_url = json_data.get('murl')
                        page_url = json_data.get('purl')

                        if image_url and page_url:
                            result_list.append(ImageSearchResult(
                                query=query,
                                name=title,
                                description=f"Image search result: {title}",
                                link=page_url,
                                data=[{
                                    'title': title,
                                    'image_url': image_url,
                                    'page_url': page_url
                                }]
                            ))
                    except (KeyError, json.JSONDecodeError, TypeError):
                        continue

                if not result_list:
                    print(f"No image results could be parsed for '{query}'.")
                    return []

                return result_list
        except httpx.RequestError as e:
            print(f"Error: Bing image search request failed: {e}")
            return []



