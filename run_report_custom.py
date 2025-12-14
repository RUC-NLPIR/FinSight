import argparse
import os
import sys
from pathlib import Path
import asyncio
import traceback
from collections import defaultdict
import logging
from dotenv import load_dotenv
load_dotenv()

from src.config import Config
from src.agents import DataCollector, DataAnalyzer, ReportGenerator
from src.memory import Memory
from src.utils import setup_logger
from src.utils import get_logger
get_logger().set_agent_context('runner', 'main')


async def run_report(query, save_note: str = None, resume: bool = True):
    use_llm_name = os.getenv("DS_MODEL_NAME")
    use_vlm_name = os.getenv("VLM_MODEL_NAME")
    use_embedding_name = os.getenv("EMBEDDING_MODEL_NAME")
    config = Config(
        config_file_path='/data00/jiajie_jin/finsight/FinSight/tests/my_config.yaml',
        config_dict={
            "output_dir": '/data00/jiajie_jin/finsight/FinSight/outputs/deepconsult-r1', 
            'target_name': query,
            "target_type": "general",
            'reference_doc_path': '/data00/jiajie_jin/finsight/FinSight/src/config/report_template.docx',
            'outline_template_path': None,
            'language': 'en',
            'save_note': str(save_note)
        }
    )
    
    # Initialize memory
    memory = Memory(config=config)
    
    # Initialize logger
    log_dir = os.path.join(config.working_dir, 'logs')
    logger = setup_logger(log_dir=log_dir, log_level=logging.INFO)
    
    if resume:
        memory.load()
        logger.info("Memory state loaded")
    # print(memory.get_analysis_result()[1])
    # assert False

    if memory.generated_analysis_tasks == []:
        # Prepare prioritized task list (lower value = higher priority)
        # Increased max_num to 8 to ensure comprehensive scenario coverage and case study inclusion
        analysis_tasks = await memory.generate_analyze_tasks(
            query=config.config['target_name'], 
            use_llm_name=use_llm_name, 
            max_num=8,
            existing_tasks=[]  # No existing tasks in this custom script
        )
    else:
        analysis_tasks = memory.generated_analysis_tasks
    tasks_to_run = []    
    # Analysis tasks (run after collection)
    for task in analysis_tasks:
        tasks_to_run.append({
            'agent_class': DataAnalyzer,
            'task_input': {
                'input_data': {
                    'task': f'Global Research Query: {config.config["target_name"]}',
                    'analysis_task': task
                },
                'echo': True,
                'max_iterations': 15,
                'enable_chart': False
            },
            'agent_kwargs': {
                'use_llm_name': use_llm_name,
                'use_vlm_name': use_vlm_name,
                'use_embedding_name': use_embedding_name,
            },
            'priority': 2,
        })
    
    # Report generation task
    tasks_to_run.append({
        'agent_class': ReportGenerator,
        'task_input': {
            'input_data': {
                'task': f'{config.config["target_name"]}',
            },
            'echo': True,
            'max_iterations': 10,
            'enable_chart': False,
        },
        'agent_kwargs': {
            'use_llm_name': use_llm_name,
            'use_embedding_name': use_embedding_name,
        },
        'priority': 3,
    })


    # Use memory to obtain/create the required agents (records tasks internally)
    agents_info = []
    for task_info in tasks_to_run:
        agent = await memory.get_or_create_agent(
            agent_class=task_info['agent_class'],
            task_input=task_info['task_input'],
            resume=resume,
            priority=task_info['priority'],
            **task_info['agent_kwargs']
        )
        # Retrieve the persisted priority (may differ on resume)
        actual_priority = task_info['priority']
        for saved_task in memory.task_mapping:
            if saved_task.get('agent_id') == agent.id:
                actual_priority = saved_task.get('priority', task_info['priority'])
                break
        
        agents_info.append({
            'agent': agent,
            'task_input': task_info['task_input'],
            'priority': actual_priority,
        })
    

    memory.save()
    
    
    # Execute tasks by priority tier (parallel within a tier)
    agents_info.sort(key=lambda x: x['priority'])
    
    # Group tasks by priority
    priority_groups = defaultdict(list)
    for agent_info in agents_info:
        priority_groups[agent_info['priority']].append(agent_info)
    
    # Execute each priority tier sequentially
    sorted_priorities = sorted(priority_groups.keys())
    for priority in sorted_priorities:
        group = priority_groups[priority]
        logger.info(f"\nExecuting priority {priority} group ({len(group)} task(s))")
        
        # Skip tasks that already finished
        tasks_to_run = []
        for agent_info in group:
            agent = agent_info['agent']
            if resume and memory.is_agent_finished(agent.id):
                logger.info(f"Agent {agent.id} already completed; skip")
                continue
            tasks_to_run.append(agent_info)
        
        if not tasks_to_run:
            logger.info(f"All tasks with priority {priority} are complete")
            continue
        
        # Run tasks within the tier concurrently
        async_tasks = []
        for agent_info in tasks_to_run:
            agent = agent_info['agent']
            logger.info(f"  Starting agent {agent.id}")
            async_tasks.append(asyncio.create_task(
                agent.async_run(resume=resume, **agent_info['task_input'])
            ))
            
        
        # Wait for completion
        if async_tasks:
            results = await asyncio.gather(*async_tasks, return_exceptions=True)
            for agent_info, result in zip(tasks_to_run, results):
                agent = agent_info['agent']
                if isinstance(result, Exception):
                    # Format full traceback for better debugging
                    tb_str = ''.join(traceback.format_exception(type(result), result, result.__traceback__))
                    logger.error(f"  Task failed: Agent {agent.id}, error: {result}\n{tb_str}")
                else:
                    logger.info(f"  Task finished: Agent {agent.id}")
        
        logger.info(f"Priority {priority} group finished\n")
    
    # Persist final state
    memory.save()
    logger.info("All tasks completed")
    return True

async def run_experiemnt(resume: bool = True, max_concurrency: int = 3, index_list=None):
    with open("/data00/jiajie_jin/finsight/FinSight/evaluations/deepconsult/queries.csv","r") as f:
        data = f.readlines()
    if index_list is None:
        index_list = range(0,20)
    
    all_query = [item.strip() for item in data][1:]
    
    # limit concurrency of run_report calls
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _bounded_run(query: str, i):
        async with semaphore:
            return await run_report(query=query, save_note=i, resume=resume)

    tasks = [asyncio.create_task(_bounded_run(all_query[idx], idx)) for idx in index_list]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    resume = True
    asyncio.run(run_experiemnt(resume=resume, index_list=list(range(5))))

    # test_query = "Evaluate the potential consequences of TikTok bans on investment risks and analyze how companies can strategically navigate these challenges. Consider how varying degrees of restrictions might impact business operations and explore adaptive measures to mitigate associated risks."
    # asyncio.run(run_report(query=test_query, save_note="0", resume=resume))
