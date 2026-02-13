"""Tests for BaseAgent._parse_llm_response and _format_execution_result.

These methods are static-like (depend only on input string), so we can test
them by instantiating a minimal mock that has these methods without needing
a full Config/Memory/LLM stack.

We import the methods directly from the source file via importlib to avoid
triggering heavy dependency chains.
"""

import importlib.util
import os
import sys

import pytest

# Load base_agent module directly to avoid full src.agents init
_AGENT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "agents", "base_agent.py"
)
_spec = importlib.util.spec_from_file_location("_base_agent_direct", _AGENT_PATH)
_mod = importlib.util.module_from_spec(_spec)

# We need src.tools and src.utils available; they should already be importable
# from pytest's PYTHONPATH. But base_agent.py imports them at module level,
# so we just let the normal import chain work.
sys.modules["_base_agent_direct"] = _mod
_spec.loader.exec_module(_mod)

BaseAgent = _mod.BaseAgent


class _FakeAgent:
    """Minimal wrapper to call BaseAgent's static-ish methods without init."""

    _parse_llm_response = BaseAgent._parse_llm_response
    _format_execution_result = BaseAgent._format_execution_result


@pytest.fixture
def agent():
    return _FakeAgent()


# ---------------------------------------------------------------------------
# _parse_llm_response
# ---------------------------------------------------------------------------

class TestParseLlmResponse:
    def test_simple_execute_tag(self, agent):
        response = "Let me run some code.\n<execute>print('hello')</execute>"
        action, content = agent._parse_llm_response(response)
        assert action == "code"
        assert "print('hello')" in content

    def test_final_result_tag(self, agent):
        response = "<final_result>The answer is 42.</final_result>"
        action, content = agent._parse_llm_response(response)
        assert action == "final"
        assert "42" in content

    def test_no_tags_returns_final(self, agent):
        response = "I don't know what to do."
        action, content = agent._parse_llm_response(response)
        assert action == "final"
        assert content == response

    def test_thinking_tags_stripped(self, agent):
        response = "<thinking>Let me think...</thinking>\n<execute>x = 1</execute>"
        action, content = agent._parse_llm_response(response)
        assert action == "code"
        assert "x = 1" in content

    def test_think_tags_stripped(self, agent):
        response = "<think>reasoning</think>\n<final_result>done</final_result>"
        action, content = agent._parse_llm_response(response)
        assert action == "final"
        assert "done" in content

    def test_multiple_tags_last_wins(self, agent):
        response = "<execute>first</execute>\n<final_result>second</final_result>"
        action, content = agent._parse_llm_response(response)
        assert action == "final"
        assert "second" in content

    def test_custom_tag(self, agent):
        response = "<search>query text</search>"
        action, content = agent._parse_llm_response(response)
        assert action == "search"
        assert content == "query text"

    def test_multiline_content(self, agent):
        response = "<execute>\nline1\nline2\nline3\n</execute>"
        action, content = agent._parse_llm_response(response)
        assert action == "code"
        assert "line1" in content
        assert "line3" in content

    def test_whitespace_stripped(self, agent):
        response = "<final_result>  result with spaces  </final_result>"
        action, content = agent._parse_llm_response(response)
        assert content == "result with spaces"


# ---------------------------------------------------------------------------
# _format_execution_result
# ---------------------------------------------------------------------------

class TestFormatExecutionResult:
    def test_success_with_output(self, agent):
        result = {"error": False, "stdout": "Hello World\n", "stderr": ""}
        formatted = agent._format_execution_result(result)
        assert "success" in formatted.lower()
        assert "Hello World" in formatted

    def test_success_no_output(self, agent):
        result = {"error": False, "stdout": "", "stderr": ""}
        formatted = agent._format_execution_result(result)
        assert "success" in formatted.lower()

    def test_failure_with_error(self, agent):
        result = {"error": True, "stdout": "", "stderr": "NameError: x is not defined\n"}
        formatted = agent._format_execution_result(result)
        assert "failed" in formatted.lower()
        assert "NameError" in formatted

    def test_failure_with_partial_output(self, agent):
        result = {"error": True, "stdout": "partial", "stderr": "Error\n"}
        formatted = agent._format_execution_result(result)
        assert "failed" in formatted.lower()
        assert "partial" in formatted.lower() or "Partial" in formatted

    def test_variables_displayed(self, agent):
        result = {
            "error": False,
            "stdout": "ok\n",
            "stderr": "",
            "variables": {"x": "int: 42"},
        }
        formatted = agent._format_execution_result(result)
        assert "x" in formatted
        assert "42" in formatted

    def test_additional_notes(self, agent):
        result = {
            "error": False,
            "stdout": "",
            "stderr": "",
            "additional_notes": "Chart saved to /tmp/chart.png",
        }
        formatted = agent._format_execution_result(result)
        assert "chart" in formatted.lower() or "Chart" in formatted
