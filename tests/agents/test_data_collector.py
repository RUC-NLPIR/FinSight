import argparse
import os
import sys
import dill
from pathlib import Path
import asyncio
import logging
from dotenv import load_dotenv
load_dotenv()
root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)

from src.config import Config
from src.agents import DataCollector
from src.memory import Memory
from src.utils import setup_logger
from src.utils import get_logger
get_logger().set_agent_context('runner', 'main')

if __name__ == "__main__":
    config = Config(
        config_file_path='tests/my_config.yaml',
    )

    memory = Memory(config=config)
    
    log_dir = os.path.join(config.working_dir, 'logs')
    logger = setup_logger(log_dir=log_dir, log_level=logging.DEBUG)


    agent = DataCollector(config=config, use_llm_name=os.getenv('DS_MODEL_NAME'), memory=memory)
    result = asyncio.run(agent.async_run(input_data={'task': '浪潮信息（000977）的股价信息'}, echo=True, max_iterations=5))
    print(result['final_result'])