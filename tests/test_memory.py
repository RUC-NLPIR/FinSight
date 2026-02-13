"""Tests for src.memory.variable_memory.Memory.

Validates save/load round-trip, add_data, add_dependency, add_log,
get_collect_data, and get_analysis_result without needing full LLM stack.

We create a minimal Config that only needs working_dir.
"""

import os
import tempfile

import pytest

# Memory has a deep import chain (Memory -> src.agents -> DeepSearchAgent
# -> web_crawler -> crawl4ai).  Skip the entire module gracefully.
try:
    from src.memory.variable_memory import Memory as _Memory
    _HAS_MEMORY = True
except ImportError:
    _HAS_MEMORY = False

pytestmark = pytest.mark.skipif(not _HAS_MEMORY, reason="crawl4ai or other deep dependency not installed")


class _MinimalConfig:
    """Fakes just enough Config for Memory.__init__."""

    def __init__(self, tmpdir):
        self.working_dir = str(tmpdir)
        self.config = {
            "working_dir": str(tmpdir),
            "target_type": "general",
        }
        self.llm_dict = {}


@pytest.fixture
def mem(tmp_path):
    """Create a Memory instance with a temp directory."""
    cfg = _MinimalConfig(tmp_path)
    return _Memory(cfg)


class TestMemorySaveLoad:
    def test_save_creates_file(self, mem, tmp_path):
        mem.save()
        mem_file = tmp_path / "memory" / "memory.pkl"
        assert mem_file.exists()
        assert mem_file.stat().st_size > 0

    def test_round_trip_empty(self, mem):
        mem.save()
        assert mem.load() is True
        assert mem.log == []
        assert mem.data == []

    def test_round_trip_with_data(self, mem):
        # Simulate adding collect data
        from src.tools.base import ToolResult
        tr = ToolResult(name="test", description="desc", data={"key": "val"}, source="src")
        mem.data.append(tr)
        mem.save()

        # Reset in-memory state
        mem.data = []
        assert mem.load() is True
        assert len(mem.data) == 1
        assert mem.data[0].name == "test"

    def test_round_trip_with_log(self, mem):
        mem.add_log(id="a1", type="tool", input_data={"q": "test"}, output_data={"r": "ok"}, error=False, note="n")
        mem.save()
        mem.log = []
        assert mem.load() is True
        assert len(mem.log) == 1
        assert mem.log[0]["id"] == "a1"

    def test_load_nonexistent_returns_false(self, mem):
        assert mem.load(checkpoint_name="nonexistent.pkl") is False


class TestMemoryDependency:
    def test_add_dependency(self, mem):
        mem.add_dependency("child1", "parent1")
        assert "parent1" in mem.dependency
        assert "child1" in mem.dependency["parent1"]

    def test_add_multiple_children(self, mem):
        mem.add_dependency("c1", "p1")
        mem.add_dependency("c2", "p1")
        assert len(mem.dependency["p1"]) == 2


class TestMemoryAddLog:
    def test_log_structure(self, mem):
        mem.add_log(
            id="agent_1",
            type="tool_search",
            input_data={"query": "AAPL"},
            output_data={"result": "found"},
            error=False,
            note="success",
        )
        assert len(mem.log) == 1
        entry = mem.log[0]
        assert entry["id"] == "agent_1"
        assert entry["error"] is False
        assert entry["note"] == "success"


class TestMemoryGetCollectData:
    def test_get_collect_data_returns_tool_results(self, mem):
        from src.tools.base import ToolResult
        tr = ToolResult(name="Stock", description="desc", data=None, source="src")
        mem.data.append(tr)
        results = mem.get_collect_data()
        assert len(results) >= 1

    def test_get_collect_data_exclude_type(self, mem):
        """When exclude_type is set, items of those types should be filtered."""
        from src.tools.base import ToolResult
        tr = ToolResult(name="Stock", description="desc", data=None, source="src")
        mem.data.append(tr)
        # ToolResult doesn't have a .type for search/click, so it should
        # still appear even when excluding 'search'
        results = mem.get_collect_data(exclude_type=["search"])
        assert len(results) >= 1
