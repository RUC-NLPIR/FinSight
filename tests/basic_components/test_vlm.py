import argparse
import os
import sys
from pathlib import Path
import asyncio
root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
from src.utils.helper import image_to_base64

vlm = OpenAI(api_key=os.getenv("VLM_API_KEY"), base_url=os.getenv("VLM_BASE_URL"))

image = image_to_base64("Snipaste.jpg")
critic_response = vlm.chat.completions.create(
    model=os.getenv("VLM_MODEL_NAME"),
    messages=[
        {"role": "user", "content": [
            {"type": "text", "text": "这是什么图案?"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image}"}}
        ]}
    ],
)
print(critic_response)