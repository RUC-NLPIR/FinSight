"""
Web Search Tools Module

This module provides web search and content extraction functionality.
It imports and exposes the main search tools from submodules.
"""

from ..base import ToolResult

class SearchResult(ToolResult):
    """Container for web search results."""

    def __init__(self, query, name, description, data, link = "", source=""):
        super().__init__(name, description, data, source)
        self.query = query
        self.link = link

    def __str__(self):
        format_output = f'Search Result for {self.query}\n'
        format_output += f"Title: {self.name}\n"
        format_output += f"Summary: {self.description}\n"
        format_output += f"Link: {self.link}\n\n"
        return format_output

    def __repr__(self):
        return self.__str__()


class ImageSearchResult(SearchResult):
    """Container for image search results."""

    def __init__(self, query, name, description, data, link = "", source=""):
        super().__init__(query, name, description, data, link, source)

    def __str__(self):
        format_output = f'Image Search Result for {self.query}\n'
        format_output += f"Title: {self.name}\n"
        format_output += f"Summary: {self.description}\n"
        format_output += f"Image Link: {self.data['image_url']}\n\n"
        format_output += f"Page Link: {self.data['page_url']}\n\n"
        return format_output

    def __repr__(self):
        return self.__str__()
