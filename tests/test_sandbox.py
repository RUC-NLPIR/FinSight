"""Tests for code executor sandbox hardening.

Proves:
1. Restricted module imports (subprocess, shutil, ctypes) are blocked.
2. File writes outside working_dir are blocked.
3. Execution timeout is enforced.
4. Normal code execution still works.
"""

import asyncio
import os
import tempfile

import pytest

from src.utils.code_executor_async import AsyncCodeExecutor


@pytest.fixture
def executor(tmp_path):
    return AsyncCodeExecutor(working_dir=str(tmp_path))


class TestRestrictedImports:
    @pytest.mark.asyncio
    async def test_subprocess_blocked(self, executor):
        result = await executor.execute("import subprocess")
        assert result["error"] is True
        assert "not allowed" in result["stderr"]

    @pytest.mark.asyncio
    async def test_shutil_blocked(self, executor):
        result = await executor.execute("import shutil")
        assert result["error"] is True
        assert "not allowed" in result["stderr"]

    @pytest.mark.asyncio
    async def test_ctypes_blocked(self, executor):
        result = await executor.execute("import ctypes")
        assert result["error"] is True
        assert "not allowed" in result["stderr"]

    @pytest.mark.asyncio
    async def test_allowed_imports_work(self, executor):
        result = await executor.execute("import json; print(json.dumps({'a': 1}))")
        assert result["error"] is False
        assert '{"a": 1}' in result["stdout"]


class TestFilesystemRestriction:
    @pytest.mark.asyncio
    async def test_write_inside_working_dir_allowed(self, executor, tmp_path):
        code = f"""
with open("{tmp_path / 'test.txt'}", "w") as f:
    f.write("hello")
print("wrote OK")
"""
        result = await executor.execute(code)
        assert result["error"] is False
        assert (tmp_path / "test.txt").read_text() == "hello"

    @pytest.mark.asyncio
    async def test_write_outside_working_dir_blocked(self, executor):
        code = """
with open("/tmp/should_not_write.txt", "w") as f:
    f.write("bad")
"""
        result = await executor.execute(code)
        assert result["error"] is True
        assert "not allowed" in result["stderr"] or "PermissionError" in result["stderr"]

    @pytest.mark.asyncio
    async def test_read_anywhere_allowed(self, executor):
        """Reading files outside working_dir should still work."""
        # Read a file that definitely exists
        code = """
with open("/dev/null", "r") as f:
    content = f.read()
print("read OK")
"""
        result = await executor.execute(code)
        assert result["error"] is False


class TestExecutionTimeout:
    @pytest.mark.asyncio
    async def test_timeout_kills_execution(self, tmp_path):
        executor = AsyncCodeExecutor(working_dir=str(tmp_path), exec_timeout=1.0)
        code = """
import time
time.sleep(30)
"""
        result = await executor.execute(code)
        assert result["error"] is True
        assert "Timeout" in result["stderr"] or "timeout" in result["stderr"].lower()

    @pytest.mark.asyncio
    async def test_fast_code_within_timeout(self, executor):
        result = await executor.execute("print('fast')")
        assert result["error"] is False
        assert "fast" in result["stdout"]
