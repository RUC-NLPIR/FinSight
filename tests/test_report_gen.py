import argparse
import os
import sys
import dill
from pathlib import Path
import asyncio


root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

import argparse
import os
import sys
from pathlib import Path
import asyncio
from collections import defaultdict
import logging

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.config import Config
from src.agents import DataCollector, DataAnalyzer, ReportGenerator
from src.memory import Memory
from src.utils import setup_logger
from src.utils import get_logger
from src.agents.base_agent import BaseAgent
get_logger().set_agent_context('runner', 'main')

if __name__ == "__main__":
    collect_tasks = ['最近股价', '商汤科技的资产负债表']
    analysis_tasks = ['公司发展历程及主营业务分析', '公司股权结构分析']
    
    config = Config(config_file='my_config.yaml')
    
    # 初始化memory
    memory = Memory(config=config)
    
    # 初始化logger（设置日志目录）
    log_dir = os.path.join(config.working_dir, 'logs')
    logger = setup_logger(log_dir=log_dir, log_level=logging.INFO)
    memory.load()

    # agent = ReportGenerator(config=config, use_llm_name='deepseek/deepseek-chat-v3.1', use_embedding_name='qwen3-embedding-0.6b',memory=memory, agent_id='agent_report_generator_795e8d0a')
    agent = asyncio.run(BaseAgent.from_checkpoint(config=config, memory=memory, agent_id='agent_report_generator_795e8d0a'))
    agent.use_embedding_name = 'qwen3-embedding-0.6b'
    result = asyncio.run(agent.async_run(input_data={'task': f'研究目标: {config.config["target_name"]}(股票代码: {config.config["stock_code"]})', 'task_type': 'company'}, echo=True, max_iterations=5))
    with open(os.path.join(config.working_dir, 'report_generator_result.pkl'), 'wb') as f:
        dill.dump(result, f)