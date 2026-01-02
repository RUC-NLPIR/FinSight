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
from src.agents import DataAnalyzer, DataCollector
from src.memory import Memory

if __name__ == "__main__":
    config = Config(
        config_file_path='my_config.yaml',
    )

    memory = Memory(config=config)
    # memory.load()
    # print(memory.get_analysis_result()[0])
    # assert False

    agent = DataAnalyzer(
        config=config, 
        use_llm_name=os.getenv("DS_MODEL_NAME"), 
        use_vlm_name=os.getenv("VLM_MODEL_NAME"), 
        use_embedding_name=os.getenv("EMBEDDING_MODEL_NAME"),
        memory=memory
    )
    result = asyncio.run(agent.async_run(
        input_data={'task': '商汤科技', 'analysis_task': '商汤科技的主要营收来源'}, echo=True, max_iterations=10, enable_chart=True)
    )
    print(result)
    print(result['final_result'][:100000])
    print(len(memory.data))