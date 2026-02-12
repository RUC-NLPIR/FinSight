"""Tests for the plugin loader in src.plugins.

Proves:
1. Empty dir returns (0, 0).
2. Non-existent dir is silently skipped.
3. A valid plugin Tool subclass is discovered and registered.
4. Broken plugin files produce a warning, not a crash.
5. None input returns (0, 0).
"""

import os
import warnings

import pytest

from src.plugins import load_plugins


@pytest.fixture
def plugin_dir(tmp_path):
    """Create a temp directory with a sample plugin."""
    plugin_code = '''
from src.tools.base import Tool, ToolResult

class MyCustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="Custom Plugin Tool",
            description="A test plugin tool.",
            parameters=[],
        )

    async def api_function(self):
        return [ToolResult(name=self.name, description="test", data="hello", source="plugin")]
'''
    plugin_file = tmp_path / "my_plugin.py"
    plugin_file.write_text(plugin_code)
    return str(tmp_path)


@pytest.fixture
def broken_plugin_dir(tmp_path):
    """Create a temp directory with a broken plugin."""
    broken_code = "import this_module_does_not_exist_at_all_xyz"
    (tmp_path / "broken.py").write_text(broken_code)
    return str(tmp_path)


class TestPluginLoader:
    def test_none_input(self):
        assert load_plugins(None) == (0, 0)

    def test_empty_list(self):
        assert load_plugins([]) == (0, 0)

    def test_nonexistent_dir(self):
        assert load_plugins(["/nonexistent/dir/abc123"]) == (0, 0)

    def test_empty_dir(self, tmp_path):
        assert load_plugins([str(tmp_path)]) == (0, 0)

    def test_valid_plugin_discovered(self, plugin_dir):
        tools, agents = load_plugins([plugin_dir])
        assert tools == 1
        assert agents == 0

        # Verify it was registered
        from src.tools import get_tool_by_name
        cls = get_tool_by_name("Custom Plugin Tool")
        assert cls is not None

    def test_broken_plugin_warns(self, broken_plugin_dir):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            tools, agents = load_plugins([broken_plugin_dir])
            assert tools == 0
            assert any("Failed to load plugin" in str(warning.message) for warning in w)
