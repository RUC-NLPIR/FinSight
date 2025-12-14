# FinSight Advanced Usage Guide

This comprehensive guide covers advanced configuration, customization, and extension of FinSight. It's organized into the following sections:

## 📑 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Configuration Deep Dive](#configuration-deep-dive)
  - [API Keys & Model Configuration](#api-keys--model-configuration)
  - [Config File Structure](#config-file-structure)
  - [Environment Variable Resolution](#environment-variable-resolution)
- [Prompt System](#prompt-system)
  - [Prompt Loader Architecture](#prompt-loader-architecture)
  - [Customizing Prompts](#customizing-prompts)
  - [Agent-Specific Prompts](#agent-specific-prompts)
- [Report Templates & Outlines](#report-templates--outlines)
  - [Custom Outline Templates](#custom-outline-templates)
  - [Reference Document Styling](#reference-document-styling)
- [Visual Styling](#visual-styling)
  - [Chart Color Palettes](#chart-color-palettes)
  - [VLM Critique Loop](#vlm-critique-loop)
- [Extending FinSight](#extending-finsight)
  - [Adding Custom Tools](#adding-custom-tools)
  - [Adding Custom Agents](#adding-custom-agents)
  - [Tool Auto-Registration System](#tool-auto-registration-system)
- [Memory System](#memory-system)
  - [Checkpoint & Resume](#checkpoint--resume)
  - [Data Flow Architecture](#data-flow-architecture)
- [Complete Examples](#complete-examples)

---

## Architecture Overview

FinSight is a multi-agent system built around the **Code Agent with Variable Memory (CAVM)** architecture. The core principle is that all agents operate in a **unified variable space**, executing Python code to manipulate data, tools, and memory dynamically.

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Config System                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   .env      │  │ my_config   │  │   default_config.yaml   │  │
│  │ (API Keys)  │  │   .yaml     │  │   (Defaults)            │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         └────────────────┼─────────────────────┘                 │
│                          ▼                                       │
│                   Config Object                                  │
│              (llm_dict, working_dir)                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                        Memory System                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Data Store   │  │ Task Mapping │  │ Agent Checkpoints    │   │
│  │ (ToolResult) │  │ (Scheduling) │  │ (Resume Support)     │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                        Agent Pipeline                            │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │    Data     │───▶│    Data     │───▶│      Report         │  │
│  │  Collector  │    │  Analyzer   │    │     Generator       │  │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘  │
│         │                  │                      │              │
│         ▼                  ▼                      ▼              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ DeepSearch  │    │ VLM Chart   │    │   Pandoc + PDF      │  │
│  │   Agent     │    │   Critique  │    │     Rendering       │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Execution Flow

Each agent follows a unified execution loop:

1. **`_prepare_executor`**: Set up code sandbox with helper functions and variables
2. **`_prepare_init_prompt`**: Build the initial prompt with context
3. **LLM Generation**: Get response with action tags (`<execute>`, `<report>`, `<search>`, etc.)
4. **`_parse_llm_response`**: Extract action type and content
5. **`_execute_action`**: Dispatch to appropriate handler (`_handle_code_action`, `_handle_final_action`, etc.)
6. **Checkpoint**: Save state for resume capability

---

## Configuration Deep Dive

### API Keys & Model Configuration

FinSight uses a **two-layer configuration** system:

#### Layer 1: `.env` File (Secrets)

Create a `.env` file in the project root with your API credentials:

```bash
# ===== LLM (Main Reasoning Model) =====
DS_MODEL_NAME="deepseek-chat"
DS_API_KEY="sk-your-deepseek-key"
DS_BASE_URL="https://api.deepseek.com/v1"

# ===== VLM (Vision-Language Model for Chart Critique) =====
VLM_MODEL_NAME="qwen-vl-max"
VLM_API_KEY="sk-your-vlm-key"
VLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# ===== Embedding Model (Semantic Search) =====
EMBEDDING_MODEL_NAME="text-embedding-v3"
EMBEDDING_API_KEY="sk-your-embedding-key"
EMBEDDING_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# ===== Web Search APIs (Optional) =====
SERPER_API_KEY="your-serper-key"      # Google Search via Serper
BOCHAAI_API_KEY="your-bocha-key"      # Bocha Search (Chinese-focused)
```

**Using Aggregator Endpoints (OpenRouter/AIHubMix)**:

```bash
# Example: Using OpenRouter for multiple models
DS_MODEL_NAME="openai/gpt-4o"
DS_API_KEY="sk-or-xxx"
DS_BASE_URL="https://openrouter.ai/api/v1"

VLM_MODEL_NAME="anthropic/claude-3-5-sonnet"
VLM_API_KEY="sk-or-xxx"
VLM_BASE_URL="https://openrouter.ai/api/v1"
```

#### Model Selection Guide

| Model Type | Purpose | Recommended Options |
|------------|---------|---------------------|
| **LLM** | Main reasoning, code generation, analysis | DeepSeek-Chat, GPT-4o, Claude-3.5 |
| **VLM** | Chart analysis, visual feedback | Qwen-VL-Max, GPT-4V, Claude-3.5 |
| **Embedding** | Semantic search, data retrieval | text-embedding-v3, OpenAI ada-002 |

#### Config Loading Process

The `Config` class (`src/config/config.py`) handles configuration loading:

```python
class Config:
    def __init__(self, config_file_path=None, config_dict={}):
        # 1. Load default config
        self.config = self._load_config("default_config.yaml")
        
        # 2. Overlay user config file
        if config_file_path:
            self.config.update(self._load_config(config_file_path))
        
        # 3. Overlay runtime dict (highest priority)
        self.config.update(config_dict)
        
        # 4. Set up directories and LLM instances
        self._set_dirs()
        self._set_llms()
```

### Config File Structure

Create `my_config.yaml` with the following structure:

```yaml
# ===== Target Configuration =====
target_name: "Your Company Name"           # Research target name
stock_code: "000001"                        # Stock ticker (A-share or HK format)
target_type: 'financial_company'            # Options: financial_company, macro, industry, general
output_dir: "./outputs/my-research"         # Output directory
language: 'en'                              # Output language: zh (Chinese) or en (English)

# ===== Template Paths =====
reference_doc_path: 'src/template/report_template.docx'   # Word template for styling
outline_template_path: 'src/template/company_outline.md'  # Report structure template

# ===== Custom Tasks (Optional - if not provided, LLM generates them) =====
custom_collect_tasks:
  - "Balance sheet, income statement, cash flow statement"
  - "Stock price data and trading volume"
  - "Shareholding structure and major shareholders"
  - "Analyst ratings and price targets"

custom_analysis_tasks:
  - "Analyze company development history and milestones"
  - "Evaluate revenue trends and growth drivers"
  - "Assess profitability metrics (ROE, gross margin, net margin)"
  - "Compare with industry peers on key metrics"

# ===== Cache Settings (for checkpoint/resume) =====
use_collect_data_cache: True
use_analysis_cache: True
use_report_outline_cache: True
use_full_report_cache: True
use_post_process_cache: True

# ===== LLM Configuration (references .env variables) =====
llm_config_list:
  - model_name: "${DS_MODEL_NAME}"
    api_key: "${DS_API_KEY}"
    base_url: "${DS_BASE_URL}"
    generation_params:
      temperature: 0.7
      max_tokens: 32768
      top_p: 0.95
      
  - model_name: "${EMBEDDING_MODEL_NAME}"
    api_key: "${EMBEDDING_API_KEY}"
    base_url: "${EMBEDDING_BASE_URL}"
    
  - model_name: "${VLM_MODEL_NAME}"
    api_key: "${VLM_API_KEY}"
    base_url: "${VLM_BASE_URL}"
```

### Environment Variable Resolution

The config system automatically resolves `${VAR_NAME}` patterns:

```python
# In config.py
def replace_env_vars(obj):
    """Recursively replace ${VAR_NAME} with environment variables"""
    if isinstance(obj, str):
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, obj)
        for var_name in matches:
            env_value = os.getenv(var_name)
            if env_value is None:
                raise ValueError(f"Environment variable '{var_name}' is not set")
            result = result.replace(f"${{{var_name}}}", env_value)
        return result
```

**Usage Examples**:

```python
from src.config import Config

# Basic usage
config = Config(config_file_path='my_config.yaml')

# Override at runtime
config = Config(
    config_file_path='my_config.yaml',
    config_dict={
        'output_dir': './outputs/custom-run',
        'language': 'en',
        'target_name': 'Apple Inc.',
        'stock_code': 'AAPL'
    }
)

# Access LLM instances
llm = config.llm_dict['deepseek-chat']
response = await llm.generate(messages=[{"role": "user", "content": "Hello"}])
```

---

## Prompt System

### Prompt Loader Architecture

FinSight uses a **YAML-based prompt system** that supports different report types and easy customization.

#### Directory Structure

```
src/
├── agents/
│   ├── data_analyzer/
│   │   └── prompts/
│   │       ├── general_prompts.yaml     # For general research
│   │       └── financial_prompts.yaml   # For financial reports
│   ├── data_collector/
│   │   └── prompts/
│   │       └── prompts.yaml
│   ├── report_generator/
│   │   └── prompts/
│   │       ├── general_prompts.yaml
│   │       ├── financial_company_prompts.yaml
│   │       ├── financial_macro_prompts.yaml
│   │       └── financial_industry_prompts.yaml
│   └── search_agent/
│       └── prompts/
│           └── general_prompts.yaml
└── memory/
    └── prompts/
        ├── general_prompts.yaml
        └── financial_prompts.yaml
```

#### PromptLoader Class

```python
from src.utils.prompt_loader import get_prompt_loader, PromptLoader

# Get loader for a specific agent and report type
loader = get_prompt_loader('data_analyzer', report_type='financial')

# Access specific prompts
analysis_prompt = loader.get_prompt('data_analysis')
api_prompt = loader.get_prompt('data_api')

# Format prompts with variables
formatted = loader.get_prompt('data_analysis',
    current_time="2024-12-01",
    user_query="Analyze revenue trends",
    data_info="Available datasets...",
    target_language="English"
)

# List all available prompts
print(loader.list_available_prompts())
# ['data_analysis', 'data_analysis_wo_chart', 'data_api', 'report_draft', ...]
```

### Customizing Prompts

#### Creating Custom Prompt Files

1. **Create a new YAML file** in the appropriate prompts directory:

```yaml
# src/agents/data_analyzer/prompts/my_custom_prompts.yaml

data_analysis: |
  You are a specialized analyst for {industry_name}.
  
  ## Context
  Current time: {current_time}
  Available data: {data_info}
  
  ## Task
  {user_query}
  
  ## Instructions
  1. Use <execute> tags for Python code
  2. Use <report> tags for final output
  
  ## Output Language
  All output must be in {target_language}.

data_api: |
  ### Available Functions
  
  **get_existed_data(data_id)**
  Fetch dataset by ID (0-indexed).
  
  **get_data_from_deep_search(query)**
  Search the web for additional information.
```

2. **Load your custom prompts**:

```python
# Option 1: Set target_type to match your file name
config = Config(config_dict={'target_type': 'my_custom'})

# Option 2: Directly load the prompt file
loader = PromptLoader(
    prompts_dir='src/agents/data_analyzer/prompts',
    report_type='my_custom'
)
```

### Agent-Specific Prompts

#### Data Analyzer Prompts

Key prompts in `src/agents/data_analyzer/prompts/`:

| Prompt Key | Purpose |
|------------|---------|
| `data_analysis` | Main analysis prompt with chart generation |
| `data_analysis_wo_chart` | Analysis prompt without chart placeholders |
| `data_api` | API documentation for available functions |
| `report_draft` | Final report synthesis |
| `draw_chart` | Chart generation instructions |
| `vlm_critique` | VLM feedback for chart quality |

#### Report Generator Prompts

Key prompts in `src/agents/report_generator/prompts/`:

| Prompt Key | Purpose |
|------------|---------|
| `outline_draft` | Generate report outline |
| `outline_critique` | Review outline quality |
| `outline_refinement` | Refine outline based on feedback |
| `section_writing` | Write individual sections |
| `final_polish` | Polish section content |
| `title_generation` | Generate report title |
| `abstract` | Generate executive summary |
| `table_beautify` | Format tables for display |

---

## Report Templates & Outlines

### Custom Outline Templates

FinSight supports custom outline templates to control report structure.

#### Template Location

Set in `my_config.yaml`:

```yaml
outline_template_path: 'src/template/company_outline.md'
```

#### Template Format

```markdown
# Company Fundamentals (Foundation)
Purpose: Build a 360° view of the company.
- Corporate history: timeline of milestones, strategic pivots
- Leadership: background of founders and key executives

Financing & ownership:
- Financing history: key rounds and investor confidence
- Shareholding structure: ownership mix, control patterns

# External Context & Business Model
Purpose: Position the company within its market.
- Industry analysis: TAM, CAGR, and 3-year outlook
- Business deep dive: product portfolio, monetization, moat

# Financial Deep Dive
Use structured flow: **data → trend → drivers → forward view**.
- Revenue analysis: scale, mix, cohort dynamics
- Net profit: sustainability of earnings
- Gross margin: pricing power analysis
- Cash flow: operating vs. investing vs. financing patterns

# Outlook & Valuation
- Forecasts: project core metrics
- Valuation: PS, PE, PB, DCF analysis
- Investment call: Buy/Hold/Sell recommendation

# Key Risks
Data-backed risk disclosures:
- Macro/market shocks
- Industry/competitive risks
- Company-specific issues
```

#### Creating Custom Templates

**For Financial Reports**:

```markdown
# Executive Summary
One-page overview with key metrics and investment thesis.

# Company Overview
- Business description and history
- Management and governance
- Shareholder structure

# Industry Analysis
- Market size and growth
- Competitive landscape
- Regulatory environment

# Financial Analysis
- Revenue and profitability trends
- Balance sheet analysis
- Cash flow analysis
- Key financial ratios

# Valuation
- Comparable company analysis
- DCF valuation
- Target price and recommendation

# Risks and Mitigants
- Key risks
- Mitigation strategies
```

**For General Research**:

```markdown
# Introduction
Background and research objectives.

# Literature Review
Existing research and theoretical framework.

# Methodology
Data sources and analytical approach.

# Findings
- Finding 1: [Topic]
- Finding 2: [Topic]
- Finding 3: [Topic]

# Discussion
Implications and interpretations.

# Conclusion
Summary and recommendations.

# References
```

### Reference Document Styling

The reference document controls Word output styling.

#### Configuration

```yaml
reference_doc_path: 'src/template/report_template.docx'
```

#### Creating Custom Reference Documents

1. **Start with the default template**: Copy `src/template/report_template.docx`

2. **Modify styles in Word**:
   - Heading 1, 2, 3 styles for section hierarchy
   - Normal style for body text
   - Table styles
   - Header/footer content
   - Page margins and orientation

3. **Key style elements to customize**:
   - **Fonts**: Choose professional fonts (e.g., Times New Roman, Arial)
   - **Colors**: Match corporate branding
   - **Spacing**: Adjust line and paragraph spacing
   - **ToC format**: Configure table of contents appearance

4. **Update config**:

```yaml
reference_doc_path: 'path/to/your/custom_template.docx'
```

#### Pandoc Integration

The report generator uses Pandoc for conversion:

```python
pandoc_cmd = [
    "pandoc",
    md_path,
    "-o", docx_path,
    "--standalone",
    "--toc",
    "--toc-depth=3",
    f"--resource-path={working_dir}",
    f"--reference-doc={reference_doc}"
]
```

---

## Visual Styling

### Chart Color Palettes

FinSight uses a custom color palette for consistent, professional charts.

#### Default Palette

```python
# In src/agents/data_analyzer/data_analyzer.py
custom_palette = [
    "#8B0000",  # deep crimson
    "#FF2A2A",  # bright red
    "#FF6A4D",  # orange-red
    "#FFDAB9",  # pale peach
    "#FFF5E6",  # cream
    "#FFE4B5",  # beige
    "#A0522D",  # sienna
    "#5C2E1F",  # dark brown
]
```

#### Customizing the Palette

**Option 1: Modify at Agent Initialization**

```python
class MyDataAnalyzer(DataAnalyzer):
    async def _prepare_executor(self):
        await super()._prepare_executor()
        
        # Override with custom palette
        my_palette = [
            "#1f77b4",  # blue
            "#ff7f0e",  # orange
            "#2ca02c",  # green
            "#d62728",  # red
            "#9467bd",  # purple
            "#8c564b",  # brown
            "#e377c2",  # pink
            "#7f7f7f",  # gray
        ]
        self.code_executor.set_variable("custom_palette", my_palette)
```

**Option 2: Modify the Prompt**

In `draw_chart` prompt, customize the seaborn setup:

```yaml
draw_chart: |
  # ... existing content ...
  
  Before drawing, apply this style:
  ```python
  import seaborn as sns
  
  # Corporate blue theme
  corporate_palette = [
      "#003366",  # navy
      "#0066CC",  # corporate blue
      "#66B2FF",  # light blue
      "#CCE5FF",  # pale blue
      "#E6F2FF",  # very light blue
  ]
  
  sns.set_style({
      'font.family': 'Arial',
      'axes.unicode_minus': False
  })
  sns.set_palette(corporate_palette)
  ```
```

#### Chart Styling Guidelines (from VLM Critique)

The VLM critique evaluates charts on:

1. **Communication & Insight**: Does the chart answer the analytical question?
2. **Clarity & Accuracy**: Labels, legends, titles present and readable
3. **Aesthetics & Design**: Color harmony, balanced layout

### VLM Critique Loop

The chart generation includes an iterative refinement loop:

```
┌─────────────────┐
│ LLM generates   │
│ chart code      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Execute code    │
│ Save PNG        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ VLM evaluates   │
│ chart quality   │
└────────┬────────┘
         │
    ┌────┴────┐
    │ FINISH? │
    └────┬────┘
    No   │   Yes
    │    │    │
    ▼    │    ▼
┌────────┴────────┐
│ Refine code     │    Done
│ based on        │
│ VLM feedback    │
└─────────────────┘
```

**Customizing the Critique Loop**:

```python
# In data_analyzer.py, _draw_single_chart method
async def _draw_single_chart(
    self, 
    task: str,
    report_content: str,
    chart_name: str, 
    current_variables: str,
    max_iterations: int = 3  # Increase for more refinement
) -> str:
```

---

## Extending FinSight

### Adding Custom Tools

Tools are the data acquisition layer for FinSight agents.

#### Tool Base Class

```python
from src.tools.base import Tool, ToolResult

class MyCustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="My Custom Tool",
            description="Description of what this tool does",
            parameters=[
                {
                    "name": "param1", 
                    "type": "str", 
                    "description": "First parameter", 
                    "required": True
                },
                {
                    "name": "param2", 
                    "type": "int", 
                    "description": "Optional parameter", 
                    "required": False
                },
            ]
        )
    
    async def api_function(self, param1: str, param2: int = 10):
        """
        Execute the tool and return structured results.
        
        Returns:
            List[ToolResult]: List of results
        """
        # Your data fetching logic here
        result_data = await self._fetch_data(param1, param2)
        
        return [
            ToolResult(
                name=f"Result for {param1}",
                description="Description of this result",
                data=result_data,  # Can be DataFrame, dict, list, etc.
                source="Data source URL or description"
            )
        ]
    
    async def _fetch_data(self, param1, param2):
        # Implementation
        pass
```

#### Real-World Example: Stock Data Tool

```python
# src/tools/financial/my_stock_tool.py

import pandas as pd
from ..base import Tool, ToolResult

class MyStockAnalysisTool(Tool):
    def __init__(self):
        super().__init__(
            name="Stock technical analysis",
            description="Compute technical indicators (SMA, RSI, MACD) for a stock",
            parameters=[
                {"name": "stock_code", "type": "str", "description": "Stock ticker", "required": True},
                {"name": "period", "type": "int", "description": "Analysis period in days", "required": False},
            ],
        )

    async def api_function(self, stock_code: str, period: int = 30):
        import efinance as ef
        
        try:
            # Fetch price data
            df = ef.stock.get_quote_history(stock_code)
            df = df.tail(period)
            
            # Calculate technical indicators
            df['SMA_20'] = df['收盘'].rolling(window=20).mean()
            df['SMA_50'] = df['收盘'].rolling(window=50).mean()
            
            # RSI calculation
            delta = df['收盘'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            return [
                ToolResult(
                    name=f"Technical analysis for {stock_code}",
                    description=f"SMA, RSI indicators for past {period} days",
                    data=df,
                    source="Calculated from exchange trading data"
                )
            ]
        except Exception as e:
            return [
                ToolResult(
                    name=f"Error: {stock_code}",
                    description=f"Failed to fetch data: {str(e)}",
                    data=None,
                    source=""
                )
            ]
```

### Tool Auto-Registration System

Tools are automatically registered when placed in the correct directory.

#### Registration Mechanism

```python
# src/tools/__init__.py

def _auto_register_tools():
    """Automatically discover and register tools from submodules."""
    for importer, modname, ispkg in pkgutil.walk_packages([current_dir]):
        module = importlib.import_module(modname)
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Tool) and obj != Tool:
                # Determine category from path
                category = modname.split('.')[0]  # e.g., 'financial'
                register_tool(obj, category)
```

#### Adding Your Tool

1. **Place your tool file** in the appropriate category folder:
   ```
   src/tools/
   ├── financial/
   │   └── my_stock_tool.py  # Your new tool
   ├── macro/
   ├── industry/
   └── web/
   ```

2. **Tool is auto-registered** on import

3. **Verify registration**:
   ```python
   from src.tools import list_tools, get_tool_by_name
   
   print(list_tools())
   # [..., 'Stock technical analysis', ...]
   
   tool = get_tool_by_name('Stock technical analysis')()
   result = await tool.api_function(stock_code='000001')
   ```

### Adding Custom Agents

#### Agent Base Class

```python
from src.agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    AGENT_NAME = 'my_custom_agent'
    AGENT_DESCRIPTION = 'Description for use as a tool by other agents'
    NECESSARY_KEYS = ['task', 'custom_param']  # Required input keys
    
    def __init__(
        self,
        config,
        tools=None,
        use_llm_name: str = "deepseek-chat",
        enable_code=True,
        memory=None,
        agent_id: str = None
    ):
        # Load custom tools if none provided
        if tools is None:
            tools = self._get_default_tools()
        
        super().__init__(
            config=config,
            tools=tools,
            use_llm_name=use_llm_name,
            enable_code=enable_code,
            memory=memory,
            agent_id=agent_id
        )
        
        # Load prompts
        from src.utils.prompt_loader import get_prompt_loader
        self.prompt_loader = get_prompt_loader('my_custom_agent', report_type='general')
    
    def _get_default_tools(self):
        """Define default tools for this agent."""
        from src.agents import DeepSearchAgent
        return [DeepSearchAgent(config=self.config, memory=self.memory)]
    
    async def _prepare_executor(self):
        """Set up code executor with helper functions."""
        # Expose helper functions to the code sandbox
        self.code_executor.set_variable("call_tool", self._agent_tool_function)
        self.code_executor.set_variable("custom_helper", self._custom_helper)
    
    def _custom_helper(self, data):
        """Custom helper function available in code execution."""
        return process_data(data)
    
    async def _prepare_init_prompt(self, input_data: dict) -> list[dict]:
        """Build the initial conversation prompt."""
        task = input_data.get('task')
        custom_param = input_data.get('custom_param')
        
        prompt = self.prompt_loader.get_prompt('main_prompt',
            task=task,
            custom_param=custom_param,
            current_time=self.current_time
        )
        
        return [{"role": "user", "content": prompt}]
    
    # Custom action handlers
    async def _handle_analyze_action(self, action_content: str):
        """Handle <analyze> action tag."""
        result = await self._perform_analysis(action_content)
        return {
            "action": "analyze",
            "action_content": action_content,
            "result": result,
            "continue": True,  # Continue the loop
        }
    
    async def _handle_final_action(self, action_content: str):
        """Handle <final> action tag - end the loop."""
        return {
            "action": "final",
            "action_content": action_content,
            "result": action_content,
            "continue": False,  # Stop the loop
        }
```

#### Using Agents as Tools

Agents can be used as tools by other agents:

```python
# In parent agent
class ParentAgent(BaseAgent):
    def _set_default_tools(self):
        self.tools = [
            MyCustomAgent(config=self.config, memory=self.memory),
            DeepSearchAgent(config=self.config, memory=self.memory),
        ]
```

---

## Memory System

### Checkpoint & Resume

FinSight's checkpoint system enables resuming interrupted runs.

#### How Checkpoints Work

```python
# Each agent saves state during execution
await self.save(
    state={
        'conversation_history': conversation_history,
        'current_round': current_round,
        'input_data': input_data,
    },
    checkpoint_name='latest.pkl'
)

# On resume, state is restored
state = await self.load(checkpoint_name='latest.pkl')
if state:
    conversation_history = state.get('conversation_history', [])
    current_round = state.get('current_round', 0)
```

#### Checkpoint Locations

```
outputs/
└── <target_name>/
    ├── memory/
    │   └── memory.pkl           # Global memory state
    ├── agent_working/
    │   ├── agent_data_collector_xxx/
    │   │   └── .cache/
    │   │       └── latest.pkl   # Agent checkpoint
    │   ├── agent_data_analyzer_xxx/
    │   │   ├── .cache/
    │   │   │   ├── latest.pkl
    │   │   │   └── charts.pkl   # Chart generation progress
    │   │   └── images/          # Generated charts
    │   └── agent_report_generator_xxx/
    │       └── .cache/
    │           ├── outline_latest.pkl
    │           ├── section_0.pkl
    │           ├── section_1.pkl
    │           └── report_latest.pkl
    └── logs/
```

#### Controlling Resume Behavior

```python
# Full resume (default)
asyncio.run(run_report(resume=True))

# Fresh start
asyncio.run(run_report(resume=False))
```

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Memory                                   │
│                                                                  │
│  ┌─────────────────┐     ┌─────────────────────────────────┐   │
│  │ data: List      │     │ task_mapping: List               │   │
│  │ - ToolResult    │     │ - task_key                       │   │
│  │ - SearchResult  │     │ - agent_class_name               │   │
│  │ - AnalysisResult│     │ - agent_id                       │   │
│  └─────────────────┘     │ - priority                       │   │
│                          └─────────────────────────────────┘   │
│  ┌─────────────────┐     ┌─────────────────────────────────┐   │
│  │ dependency:     │     │ log: List                        │   │
│  │ parent -> child │     │ - timestamp                      │   │
│  │ mapping         │     │ - agent_id, input, output        │   │
│  └─────────────────┘     └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Access Methods                           │
│                                                                  │
│  memory.get_collect_data()      → List[ToolResult]              │
│  memory.get_analysis_result()   → List[AnalysisResult]          │
│  memory.retrieve_relevant_data(query, top_k) → List[ToolResult] │
│  memory.select_data_by_llm(query) → (List, str)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Complete Examples

### Example 1: Custom Company Analysis

```python
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from src.config import Config
from src.memory import Memory
from src.agents import DataCollector, DataAnalyzer, ReportGenerator

async def analyze_company():
    # Configuration
    config = Config(
        config_file_path='my_config.yaml',
        config_dict={
            'target_name': 'Apple Inc.',
            'stock_code': 'AAPL',
            'target_type': 'financial_company',
            'language': 'en',
            'output_dir': './outputs/apple-analysis',
        }
    )
    
    memory = Memory(config=config)
    
    # Define custom tasks
    collect_tasks = [
        "Financial statements (10-K, 10-Q)",
        "Stock price history",
        "Analyst ratings",
        "Competitor data (Microsoft, Google)",
    ]
    
    analysis_tasks = [
        "Analyze iPhone vs Services revenue trends",
        "Evaluate profit margin sustainability",
        "Compare valuation multiples with FAANG peers",
    ]
    
    # Run data collection
    for task in collect_tasks:
        collector = DataCollector(
            config=config,
            memory=memory,
            use_llm_name=os.getenv("DS_MODEL_NAME")
        )
        await collector.async_run(
            input_data={'task': f"Apple Inc.: {task}"},
            max_iterations=15
        )
    
    # Run analysis
    for task in analysis_tasks:
        analyzer = DataAnalyzer(
            config=config,
            memory=memory,
            use_llm_name=os.getenv("DS_MODEL_NAME"),
            use_vlm_name=os.getenv("VLM_MODEL_NAME"),
            use_embedding_name=os.getenv("EMBEDDING_MODEL_NAME")
        )
        await analyzer.async_run(
            input_data={
                'task': 'Apple Inc. Investment Research',
                'analysis_task': task
            },
            max_iterations=15,
            enable_chart=True
        )
    
    # Generate report
    generator = ReportGenerator(
        config=config,
        memory=memory,
        use_llm_name=os.getenv("DS_MODEL_NAME"),
        use_embedding_name=os.getenv("EMBEDDING_MODEL_NAME")
    )
    
    report = await generator.async_run(
        input_data={'task': 'Apple Inc. Investment Research'},
        max_iterations=20,
        enable_chart=True
    )
    
    print(f"Report generated: {config.working_dir}")

asyncio.run(analyze_company())
```

### Example 2: General Deep Research

```python
async def deep_research(query: str):
    """Run deep research on any topic."""
    config = Config(
        config_file_path='my_config.yaml',
        config_dict={
            'target_name': query,
            'target_type': 'general',
            'language': 'en',
            'output_dir': f'./outputs/research-{query[:30]}',
        }
    )
    
    memory = Memory(config=config)
    
    # Auto-generate analysis tasks
    analysis_tasks = await memory.generate_analyze_tasks(
        query=query,
        use_llm_name=os.getenv("DS_MODEL_NAME"),
        max_num=8
    )
    
    # Run analysis tasks
    for task in analysis_tasks:
        analyzer = DataAnalyzer(
            config=config,
            memory=memory,
            use_llm_name=os.getenv("DS_MODEL_NAME"),
            use_vlm_name=os.getenv("VLM_MODEL_NAME"),
            use_embedding_name=os.getenv("EMBEDDING_MODEL_NAME")
        )
        await analyzer.async_run(
            input_data={
                'task': query,
                'analysis_task': task
            },
            max_iterations=15,
            enable_chart=False  # Text-only for general research
        )
    
    # Generate report
    generator = ReportGenerator(
        config=config,
        memory=memory,
        use_llm_name=os.getenv("DS_MODEL_NAME"),
        use_embedding_name=os.getenv("EMBEDDING_MODEL_NAME")
    )
    
    report = await generator.async_run(
        input_data={'task': query},
        max_iterations=15,
        enable_chart=False,
        add_introduction=False,  # Skip abstract for general reports
        add_reference_section=True
    )
    
    return report

# Usage
asyncio.run(deep_research("Impact of AI on healthcare industry in 2024"))
```

---

## Contributing

We welcome contributions! Key areas for contribution:

1. **New Tools**: Add data sources for different markets
2. **Prompt Improvements**: Enhance agent reasoning quality
3. **Visualization**: Better chart templates and styles
4. **Documentation**: Tutorials and examples


