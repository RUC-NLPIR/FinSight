import argparse
import os
import sys
from pathlib import Path
import asyncio
root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)


from src.config import Config

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    config = Config(
        config_file_path='tests/my_config.yaml'
    )
    print(config)
    sample_data = [{"role": "user", "content": "请帮我生成一个10个单词的英文句子。"}]
    
    print(config.llm_dict)
    ds_model_name = os.getenv('DS_MODEL_NAME')
    llm = config.llm_dict[ds_model_name]
    result = asyncio.run(llm.generate(messages=sample_data))
    print(result)