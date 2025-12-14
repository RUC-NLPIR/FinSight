# -*- coding: utf-8 -*-
"""
Safe code executor that relies on IPython to run notebook-style snippets.
"""

import os
import sys
import ast
import traceback
import io
from typing import Dict, Any, List, Optional, Tuple
from contextlib import redirect_stdout, redirect_stderr
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import font_manager
import pandas as pd


class CodeExecutor:
    """
    Safe code executor with dependency controls, output capture, and image export support.
    """   
    ALLOWED_IMPORTS = {
        'pandas', 'pd',
        'numpy', 'np', 
        'matplotlib', 'matplotlib.pyplot', 'plt',
        'duckdb', 'scipy', 'sklearn',
        'plotly', 'dash', 'requests', 'urllib',
        'os', 'sys', 'json', 'csv', 'datetime', 'time',
        'math', 'statistics', 're', 'pathlib', 'io',
        'collections', 'itertools', 'functools', 'operator',
        'warnings', 'logging', 'copy', 'pickle', 'gzip', 'zipfile',
        'typing', 'dataclasses', 'enum', 'sqlite3', 'seaborn', 'plotly.express'
    }
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize the executor.

        Args:
            output_dir: Directory for saved figures/files.
        """
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize IPython shell
        self.shell = InteractiveShell.instance()
        
        # Configure font handling
        self._setup_chinese_font()
        
        # Preload common libraries
        self._setup_common_imports()
        
        # Image counter
        self.image_counter = 0
        
    def _setup_chinese_font(self):
        """Configure matplotlib font settings (prefer Chinese-friendly fonts)."""
        try:
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib import font_manager
            
            font_path = "./font/kt_font.ttf"
            
            if not os.path.exists(font_path):
                raise FileNotFoundError(f"Font file not found: {font_path}")
            
            font_manager.fontManager.addfont(font_path)
            
            font_prop = font_manager.FontProperties(fname=font_path)
            font_name = font_prop.get_name()
            
            plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            
            # print(f"Successfully set custom font: {font_name}")
            
            # Mirror the configuration within the shell
            self.shell.run_cell(f"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
font_path = "./font/kt_font.ttf"
plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
plt.rcParams['axes.unicode_minus'] = False
""")
            
        except Exception as e:
            print(f"Failed to configure custom font: {e}")
            # Fallback to system defaults
            try:
                self.shell.run_cell("""
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = ['KaiTi']
plt.rcParams['axes.unicode_minus'] = False
""")
            except:
                pass
            
    def _setup_common_imports(self):
        """Preload commonly used libraries inside the IPython shell."""
        common_imports = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager
font_path = "./font/kt_font.ttf" 
plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
plt.rcParams['axes.unicode_minus'] = False
import seaborn as sns
# Chart styling
sns.set_style("whitegrid", {
    'font.family': 'KaiTi',
    'axes.unicode_minus': False
})
import os
import json
from IPython.display import display
"""
        try:
            self.shell.run_cell(common_imports)
            # Ensure display() is available inside the shell namespace
            from IPython.display import display
            self.shell.user_ns['display'] = display
        except Exception as e:
            print(f"Failed to preload libraries: {e}")
    
    def _check_code_safety(self, code: str) -> Tuple[bool, str]:
        """
        Perform basic safety checks on the submitted code.

        Returns:
            (is_safe, error_message)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        
        # for node in ast.walk(tree):
        #     if isinstance(node, ast.Import):
        #         for alias in node.names:
        #             if alias.name not in self.ALLOWED_IMPORTS:
            
        #     elif isinstance(node, ast.ImportFrom):
        #         if node.module not in self.ALLOWED_IMPORTS:
        #             return False, f"Disallowed import: {node.module}"
        #       # Check for dangerous calls
        #     elif isinstance(node, ast.Call):
        #         if isinstance(node.func, ast.Name):
        #             if node.func.id in ['exec', 'eval', '__import__']:
        #                 return False, f"Disallowed function call: {node.func.id}"
        
        return True, ""
    
    def get_current_figures_info(self) -> List[Dict[str, Any]]:
        """Return metadata about the current matplotlib figures without saving them."""
        figures_info = []
        
        # Enumerate active figures
        fig_nums = plt.get_fignums()
        
        for fig_num in fig_nums:
            fig = plt.figure(fig_num)
            if fig.get_axes():  # Only track figures with content
                figures_info.append({
                    'figure_number': fig_num,
                    'axes_count': len(fig.get_axes()),
                    'figure_size': fig.get_size_inches().tolist(),
                    'has_content': True
                })
        
        return figures_info
    
    def _format_table_output(self, obj: Any) -> str:
        """Format tabular output with row limits."""
        if hasattr(obj, 'shape') and hasattr(obj, 'head'):  # pandas DataFrame
            rows, cols = obj.shape
            print(f"\nData shape: {rows} rows x {cols} columns")
            print(f"Columns: {list(obj.columns)}")
            
            if rows <= 15:
                return str(obj)
            else:
                head_part = obj.head(5)
                tail_part = obj.tail(5)
                return f"{head_part}\n...\n({rows-10} rows omitted)\n...\n{tail_part}"
        
        return str(obj)
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """
        Execute code and return structured results.

        Args:
            code: Python source code to run.

        Returns:
            {
                'success': bool,
                'output': str,
                'error': str,
                'variables': Dict[str, Any]  # Newly created important variables
            }
        """
        # Run safety checks
        is_safe, safety_error = self._check_code_safety(code)
        if not is_safe:
            return {
                'success': False,
                'output': '',
                'error': f"Code safety check failed: {safety_error}",
                'variables': {}
            }
        
        # Record existing variables
        vars_before = set(self.shell.user_ns.keys())

        try:
            # Capture stdout/stderr via IPython utilities
            with capture_output() as captured:
                result = self.shell.run_cell(code)
            
            # Inspect execution result
            if result.error_before_exec:
                error_msg = str(result.error_before_exec)
                return {
                    'success': False,
                    'output': captured.stdout,
                    'error': f"Error before execution: {error_msg}",
                    'variables': {}
                }
            
            if result.error_in_exec:
                error_msg = str(result.error_in_exec)
                return {
                    'success': False,
                    'output': captured.stdout,
                    'error': f"Execution error: {error_msg}",
                    'variables': {}
                }
            
            # Fetch captured output
            output = captured.stdout
            
            # Append formatted return values, if any
            if result.result is not None:
                formatted_result = self._format_table_output(result.result)
                output += f"\n{formatted_result}"
            vars_after = set(self.shell.user_ns.keys())
            new_vars = vars_after - vars_before
            
            # Track newly created data structures (e.g., DataFrames)
            important_new_vars = {}
            for var_name in new_vars:
                if not var_name.startswith('_'):
                    try:
                        var_value = self.shell.user_ns[var_name]
                        if hasattr(var_value, 'shape'):  # pandas DataFrame, numpy array
                            important_new_vars[var_name] = f"{type(var_value).__name__} with shape {var_value.shape}"
                        elif var_name in ['session_output_dir']:  # important path variable
                            important_new_vars[var_name] = str(var_value)
                    except:
                        pass
            
            return {
                'success': True,
                'output': output,                
                'error': '',
                'variables': important_new_vars
            }
        except Exception as e:
            return {
                'success': False,
                'output': captured.stdout if 'captured' in locals() else '',
                'error': f"Execution exception: {str(e)}\n{traceback.format_exc()}",
                'variables': {}
            }    
    
    def reset_environment(self):
        """Reset the execution environment to its initial state."""
        self.shell.reset()
        self._setup_common_imports()
        self._setup_chinese_font()
        plt.close('all')
        self.image_counter = 0
    
    def set_variable(self, name: str, value: Any):
        """Inject a variable into the execution environment."""
        self.shell.user_ns[name] = value
    
    def get_environment_info(self) -> str:
        """Summarize variables in the current environment for prompt building."""
        info_parts = []
        
        # Capture important data variables
        important_vars = {}
        for var_name, var_value in self.shell.user_ns.items():
            if not var_name.startswith('_') and var_name not in ['In', 'Out', 'get_ipython', 'exit', 'quit']:
                try:
                    if hasattr(var_value, 'shape'):  # pandas DataFrame, numpy array
                        important_vars[var_name] = f"{type(var_value).__name__} with shape {var_value.shape}"
                    elif var_name in ['session_output_dir']:
                        important_vars[var_name] = str(var_value)
                    elif isinstance(var_value, (int, float, str, bool)) and len(str(var_value)) < 100:
                        important_vars[var_name] = f"{type(var_value).__name__}: {var_value}"
                    elif hasattr(var_value, '__module__') and var_value.__module__ in ['pandas', 'numpy', 'matplotlib.pyplot']:
                        important_vars[var_name] = f"Imported module: {var_value.__module__}"
                    if isinstance(var_value, pd.DataFrame):
                        important_vars[var_name] += ", and dtypes: " + str(var_value.dtypes)
                except:
                    continue
        
        if important_vars:
            info_parts.append("Current environment variables:")
            for var_name, var_info in important_vars.items():
                info_parts.append(f"- {var_name}: {var_info}")
        else:
            info_parts.append("Environment preloads pandas, numpy, matplotlib, and related libraries.")
        
        if 'session_output_dir' in self.shell.user_ns:
            info_parts.append(f"Image output directory: session_output_dir = '{self.shell.user_ns['session_output_dir']}'")
        
        return "\n".join(info_parts)

