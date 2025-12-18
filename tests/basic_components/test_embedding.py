import os
import sys
import asyncio
from pathlib import Path

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
    embedding_model_name = os.getenv('EMBEDDING_MODEL_NAME')
    embedding_model = config.llm_dict[embedding_model_name]
    response = asyncio.run(embedding_model.generate_embeddings(input_texts=["who is jack"]))
    print(response)