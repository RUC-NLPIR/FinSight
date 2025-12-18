import argparse
import os
import sys
from pathlib import Path
import asyncio
import logging
root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)

from src.config import Config
from src.agents import DeepSearchAgent
from src.memory import Memory
from src.utils import setup_logger
from src.utils import get_logger
get_logger().set_agent_context('runner', 'main')
from dotenv import load_dotenv
load_dotenv()
if __name__ == "__main__":
    
    config = Config(
        config_file_path='my_config.yaml',
    )

    memory = Memory(config=config)
    # memory.load()
    # print(len(memory.data))
    # assert False
    log_dir = os.path.join(config.working_dir, 'logs')
    logger = setup_logger(log_dir=log_dir, log_level=logging.INFO)
    agent = DeepSearchAgent(config=config, use_llm_name=os.getenv('DS_MODEL_NAME'), memory=memory)
    result = asyncio.run(agent.async_run(input_data={'task': '商汤科技', 'query': 'SenseTime government contracts enterprise customers financial services healthcare clients 2024'}, echo=True, max_iterations=5))
    # print(result)
    print(result['final_result'])
    print(len(memory.data))