"""
Finsight Tools Module

This module provides a unified interface for accessing all available financial data collection tools.
"""

import importlib
import inspect
from typing import Dict, List, Type, Any, Optional
from .base import Tool, ToolResult

from .web.web_crawler import *
from .web.search_engine_requests import *
from .web.search_engine_playwright import *
from .web.base_search import *
from .macro.macro import *
from .financial.company_statements import *
from .financial.stock import *
from .financial.market import *
from .industry.industry import *

# Global registry for all tools
_REGISTERED_TOOLS: Dict[str, Type[Tool]] = {}
_TOOL_CATEGORIES: Dict[str, List[str]] = {
    'financial': [],
    'macro': [],
    'industry': [],
    'web': []
}

def register_tool(tool_class: Type[Tool], category: str = 'general') -> Type[Tool]:
    try:
        tool_name = tool_class().name
        _REGISTERED_TOOLS[tool_name] = tool_class
        if category not in _TOOL_CATEGORIES:
            _TOOL_CATEGORIES[category] = []
        _TOOL_CATEGORIES[category].append(tool_name)
        
        # print(f"Registered tool: {tool_name} in category: {category}")
        
    except Exception as e:
        print(f"Warning: Failed to register tool {tool_class.__name__}: {e}")
    
    return tool_class

def get_avail_tools(category: Optional[str] = None) -> Dict[str, Type[Tool]]:
    """
    Get all available tools, optionally filtered by category.
    
    Args:
        category: Optional category filter. If None, returns all tools.
        
    Returns:
        Dictionary mapping tool names to tool classes
    """
    if category is None:
        return _REGISTERED_TOOLS.copy()
    
    if category not in _TOOL_CATEGORIES:
        return {}
    
    return {
        tool_name: _REGISTERED_TOOLS[tool_name] 
        for tool_name in _TOOL_CATEGORIES[category]
        if tool_name in _REGISTERED_TOOLS
    }

def get_tool_by_name(tool_name: str) -> Optional[Type[Tool]]:
    """
    Get a specific tool by name.
    
    Args:
        tool_name: Name of the tool to retrieve
        
    Returns:
        Tool class if found, None otherwise
    """
    return _REGISTERED_TOOLS.get(tool_name)

def get_tool_categories() -> Dict[str, List[str]]:
    """
    Get all tool categories and their associated tools.
    
    Returns:
        Dictionary mapping categories to lists of tool names
    """
    return _TOOL_CATEGORIES.copy()

def list_tools() -> List[str]:
    """
    List all registered tool names.
    
    Returns:
        List of tool names
    """
    return list(_REGISTERED_TOOLS.keys())

def get_tool_info(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Dictionary with tool information, or None if tool not found
    """
    tool_class = get_tool_by_name(tool_name)
    if tool_class is None:
        return None

    return {
            'name': tool_class.name,
            'description': tool_class.description,
            'parameters': tool_class.parameters,
        }

# Auto-register tools from submodules
def _auto_register_tools():
    """Automatically discover and register tools from submodules."""
    import os
    import pkgutil
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Dynamically discover all submodules
    submodules = []
    
    # Walk through all subdirectories and find Python modules
    for importer, modname, ispkg in pkgutil.walk_packages([current_dir], prefix=f"{__name__}."):
        if not ispkg:  # Only import modules, not packages
            submodules.append(modname)
    
    # print(f"Discovered {len(submodules)} submodules: {submodules}")
    
    for submodule in submodules:
        try:
            # Convert module name to relative import format
            relative_name = submodule.replace(f"{__name__}.", "")
            module = importlib.import_module(f'.{relative_name}', package=__name__)
            
            # Find all classes that inherit from Tool
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, Tool) and 
                    obj != Tool and 
                    obj.__module__ == module.__name__):
                    
                    # Determine category from submodule path
                    category = 'general'  # default category
                    if '.' in relative_name:
                        # Extract category from path (e.g., 'financial.stock' -> 'financial')
                        category = relative_name.split('.')[0]
                    
                    register_tool(obj, category)
                    
        except Exception as e:
            print(f"Warning: Failed to import submodule {submodule}: {e}")

# Auto-register tools when module is imported
_auto_register_tools()

# Export main functions and classes
__all__ = [
    'Tool',
    'ToolResult', 
    'register_tool',
    'get_avail_tools',
    'get_tool_by_name',
    'get_tool_categories',
    'list_tools',
    'get_tool_info'
]

