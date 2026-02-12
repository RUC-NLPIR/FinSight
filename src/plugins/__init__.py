"""Directory-based plugin loader for FinSight.

Scans one or more directories for Python files that contain ``Tool`` or
``BaseAgent`` subclasses, imports them, and registers the discovered classes
with the tool registry.

Usage::

    from src.plugins import load_plugins
    n_tools, n_agents = load_plugins(["~/.finsight/plugins", "./custom_plugins"])
"""

import importlib.util
import os
import sys
import warnings
from typing import List, Tuple

from src.tools.base import Tool


def load_plugins(plugin_dirs: List[str] | None = None) -> Tuple[int, int]:
    """Discover and register plugins from *plugin_dirs*.

    Parameters
    ----------
    plugin_dirs : list[str] | None
        Filesystem paths to scan.  Each directory is walked for ``.py`` files.
        ``~`` is expanded.  Non-existent directories are silently skipped.

    Returns
    -------
    tuple[int, int]
        ``(tools_loaded, agents_loaded)`` count of newly registered classes.
    """
    if not plugin_dirs:
        return (0, 0)

    # Lazy import — BaseAgent may not be importable in minimal envs.
    BaseAgent = None
    try:
        from src.agents.base_agent import BaseAgent as _BA
        BaseAgent = _BA
    except ImportError:
        pass

    from src.tools import register_tool

    tools_loaded = 0
    agents_loaded = 0

    for raw_dir in plugin_dirs:
        plugin_dir = os.path.expanduser(raw_dir)
        if not os.path.isdir(plugin_dir):
            continue

        for root, _dirs, files in os.walk(plugin_dir):
            for fname in sorted(files):
                if not fname.endswith(".py") or fname.startswith("_"):
                    continue
                fpath = os.path.join(root, fname)
                mod_name = f"finsight_plugin_{fname[:-3]}"

                try:
                    spec = importlib.util.spec_from_file_location(mod_name, fpath)
                    if spec is None or spec.loader is None:
                        continue
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[mod_name] = mod
                    spec.loader.exec_module(mod)
                except Exception as exc:
                    warnings.warn(f"Failed to load plugin {fpath}: {exc}")
                    continue

                # Scan module for Tool / BaseAgent subclasses
                for attr_name in dir(mod):
                    obj = getattr(mod, attr_name)
                    if not isinstance(obj, type):
                        continue

                    if issubclass(obj, Tool) and obj is not Tool:
                        # Guard: do not override core tools with plugins
                        try:
                            instance = obj()
                            from src.tools import get_tool_by_name
                            existing = get_tool_by_name(instance.name)
                            if existing is not None:
                                warnings.warn(
                                    f"Plugin tool '{instance.name}' from {fpath} "
                                    f"conflicts with existing core tool — skipping"
                                )
                                continue
                            register_tool(obj, category="plugin")
                            tools_loaded += 1
                        except Exception as exc:
                            warnings.warn(f"Failed to register plugin tool {attr_name}: {exc}")

                    elif BaseAgent is not None and issubclass(obj, BaseAgent) and obj is not BaseAgent:
                        # Agent plugins are tracked but registered differently
                        agents_loaded += 1

    return (tools_loaded, agents_loaded)
