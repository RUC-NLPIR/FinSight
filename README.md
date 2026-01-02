<div align="center">

<img src="assets/finsight-logo-v2.png" width="400">

FinSight: Towards Real-World Financial Deep Research
---

*From data to insights, fully automated, multi-modal financial reports.*


<p>

[![arXiv](https://img.shields.io/badge/arXiv-2510.16844-b31b1b.svg?style=flat)](https://arxiv.org/abs/2510.16844)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
<a href="https://deepwiki.com/RUC-NLPIR/FinSight"><img src="https://devin.ai/assets/deepwiki-badge.png" alt="DeepWiki Document" height="20"/></a>
[![AFAC2025 Track 4](https://img.shields.io/badge/🏆_AFAC2025-1st_Place_(1/1289)-gold.svg?style=flat)](https://tianchi.aliyun.com/specials/promotion/afac2025)

</p>

**FinSight** is a multi-agent research system that automates the entire financial research process — from data collection and analysis to generating publication-ready reports with professional charts and deep insights.

🎯 **One ticker, one click, one comprehensive research report.**


<br>

*If this project helps you, please ⭐ star & 🍴 fork!*

</div>

## 🎥 Demo

https://github.com/user-attachments/assets/41963369-3dd4-4dfd-ad95-ef95cd092ebb

<p align="center">
  <i>Easy-to-Use UI demo: one ticker ➜ automated research ➜ publish-ready report.</i>
</p>


<div align="center">
  <a href="/assets/example_reports/Financial_Agent_Industry.pdf">
    <img src="/assets/example6_industry.jpg" width="100%" alt="The Development of Financial AI Agents">
  </a>

  <i>📄 Final Generated Report Example: The Development of Financial AI Agents (click pickture to read)</i>
</div>




## 📑 Table of Contents
- [✨ Key Features](#-key-features)
- [🗺️ Roadmap](#-roadmap)
- [🚀 Quick Start](#-quick-start)
- [🎨 Result Examples](#-result-examples)
- [🏗️ Architecture](#-architecture)
- [📖 Advanced Usage](#-advanced-usage)
- [📊 Evaluation Results](#-evaluation-results)
- [📜 License](#-license)
- [📖 Citation](#-citation)
- [🙏 Acknowledgments](#-acknowledgments)


## ✨ Key Features

* **📊 Professional-Grade Report Generation**
    One-click to generate 20,000+ word financial reports that rival human experts. Outperforms GPT-5 and Perplexity Deep Research in factual accuracy, analytical depth, and presentation quality.

* **🤖 Programmable Code Agent (CAVM)**
    Implementation of the *Code Agent with Variable Memory* architecture. Unlike rigid workflows, agents operate in a unified variable space, executing Python code to manipulate data, tools, and memory dynamically for transparent and reproducible analysis.

* **📈 Automated Charting with VLM Feedback**
    Solves the "ugly AI chart" problem. Built-in visual agents strictly follow professional standards, automatically correcting missing legends, wrong scales, or low information density through visual feedback loops.

* **🔍 Deep Research with Evidence Tracing**
    No more black-box summaries. Every conclusion is derived from a transparent *Chain-of-Analysis*, with strict citations linking back to original data sources, ensuring high textual faithfulness and verifiable insights.

* **⚡ Comprehensive Market Intelligence**
    A unified interface for multi-source financial data. access real-time stock quotes, financial statements, and macro indicators across A-share and HK markets, powered by a robust Python-based tool ecosystem.

---

## 🗺️ Roadmap

FinSight is still under development and there are many issues and room for improvement. We will continue to update. And we also sincerely welcome contributions on this open-source toolkit.

- [x] Multi-agent collaborative research workflow (collector → analyzer → report)
- [x] VLM-powered chart generation + critique loops for clean visuals
- [x] Checkpoint/resume for long-running tasks
- [x] Interactive web demo (frontend + backend)
- [ ] General-purpose research adaptation beyond finance
- [ ] Multi-market support (US, global)
- [ ] Plugin system for custom tools and agents

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Pandoc (for polished DOCX/PDF export)
- Node.js (optional, for the web UI)
- API keys for your LLM stack (LLM, VLM, Embedding, Search)

### Installation

```bash
# Clone the repository
git clone https://github.com/RUC-NLPIR/FinSight.git
cd FinSight

# Install Python dependencies
pip install -r requirements.txt
```

Install Pandoc (recommended):

```bash
# Linux
sudo apt-get install pandoc

# macOS
brew install pandoc

# Windows
# Download the latest installer:
# https://github.com/jgm/pandoc/releases/latest
```

Build the web UI (optional):

```bash
cd demo/frontend
npm install
npm run build
```

### Configuration

FinSight uses a two-layer configuration:

1) `.env` — model endpoints & API keys  
```bash
cp .env.example .env
# fill in DS_MODEL_NAME / API keys / base URLs
```

2) `my_config.yaml` — research target & tasks  
```yaml
target_name: "Your Company Name"
stock_code: "000001"      # A-share or HK ticker
target_type: "financial_company"  # financial_company | macro | industry | general
output_dir: "./outputs/my-research"
language: "en"            # en or zh

custom_collect_tasks:
  - "Balance sheet, income statement, cash flow"
  - "Stock price data and trading volume"
```

### Run FinSight

**CLI (full pipeline)**
```bash
python run_report.py
```

**Web Demo**
```bash
# Backend
cd demo/backend && python app.py

# Frontend
cd demo/frontend && npm run dev
```
Open http://localhost:3000

---


## 🎨 Result Examples

Below is a **fully automated** research report on **The Development of Financial AI Agents**, generated entirely by this project.


<div align="center">
  <a href="/assets/example_reports/Financial_Agent_Industry.pdf">
    <img src="/assets/example6_industry.jpg" width="100%" alt="The Development of Financial AI Agents">
  </a>
</div>

<br>

**Breakdown of the specific capabilities used to generate such reports:**

<div align="center">

| | |
|:---:|:---:|
| <img src="assets/example1.png" width="450" alt="Core revenue analysis"> | <img src="assets/example2.png" width="450" alt="Multi-dimensional financial data"> |
| **Core revenue analysis** | **Multi-dimensional financial data** |
| <img src="assets/example3.png" width="450" alt="Publication-grade report"> | <img src="assets/example4.png" width="450" alt="Chart-grounded analysis"> |
| **Publication-grade report** | **Chart-grounded analysis** |

</div>

Full sample reports live in `assets/example_reports`.

![Full report preview](/assets/example6_industry.jpg)

---

## 🏗️ Architecture

<p align="center">
  <img src="assets/architecture.jpg" alt="FinSight Architecture" width="800"/>
</p>

FinSight is a multi-stage, memory-centric pipeline: Data Collection → Analysis + VLM chart refinement → Report drafting & polishing → Rendering. Each agent runs in a shared variable space with resumable checkpoints.

**Agent roster**

| Agent | Purpose | Key inputs | Outputs | Default tools/skills |
|-------|---------|------------|---------|----------------------|
| 📥 Data Collector | Route and gather structured/unstructured data | Task, ticker/market, custom tasks | Normalized datasets in memory | DeepSearch Agent; all financial/macro/industry tools |
| 🔍 Deep Search Agent | Multi-hop web search + content fetch with source validation | Task, query | Search snippets + crawled pages with citations | Serper/Google search; web page fetcher |
| 🔬 Data Analyzer | Code-first analysis, charting, VLM critique | Task, analysis task, collected data | Analysis report, charts + captions | DeepSearch Agent; custom palette injection |
| 📝 Report Generator | Outline → sections → polish → cover/reference → DOCX/PDF | Task, outlines, analysis/memory | Publication-ready report (MD/DOCX/PDF) | DeepSearch Agent; Pandoc + docx2pdf pipeline |

**Tool library (high-level)**

| Name | Domain | Type | What it does |
|------|--------|------|--------------|
| Stock profile | Financial | Data API | Corporate profile (A/HK) |
| Shareholding structure | Financial | Data API | Top holders, stakes, direct/indirect flags |
| Equity valuation metrics | Financial | Data API | PE/PB/ROE/margins |
| Stock candlestick data | Financial | Data API | Daily OHLCV with turnover/ROC |
| Balance sheet | Financial | Data API | Pivoted balance sheet (HK/A) |
| Income statement | Financial | Data API | Pivoted P&L (HK/A) |
| Cash-flow statement | Financial | Data API | Pivoted cash flows (HK/A) |
| CSI 300 / HSI / SSE / Nasdaq | Market Index | Data API | Daily index OHLCV |
| China macro leverage ratio | Macro | Data API | Household/corporate/gov leverage |
| Enterprise commodity price index | Macro/Industry | Data API | Commodity price index & sub-series |
| China LPR benchmark rates | Macro | Data API | 1Y/5Y benchmark rates |
| Urban surveyed unemployment | Macro | Data API | Unemployment by age/city |
| Total social financing increment | Macro | Data API | TSF components since 2015 |
| China GDP / CPI / PPI YoY | Macro | Data API | Core macro indicators |
| US CPI YoY | Macro | Data API | US inflation series |
| China exports/imports YoY, trade balance | Macro | Data API | External sector metrics |
| Fiscal revenue / FX loan / Money supply / RRR | Macro | Data API | Monetary & fiscal trackers |
| FX and gold reserves | Macro | Data API | Monthly reserves |
| National stock trading stats | Macro | Data API | Market-wide trading metrics |
| Economic policy uncertainty (CN) | Macro | Data API | EPU index |
| Industrial value-added growth | Industry | Data API | Industrial production trends |
| Above-scale industrial production YoY | Industry | Data API | Large enterprise production |
| Manufacturing PMI (official) | Industry | Data API | PMI time series |
| Caixin services PMI | Industry | Data API | Services PMI |
| Consumer price / retail price index | Industry | Data API | CPI/RPI monthly |
| GDP (monthly stats) | Industry | Data API | GDP-related monthly stats |
| Producer price index | Industry | Data API | PPI (ex-factory) |
| Consumer confidence index | Industry | Data API | Sentiment series |
| Total retail sales of consumer goods | Industry | Data API | Retail sales + YoY/MoM |
| Bing web search (requests) | Web | Search | HTML-based Bing search |
| Google Search Engine (Serper) | Web | Search | API Google search |
| Bocha web search | Web | Search | CN-focused search API |
| DuckDuckGo / Sogou search | Web | Search | Alternative HTML searches |
| Financial site in-domain search (requests/playwright) | Web | Search | Scoped finance domains |
| Bing web search (Playwright) | Web | Search (browser) | Dynamic page search |
| Bing image search | Web | Image search | Image/snippet retrieval |
| Web page content fetcher | Web | Crawler | HTML/PDF crawl + markdown extraction |

---


## 📖 Advanced Usage

> **📚 Full Documentation**: See **[docs/advanced_usage.md](docs/advanced_usage.md)** for comprehensive technical documentation with code examples.

<details>
<summary><b>🔑 API Keys & Model Configuration</b></summary>

### Environment Variables (`.env`)

FinSight requires three model types. Create a `.env` file in the project root:

```bash
# LLM (Main reasoning, code generation)
DS_MODEL_NAME="deepseek-chat"
DS_API_KEY="sk-your-key"
DS_BASE_URL="https://api.deepseek.com/v1"

# VLM (Chart analysis and refinement)
VLM_MODEL_NAME="qwen-vl-max"
VLM_API_KEY="sk-your-key"
VLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# Embedding (Semantic search)
EMBEDDING_MODEL_NAME="text-embedding-v3"
EMBEDDING_API_KEY="sk-your-key"
EMBEDDING_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# Web Search (Optional)
SERPER_API_KEY="your-serper-key"      # Google Search via Serper
BOCHAAI_API_KEY="your-bocha-key"      # Bocha Search (Chinese-focused)
```

### Using Aggregator Endpoints

```bash
# Example: OpenRouter
DS_MODEL_NAME="openai/gpt-4o"
DS_API_KEY="sk-or-xxx"
DS_BASE_URL="https://openrouter.ai/api/v1"
```

### Config Loading Logic

The `Config` class loads settings in priority order:
1. `src/config/default_config.yaml` (defaults)
2. `my_config.yaml` (your overrides)
3. Runtime `config_dict` (highest priority)

Environment variables are resolved via `${VAR_NAME}` syntax in YAML.

**Quick Test**:
```python
from src.config import Config
config = Config(config_file_path='my_config.yaml')
print(config.llm_dict.keys())  # Available models
```

</details>

<details>
<summary><b>📝 YAML Config File Reference</b></summary>

### Complete `my_config.yaml` Structure

```yaml
# ===== Target Configuration =====
target_name: "Company Name"          # Research target
stock_code: "000001"                 # Ticker (A-share or HK format)
target_type: 'financial_company'     # financial_company | macro | industry | general
output_dir: "./outputs/my-research"  # Output directory
language: 'en'                       # en | zh

# ===== Template Paths =====
reference_doc_path: 'src/template/report_template.docx'
outline_template_path: 'src/template/company_outline.md'

# ===== Custom Tasks (Optional) =====
# If omitted, LLM auto-generates appropriate tasks
custom_collect_tasks:
  - "Financial statements (balance sheet, income, cash flow)"
  - "Stock price history and trading volume"
  - "Shareholding structure"

custom_analysis_tasks:
  - "Analyze revenue trends and growth drivers"
  - "Evaluate profitability metrics (ROE, margins)"
  - "Compare with industry peers"

# ===== Cache/Resume Settings =====
use_collect_data_cache: True
use_analysis_cache: True
use_report_outline_cache: True
use_full_report_cache: True
use_post_process_cache: True

# ===== LLM Configuration =====
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

### Target Types Explained

| Type | Use Case | Default Tools |
|------|----------|---------------|
| `financial_company` | Listed company research | All financial + market tools |
| `macro` | Macroeconomic analysis | Macro indicators + GDP/CPI tools |
| `industry` | Industry/sector research | Industry + PMI tools |
| `general` | General deep research | Web search only |

</details>

<details>
<summary><b>✏️ Prompt System & Customization</b></summary>

### Prompt Directory Structure

```
src/agents/
├── data_analyzer/prompts/
│   ├── general_prompts.yaml      # For general research
│   └── financial_prompts.yaml    # For financial reports
├── report_generator/prompts/
│   ├── general_prompts.yaml
│   ├── financial_company_prompts.yaml
│   ├── financial_macro_prompts.yaml
│   └── financial_industry_prompts.yaml
├── data_collector/prompts/
│   └── prompts.yaml
└── search_agent/prompts/
    └── general_prompts.yaml
```

### Using the Prompt Loader

```python
from src.utils.prompt_loader import get_prompt_loader

# Load prompts for an agent
loader = get_prompt_loader('data_analyzer', report_type='financial')

# Get a specific prompt
prompt = loader.get_prompt('data_analysis',
    current_time="2024-12-01",
    user_query="Analyze revenue trends",
    data_info="Available datasets...",
    target_language="English"
)

# List all available prompts
print(loader.list_available_prompts())
```

### Creating Custom Prompts

1. Create `src/agents/data_analyzer/prompts/my_custom_prompts.yaml`:

```yaml
data_analysis: |
  You are an expert analyst for {industry_name}.
  
  ## Task
  {user_query}
  
  ## Available Data
  {data_info}
  
  ## Instructions
  Use <execute> for Python code, <report> for final output.
  All output must be in {target_language}.
```

2. Set `target_type: 'my_custom'` in config to load your prompts.

### Key Prompt Variables

| Variable | Description |
|----------|-------------|
| `{current_time}` | Timestamp for time-sensitive analysis |
| `{user_query}` | The analysis task |
| `{data_info}` | Available datasets catalog |
| `{api_descriptions}` | Tool API documentation |
| `{target_language}` | Output language (English/Chinese) |

</details>

<details>
<summary><b>📑 Custom Outlines & Report Templates</b></summary>

### Outline Template Configuration

Set in `my_config.yaml`:
```yaml
outline_template_path: 'src/template/company_outline.md'
```

### Creating Custom Outlines

**For Financial Company Reports**:
```markdown
# Executive Summary
Key metrics, investment thesis, rating.

# Company Overview
- Business description and history
- Management and governance
- Shareholder structure

# Industry Analysis
- Market size and growth
- Competitive landscape

# Financial Analysis
- Revenue and profitability trends
- Balance sheet analysis
- Cash flow analysis

# Valuation
- Comparable company analysis
- DCF valuation
- Target price

# Risks
- Key risks and mitigants
```

**For General Research**:
```markdown
# Introduction
Research objectives and scope.

# Background
Context and literature review.

# Methodology
Data sources and approach.

# Findings
- Finding 1
- Finding 2
- Finding 3

# Discussion
Implications and analysis.

# Conclusion
Summary and recommendations.
```

### Reference Document (Word Styling)

The `reference_doc_path` controls Word output formatting:

```yaml
reference_doc_path: 'src/template/report_template.docx'
```

**To customize**:
1. Copy the default template
2. Edit styles in Word (Heading 1/2/3, Normal, Table styles)
3. Update the config path

</details>

<details>
<summary><b>🎨 Chart Styling & Color Palettes</b></summary>

### Default Color Palette

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

### Custom Palette via Subclass

```python
class MyDataAnalyzer(DataAnalyzer):
    async def _prepare_executor(self):
        await super()._prepare_executor()
        
        # Corporate blue theme
        my_palette = [
            "#003366", "#0066CC", "#66B2FF",
            "#CCE5FF", "#E6F2FF"
        ]
        self.code_executor.set_variable("custom_palette", my_palette)
```

### VLM Chart Critique Loop

Charts go through iterative refinement:

1. **LLM generates** chart code
2. **Code executes** and saves PNG
3. **VLM evaluates** quality (clarity, labels, aesthetics)
4. **If not "FINISH"**: LLM refines based on VLM feedback
5. **Repeat** up to `max_iterations` (default: 3)

Customize in `draw_chart` prompt or adjust iterations:
```python
chart_code, chart_name = await self._draw_single_chart(
    task=...,
    max_iterations=5  # More refinement cycles
)
```

</details>

<details>
<summary><b>🛠️ Adding Custom Tools</b></summary>

### Tool Base Class

```python
from src.tools.base import Tool, ToolResult

class MyCustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="My Custom Tool",
            description="Description for LLM to understand usage",
            parameters=[
                {"name": "param1", "type": "str", 
                 "description": "First parameter", "required": True},
                {"name": "param2", "type": "int", 
                 "description": "Optional parameter", "required": False},
            ]
        )
    
    async def api_function(self, param1: str, param2: int = 10):
        # Fetch or compute data
        result_data = await self._fetch_data(param1, param2)
        
        return [
            ToolResult(
                name=f"Result for {param1}",
                description="What this data contains",
                data=result_data,  # DataFrame, dict, list, etc.
                source="Data source URL or description"
            )
        ]
```

### Auto-Registration

Place your tool in the appropriate category folder:
```
src/tools/
├── financial/
│   └── my_stock_tool.py  ← Your new tool
├── macro/
├── industry/
└── web/
```

Tools are **automatically registered** on import:
```python
from src.tools import list_tools, get_tool_by_name

print(list_tools())  # Your tool appears here
tool = get_tool_by_name('My Custom Tool')()
result = await tool.api_function(param1='test')
```

### Example: Stock Technical Analysis Tool

```python
# src/tools/financial/technical_tool.py
import pandas as pd
from ..base import Tool, ToolResult

class TechnicalAnalysisTool(Tool):
    def __init__(self):
        super().__init__(
            name="Stock technical indicators",
            description="Calculate SMA, RSI, MACD for a stock",
            parameters=[
                {"name": "stock_code", "type": "str", 
                 "description": "Stock ticker", "required": True},
            ],
        )

    async def api_function(self, stock_code: str):
        import efinance as ef
        
        df = ef.stock.get_quote_history(stock_code)
        # Calculate indicators...
        df['SMA_20'] = df['收盘'].rolling(window=20).mean()
        
        return [ToolResult(
            name=f"Technical indicators for {stock_code}",
            description="SMA, RSI indicators",
            data=df,
            source="Calculated from exchange data"
        )]
```

</details>

<details>
<summary><b>🤖 Adding Custom Agents</b></summary>

### Agent Base Class

```python
from src.agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    AGENT_NAME = 'my_custom_agent'
    AGENT_DESCRIPTION = 'Description for use as a sub-agent'
    NECESSARY_KEYS = ['task', 'custom_param']
    
    def __init__(self, config, tools=None, use_llm_name="deepseek-chat",
                 enable_code=True, memory=None, agent_id=None):
        if tools is None:
            tools = self._get_default_tools()
        super().__init__(config, tools, use_llm_name, enable_code, memory, agent_id)
        
        # Load prompts
        from src.utils.prompt_loader import get_prompt_loader
        self.prompt_loader = get_prompt_loader('my_custom_agent')
    
    async def _prepare_init_prompt(self, input_data: dict) -> list[dict]:
        prompt = self.prompt_loader.get_prompt('main_prompt',
            task=input_data['task'],
            current_time=self.current_time
        )
        return [{"role": "user", "content": prompt}]
    
    # Custom action handlers
    async def _handle_analyze_action(self, action_content: str):
        result = await self._perform_analysis(action_content)
        return {"action": "analyze", "result": result, "continue": True}
    
    async def _handle_final_action(self, action_content: str):
        return {"action": "final", "result": action_content, "continue": False}
```

### Using Agents as Tools

```python
class ParentAgent(BaseAgent):
    def _set_default_tools(self):
        self.tools = [
            MyCustomAgent(config=self.config, memory=self.memory),
            DeepSearchAgent(config=self.config, memory=self.memory),
        ]
```

</details>

<details>
<summary><b>💾 Checkpoint & Resume System</b></summary>

### How It Works

Each agent saves state during execution:
```python
await self.save(
    state={
        'conversation_history': conversation_history,
        'current_round': current_round,
    },
    checkpoint_name='latest.pkl'
)
```

### Checkpoint Locations

```
outputs/<target_name>/
├── memory/
│   └── memory.pkl           # Global memory state
├── agent_working/
│   ├── agent_data_collector_xxx/
│   │   └── .cache/latest.pkl
│   ├── agent_data_analyzer_xxx/
│   │   ├── .cache/latest.pkl
│   │   ├── .cache/charts.pkl
│   │   └── images/
│   └── agent_report_generator_xxx/
│       └── .cache/
│           ├── outline_latest.pkl
│           ├── section_0.pkl
│           └── report_latest.pkl
└── logs/
```

### Controlling Resume

```python
# Resume from checkpoints (default)
asyncio.run(run_report(resume=True))

# Fresh start (ignores checkpoints)
asyncio.run(run_report(resume=False))
```

### Memory Data Flow

```python
from src.memory import Memory

memory = Memory(config=config)
memory.load()  # Load from checkpoint

# Access collected data
data_list = memory.get_collect_data()

# Access analysis results
analyses = memory.get_analysis_result()

# Semantic search
relevant = await memory.retrieve_relevant_data(
    query="revenue trends",
    top_k=10,
    embedding_model="text-embedding-v3"
)
```

</details>

<details>
<summary><b>📚 Complete Code Examples</b></summary>

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
    config = Config(
        config_file_path='my_config.yaml',
        config_dict={
            'target_name': 'Apple Inc.',
            'stock_code': 'AAPL',
            'target_type': 'financial_company',
            'language': 'en',
        }
    )
    
    memory = Memory(config=config)
    
    # Run analysis
    analyzer = DataAnalyzer(
        config=config, memory=memory,
        use_llm_name=os.getenv("DS_MODEL_NAME"),
        use_vlm_name=os.getenv("VLM_MODEL_NAME"),
        use_embedding_name=os.getenv("EMBEDDING_MODEL_NAME")
    )
    
    await analyzer.async_run(
        input_data={
            'task': 'Apple Inc. Investment Research',
            'analysis_task': 'Analyze iPhone vs Services revenue'
        },
        max_iterations=15,
        enable_chart=True
    )
    
    # Generate report
    generator = ReportGenerator(config=config, memory=memory,
        use_llm_name=os.getenv("DS_MODEL_NAME"),
        use_embedding_name=os.getenv("EMBEDDING_MODEL_NAME"))
    
    await generator.async_run(
        input_data={'task': 'Apple Inc. Investment Research'},
        enable_chart=True
    )

asyncio.run(analyze_company())
```

### Example 2: General Deep Research

```python
async def deep_research(query: str):
    config = Config(config_dict={
        'target_name': query,
        'target_type': 'general',
        'language': 'en',
    })
    
    memory = Memory(config=config)
    
    # Auto-generate analysis tasks
    tasks = await memory.generate_analyze_tasks(
        query=query,
        use_llm_name=os.getenv("DS_MODEL_NAME"),
        max_num=5
    )
    
    for task in tasks:
        analyzer = DataAnalyzer(config=config, memory=memory, ...)
        await analyzer.async_run(
            input_data={'task': query, 'analysis_task': task},
            enable_chart=False
        )
    
    generator = ReportGenerator(config=config, memory=memory, ...)
    await generator.async_run(
        input_data={'task': query},
        enable_chart=False,
        add_introduction=False
    )

asyncio.run(deep_research("Impact of AI on healthcare in 2024"))
```

</details>

> **📚 See [docs/advanced_usage.md](docs/advanced_usage.md)** for the complete technical reference with architecture diagrams, troubleshooting, and more examples.

---

## 📊 Evaluation Results

We conducted comprehensive evaluations comparing FinSight against leading commercial deep research systems, including **OpenAI Deep Research** and **Gemini-2.5-Pro Deep Research**. Our experiments demonstrate that FinSight significantly outperforms existing solutions, achieving a state-of-the-art overall score of **8.09**.

<div align="center">

| | |
|:---:|:---:|
| <img src="assets/evaluation_result_1.jpg" width="500" alt="Comparison with Deep Research Agents"> | <img src="assets/evaluation_result_2.jpg" width="500" alt="Generated Report Sample"> |
| **Figure 1:** Performance comparison against SOTA agents | **Figure 2:** Key Fact Recall and Citation Authority |

</div>

**Key Findings:**
- **SOTA Performance:** FinSight achieves superior overall scores (**8.09**) compared to Gemini-2.5-Pro Deep Research (6.82) and OpenAI Deep Research (6.11).
- **Deep Analysis:** Our **Two-Stage Writing Framework** produces reports with higher information richness and analytical depth compared to single-pass LLM searches.
- **Expert Visualization:** The **Iterative Vision-Enhanced Mechanism** ensures publication-grade charts, achieving a visualization score of **9.00** (vs. 4.65 for OpenAI).

> 📄 For detailed experimental setup and complete results, please refer to our [paper](https://arxiv.org/abs/2510.16844).

---

## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## 📖 Citation

If you find FinSight useful in your research, please cite our paper:

```bibtex
@article{jin2025finsight,
  author       = {Jiajie Jin and Yuyao Zhang and Yimeng Xu and 
                  Hongjin Qian and Yutao Zhu and Zhicheng Dou},
  title        = {FinSight: Towards Real-World Financial Deep Research},
  journal      = {CoRR},
  volume       = {abs/2510.16844},
  year         = {2025},
  url          = {https://doi.org/10.48550/arXiv.2510.16844},
  eprinttype   = {arXiv},
  eprint       = {2510.16844},
}
```

---

## 🙏 Acknowledgments

- [AkShare](https://akshare.akfamily.xyz/) for financial data APIs
- [eFinance](https://github.com/mpquant/efinance) for stock data
- [Crawl4AI](https://github.com/unclecode/crawl4ai) for web crawling



