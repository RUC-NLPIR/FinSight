"""Tests for the Tool and ToolResult base classes in src.tools.base.

We load src/tools/base.py directly via importlib.util to avoid triggering
the package __init__.py, which cascades into heavy optional dependencies
(crawl4ai, playwright, browser-use, etc.) that may not be installed.
"""

import importlib.util
import os
import sys

import pandas as pd
import pytest

# Load base.py as a standalone module without triggering src.tools.__init__
_base_path = os.path.join(os.path.dirname(__file__), "..", "src", "tools", "base.py")
_spec = importlib.util.spec_from_file_location("_tools_base", os.path.abspath(_base_path))
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
Tool = _base.Tool
ToolResult = _base.ToolResult


# ---------------------------------------------------------------------------
# ToolResult tests
# ---------------------------------------------------------------------------

class TestToolResult:
    """Verify ToolResult data handling and string representations."""

    def test_basic_creation(self):
        r = ToolResult("test", "desc", {"key": "val"}, source="http://example.com")
        assert r.name == "test"
        assert r.description == "desc"
        assert r.data == {"key": "val"}
        assert r.source == "http://example.com"

    def test_single_item_list_unwrap(self):
        """A list with exactly one element should be unwrapped."""
        r = ToolResult("test", "desc", [42])
        assert r.data == 42

    def test_multi_item_list_kept(self):
        """A list with multiple elements stays as-is."""
        r = ToolResult("test", "desc", [1, 2, 3])
        assert r.data == [1, 2, 3]

    def test_dataframe_str(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        r = ToolResult("test", "desc", df)
        s = str(r)
        assert "First five rows:" in s

    def test_dict_str(self):
        r = ToolResult("test", "desc", {"key": "value"})
        s = str(r)
        assert "Partial data preview:" in s

    def test_hash_and_eq(self):
        r1 = ToolResult("name", "desc", 1)
        r2 = ToolResult("name", "desc", 999)
        assert r1 == r2
        assert hash(r1) == hash(r2)

    def test_not_equal(self):
        r1 = ToolResult("name1", "desc", 1)
        r2 = ToolResult("name2", "desc", 1)
        assert r1 != r2

    def test_get_full_string_df(self):
        df = pd.DataFrame({"col": range(20)})
        r = ToolResult("test", "desc", df)
        full = r.get_full_string()
        # to_string() for 20 rows includes all rows
        assert "19" in full

    def test_get_full_string_non_df(self):
        r = ToolResult("test", "desc", "hello world")
        assert r.get_full_string() == "hello world"


# ---------------------------------------------------------------------------
# Tool base class tests
# ---------------------------------------------------------------------------

class TestToolBase:
    """Verify the Tool base class contract."""

    def test_id_unique(self):
        """Two instances of the same tool class get different IDs."""
        t1 = Tool("test", "desc", [])
        t2 = Tool("test", "desc", [])
        assert t1.id != t2.id

    def test_description_formatting(self):
        t = Tool(
            "MyTool",
            "Does stuff",
            [{"name": "x", "type": "int", "description": "a number"}],
        )
        desc = t.description
        assert "MyTool" in desc
        assert "Does stuff" in desc
        assert "x: int" in desc

    def test_prepare_params_default(self):
        t = Tool("t", "d", [])
        assert t.prepare_params(None) == {}

    @pytest.mark.asyncio
    async def test_api_function_not_implemented(self):
        t = Tool("t", "d", [])
        with pytest.raises(NotImplementedError):
            await t.api_function()
