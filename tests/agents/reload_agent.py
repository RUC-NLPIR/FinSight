import argparse
import os
import sys
import dill
from pathlib import Path
import asyncio
import logging

root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)
from dotenv import load_dotenv
load_dotenv()


from src.config import Config
from src.agents import DataCollector
from src.agents.base_agent import BaseAgent
from src.memory import Memory
from src.utils import setup_logger
from src.utils import get_logger
get_logger().set_agent_context('runner', 'main')

if __name__ == "__main__":
    config = Config(
        config_file_path='tests/my_config.yaml',
        config_dict={
            "output_dir": 'outputs/tests', 
            'target_name':'商汤科技',
            'stock_code': '00020',
            'reference_doc_path': 'src/config/report_template.docx',
            'outline_template_path': "src/template/company_outline.md",
        }
    )

    memory = Memory(config=config)
    log_dir = os.path.join(config.working_dir, 'logs')
    logger = setup_logger(log_dir=log_dir, log_level=logging.DEBUG)

    agent = asyncio.run(BaseAgent.from_checkpoint(config=config, memory=memory, agent_id='agent_data_collector_a8e4b96b', checkpoint_name='latest.pkl'))
    print(agent.current_checkpoint)