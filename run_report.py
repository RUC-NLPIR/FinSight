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

IF_RESUME = True
MAX_CONCURRENT = 3


async def run_report(resume: bool = True, max_concurrent: int = None):
    """
    Run report generation with optional concurrency limit.
    
    Args:
        resume: Whether to resume from previous state
        max_concurrent: Maximum number of concurrent tasks. If None, uses MAX_CONCURRENT env var or unlimited.
    """
    use_llm_name = os.getenv("DS_MODEL_NAME")
    use_vlm_name = os.getenv("VLM_MODEL_NAME")
    use_embedding_name = os.getenv("EMBEDDING_MODEL_NAME")
    
    # Get max concurrent from parameter, env var, or default to unlimited
    if max_concurrent is None:
        max_concurrent = int(os.getenv("MAX_CONCURRENT", "0")) or None
    config = Config(
        config_file_path='my_config.yaml',
        config_dict={}
    )
    collect_tasks = config.config['custom_collect_tasks']
    analysis_tasks = config.config['custom_analysis_tasks']
    # Initialize memory
    memory = Memory(config=config)
    
    # Initialize logger
    log_dir = os.path.join(config.working_dir, 'logs')
    logger = setup_logger(log_dir=log_dir, log_level=logging.INFO)
    
    # Log concurrency settings
    if max_concurrent:
        logger.info(f"Concurrency limit: {max_concurrent} tasks")
    else:
        logger.info("No concurrency limit (unlimited)")
    
    if resume:
        memory.load()
        logger.info("Memory state loaded")
    
    # Generate additional collect and analysis tasks using LLM if not already generated
    research_query = f"Research target: {config.config['target_name']} (ticker: {config.config['stock_code']}), target type: {config.config.get('target_type', 'company')}"
    
    # Generate collect tasks if not already generated (or if we want fresh tasks)
    if not memory.generated_collect_tasks:
        logger.info("Generating collect tasks using LLM...")
        generated_collect_tasks = await memory.generate_collect_tasks(
            query=research_query,
            use_llm_name=use_llm_name,
            max_num=5,
            existing_tasks=collect_tasks  # Pass existing tasks to avoid duplication
        )
        logger.info(f"Generated {len(generated_collect_tasks)} collect tasks")
    else:
        generated_collect_tasks = memory.generated_collect_tasks
        logger.info(f"Using {len(generated_collect_tasks)} previously generated collect tasks")
    
    # Generate analysis tasks if not already generated
    if not memory.generated_analysis_tasks:
        logger.info("Generating analysis tasks using LLM...")
        generated_analysis_tasks = await memory.generate_analyze_tasks(
            query=research_query,
            use_llm_name=use_llm_name,
            max_num=5,
            existing_tasks=analysis_tasks  # Pass existing tasks to avoid duplication
        )
        logger.info(f"Generated {len(generated_analysis_tasks)} analysis tasks")
    else:
        generated_analysis_tasks = memory.generated_analysis_tasks
        logger.info(f"Using {len(generated_analysis_tasks)} previously generated analysis tasks")
    
    # Merge custom tasks with generated tasks (remove duplicates)
    all_collect_tasks = list(collect_tasks) + [task for task in generated_collect_tasks if task not in collect_tasks]
    all_analysis_tasks = list(analysis_tasks) + [task for task in generated_analysis_tasks if task not in analysis_tasks]
    
    logger.info(f"Total collect tasks: {len(all_collect_tasks)} (custom: {len(collect_tasks)}, generated: {len(generated_collect_tasks)})")
    logger.info(f"Total analysis tasks: {len(all_analysis_tasks)} (custom: {len(analysis_tasks)}, generated: {len(generated_analysis_tasks)})")
    
    # Update the tasks to be used
    collect_tasks = all_collect_tasks
    analysis_tasks = all_analysis_tasks
    # print(memory.task_mapping)
    # mapping = memory.task_mapping
    # for item in mapping:
    #     print(item['agent_id'])
    # assert False
    
    # Prepare prioritized task list (lower value = higher priority)
    tasks_to_run = []
    
    # Data-collection tasks
    for task in collect_tasks:
        tasks_to_run.append({
            'agent_class': DataCollector,
            'task_input': {
                'input_data': {'task': f'Research target: {config.config["target_name"]} (ticker: {config.config["stock_code"]}), task: {task}'},
                'echo': True,
                'max_iterations': 20,
                'resume': resume,
            },
            'agent_kwargs': {
                'use_llm_name': use_llm_name,
            },
            'priority': 1,
        })
    
    # Analysis tasks (run after collection)
    for task in analysis_tasks:
        tasks_to_run.append({
            'agent_class': DataAnalyzer,
            'task_input': {
                'input_data': {
                    'task': f'Research target: {config.config["target_name"]} (ticker: {config.config["stock_code"]})',
                    'analysis_task': task
                },
                'echo': True,
                'max_iterations': 20,
                'resume': resume,
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
                'task': f'Research target: {config.config["target_name"]} (ticker: {config.config["stock_code"]})',
                'task_type': 'company',
            },
            'echo': True,
            'max_iterations': 20,
            'resume': resume,
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
        agent_resume = group[0]['task_input']['resume']
        concurrency_info = f" (max concurrent: {max_concurrent})" if max_concurrent else ""
        logger.info(f"\nExecuting priority {priority} group ({len(group)} task(s){concurrency_info})")
        
        # Skip tasks that already finished
        tasks_to_run = []
        for agent_info in group:
            agent = agent_info['agent']
            if agent_resume and resume and memory.is_agent_finished(agent.id):
                logger.info(f"Agent {agent.id} already completed; skip")
                continue
            tasks_to_run.append(agent_info)
        
        if not tasks_to_run:
            logger.info(f"All tasks with priority {priority} are complete")
            continue
        
        # Run tasks within the tier with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent) if max_concurrent else None
        
        async def run_agent_with_limit(agent_info):
            """Run agent with semaphore limit if configured"""
            agent = agent_info['agent']
            if semaphore:
                async with semaphore:
                    logger.info(f"Starting agent {agent.id}")
                    return await agent.async_run(**agent_info['task_input'])
            else:
                logger.info(f"Starting agent {agent.id}")
                return await agent.async_run(**agent_info['task_input'])
        
        # Create tasks
        async_tasks = []
        for agent_info in tasks_to_run:
            async_tasks.append(asyncio.create_task(
                run_agent_with_limit(agent_info)
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


if __name__ == '__main__':
    asyncio.run(run_report(resume=IF_RESUME, max_concurrent=MAX_CONCURRENT))

