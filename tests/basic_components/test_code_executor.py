import argparse
import os
import sys
from pathlib import Path
import asyncio

root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)

from src.config import Config
from src.utils import AsyncCodeExecutor, CodeExecutor

async def main():
    print("\n--- [Test 1: Basic Execution & Package Import] ---")
    executor_1 = AsyncCodeExecutor(working_dir=".cache")
    
    executor_1.set_variable("my_message", "Hello, World!")
    print("Step 1: Importing pandas and performing a calculation")
    code_string = """
import pandas as pd
a = 42
b = 329
print(a + b)
print(xxx)
"""
    result_1 = await executor_1.execute(code_string)
    print(result_1)
    print("---------")
    code_string2 = """
a = a+1
print(a)
"""
    result_2 = await executor_1.execute(code_string2)
    print(result_2)
    print("ressss")

    # result_3 = await executor_1.get_environment_info()
    # print(result_3)

    result_4 = await executor_1.execute("print(my_message)")
    print(result_4)

    executor_1.set_variable("my_message2", "Hello, World!2")
    result_5 = await executor_1.execute("print(my_message2)")
    print(result_5)

    num = 0
    def test_function(x):
        print("this is a test function")
        print(x)
        num += 1
        return x+1
    print(num)
    result = executor_1.set_variable("test_function", test_function)
    result = await executor_1.execute("test_function(1)")
    print(result)
    print(num)



if __name__ == "__main__":
    asyncio.run(main())