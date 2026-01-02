"""
Web Crawler APIs

This module contains web crawling and content extraction functionality.
"""

from typing import List, Dict
import re
import json
import asyncio
import aiohttp
import httpx
from io import BytesIO
import pdfplumber
import chardet

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from openai import OpenAI
from bs4 import BeautifulSoup

from ..base import Tool, ToolResult




class Click(Tool):
    """
    Web-page detail retrieval tool that fetches HTML or PDF content for review.
    """

    def __init__(self):
        super().__init__(
            name="Web page content fetcher",
            description="Retrieve detailed content for the supplied URLs (HTML or PDF) to support downstream analysis.",
            parameters=[
                {"name": "urls", "type": "List[str]", "description": "List of URLs to crawl", "required": True},
                {"name": "task", "type": "str", "description": "Overall task description used for filtering/summarization", "required": True}
            ],
        )
        self.type = 'tool_click'
    
    async def fetch_url(self, url: str) -> str:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        return f"Error fetching url: HTTP status code {response.status}"
                    
                    # Decode with detected encoding to avoid UTF-8 decode errors
                    raw_bytes = await response.read()
                    if not raw_bytes:
                        return "Error fetching url: Empty response"
                    detected_encoding = response.charset or chardet.detect(raw_bytes).get('encoding') or 'utf-8'
                    html_content = raw_bytes.decode(detected_encoding, errors='replace')
            
            soup = BeautifulSoup(html_content, 'html.parser')

            for element in soup(['script', 'style', 'meta', 'noscript', 'head', 'title']):
                element.extract() 
            text = soup.get_text(separator=' ')
        
            lines = (line.strip() for line in text.splitlines())
            clean_text = '\n'.join(line for line in lines if line)
   
            return clean_text

        except asyncio.TimeoutError:
            return "Error fetching url: Request timeout"
        except Exception as e:
            return f"Error fetching url: {str(e)}"

    async def api_function(self, urls: List[str], task: str) -> List[ToolResult]:
        """
        Crawl each URL and return the retrieved content (up to 10,000 chars).

        Args:
            urls: List of target URLs.
            task: Task description for future filtering (currently unused).

        Returns:
            List[ToolResult]: Collected page snippets.
        """
        if isinstance(urls, str):
            urls = [urls]
        try:
            browser_conf = BrowserConfig(headless=True)  # or False to see the browser
            run_conf = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS
            )
            result_list = []
            for url in urls:
                if url.endswith(".pdf"):
                    content = await self.extract_pdf_text_async(url)
                else:
                    async with AsyncWebCrawler(config=browser_conf) as crawler:
                        result = await crawler.arun(url=url, config=run_conf)
                        content = str(result.markdown)
                    
                    # use naive requests with async to get the content
                    # content = await self.fetch_url(url)

                # if task == '' or len(content) < 10000:
                result_list.append(
                    ClickResult(
                        name=content[:30],
                        description=f"Title: {url}",
                        data=content[:6000],
                        link=url,
                        source=f"URL: {url}"
                    )
                )
                # else:    
                #     # Use an LLM to extract the task-relevant snippets
                #     response = llm.generate(
                #         messages=[
                #             {"role": "system", "content": CONTENT_SUMMARY_PROMPT},
                #             {"role": "user", "content": f"Extract information related to {task} from the following page:\n{content[:10000]}"}
                #         ]
                #     )
                    
                #     summary_json = self.extract_json_from_text(response)
                #     if summary_json and summary_json.get('title') and summary_json.get('content'):
                #         result_list.append(
                #             ClickResult(
                #                 name=f"Detailed information for {url}",
                #                 description=f"Title：{summary_json['title']}", 
                #                 data=summary_json['content'],
                #                 source=f"URL: {url}"
                #             )
                #         )
            return result_list

        except Exception as e:
            print(f"Error: {e}")
            return []
    

    def extract_json_from_text(self, text: str) -> Dict:
        """
        Attempt to parse a JSON object embedded in the supplied text.

        Args:
            text: Text that may contain JSON.

        Returns:
            Dict: Parsed JSON object, or None on failure.
        """
        # First attempt to match fenced ```json``` blocks
        pattern = r'```json(.*?)```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except Exception as e:
                print(f"Error parsing JSON from code block: {e}")
                return None
        else:
            # Fallback: parse the entire string as JSON
            try:
                return json.loads(text)
            except Exception as e:
                print(f"Error parsing JSON directly: {e}")
                return None

    async def extract_pdf_text_async(self, url: str) -> str:
        """
        Asynchronously extract text from a PDF URL.

        Args:
            url: PDF file URL.

        Returns:
            str: Extracted text or an error message.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30)
                if response.status_code != 200:
                    return f"Error: Unable to retrieve the PDF (status code {response.status_code})"
                
                content = response.content
                
                with pdfplumber.open(BytesIO(content)) as pdf:
                    full_text = ""
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            full_text += text
                
                return full_text
                
        except Exception as e:
            return f"Error: {str(e)}"


class ClickResult(ToolResult):
    """Container for web-content retrieval outputs."""

    def __init__(self, name, description, data, link="", source=""):
        super().__init__(name, description, data, source)
        self.link = link

    def __str__(self):
        format_output = self.name + "\n" + self.description + "\n\n"
        format_output += f"Content: {self.data}"
        return format_output
    
    def brief_str(self):
        format_output = self.name + "\n" + self.description + "\n\n"
        format_output += f"Content: {self.data[:100]}"
        return format_output

    def __repr__(self):
        return self.__str__()