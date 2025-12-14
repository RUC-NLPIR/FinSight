import os
import sys
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Add project root to path
root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)

from src.config import Config
from src.agents import DataCollector, DataAnalyzer, ReportGenerator
from src.memory import Memory
from src.utils import setup_logger, get_logger
import logging


class LLMConfig(BaseModel):
    model_name: str
    api_key: str
    base_url: str
    generation_params: Optional[Dict[str, Any]] = {}


class SystemConfig(BaseModel):
    target_name: str
    stock_code: str
    output_dir: str = "outputs/demo"
    reference_doc_path: Optional[str] = "src/template/report_template.docx"
    outline_template_path: Optional[str] = "src/template/company_outline.md"
    llm_configs: List[LLMConfig]
    ds_model_name: str
    vlm_model_name: str
    embedding_model_name: str


class Task(BaseModel):
    id: str
    type: str  # "collect" or "analyze"
    content: str


class TaskList(BaseModel):
    collect_tasks: List[Task]
    analysis_tasks: List[Task]


class ExecutionRequest(BaseModel):
    resume: bool = False


class AgentStatus(BaseModel):
    agent_id: str
    agent_type: str
    task_content: str
    status: str  # "pending", "running", "completed", "error"
    priority: int
    progress: Optional[str] = ""



class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.agent_logs: Dict[str, List[str]] = defaultdict(list)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send historical logs to new connection
        for agent_id, logs in self.agent_logs.items():
            for log in logs:
                try:
                    await websocket.send_json({
                        "type": "log",
                        "agent_id": agent_id,
                        "message": log,
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    pass

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    def add_log(self, agent_id: str, log_message: str):
        self.agent_logs[agent_id].append(log_message)
    
    def clear_logs(self):
        self.agent_logs.clear()


app = FastAPI(title="FinSight Demo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


manager = ConnectionManager()
current_config: Optional[SystemConfig] = None
current_tasks: TaskList = TaskList(collect_tasks=[], analysis_tasks=[])
execution_state: Dict[str, Any] = {
    "is_running": False,
    "agents": [],
    "current_priority": None
}



class WebSocketLogHandler(logging.Handler):
    def __init__(self, connection_manager: ConnectionManager):
        super().__init__()
        self.manager = connection_manager
    
    def emit(self, record):
        try:
            log_message = self.format(record)
            # Get agent info from record (injected by AgentContextFilter)
            agent_id = getattr(record, 'agent_id', 'system')
            agent_name = getattr(record, 'agent_name', 'system')
            
            # Store log
            self.manager.add_log(agent_id, log_message)
            
            # Broadcast to all connected clients
            asyncio.create_task(self.manager.broadcast({
                "type": "log",
                "agent_id": agent_id,
                "agent_type": agent_name,
                "message": log_message,
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname
            }))
        except Exception:
            self.handleError(record)


# Get the base directory for user configs
USER_CONFIGS_DIR = Path(__file__).parent / "user_configs"
SYSTEM_CONFIGS_DIR = USER_CONFIGS_DIR / "system"
TASKS_CONFIGS_DIR = USER_CONFIGS_DIR / "tasks"
EXECUTION_STATE_DIR = USER_CONFIGS_DIR / "execution"

# Ensure directories exist
SYSTEM_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
TASKS_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
EXECUTION_STATE_DIR.mkdir(parents=True, exist_ok=True)

# File to store last execution state
LAST_EXECUTION_FILE = EXECUTION_STATE_DIR / "last_execution.json"


class ConfigNameRequest(BaseModel):
    name: str


@app.get("/api/config")
async def get_config():
    """Get current system configuration"""
    if current_config is None:
        return {"config": None}
    return {"config": current_config.dict()}


@app.get("/api/config/list")
async def list_configs():
    """List all saved system configurations"""
    configs = []
    for config_file in SYSTEM_CONFIGS_DIR.glob("*.json"):
        config_name = config_file.stem
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            configs.append({
                "name": config_name,
                "target_name": config_data.get("target_name", ""),
                "stock_code": config_data.get("stock_code", ""),
                "modified_time": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
            })
        except Exception as e:
            print(f"Error reading config {config_name}: {e}")
    
    # Sort by modified time, newest first
    configs.sort(key=lambda x: x["modified_time"], reverse=True)
    return {"configs": configs}


@app.post("/api/config")
async def update_config(config: SystemConfig):
    """Update current system configuration (in memory only)"""
    global current_config
    current_config = config
    return {"status": "success", "message": "Configuration updated in memory"}


@app.post("/api/config/save")
async def save_config(request: ConfigNameRequest):
    """Save current configuration with a specific name"""
    if current_config is None:
        raise HTTPException(status_code=400, detail="No configuration to save")
    
    config_file = SYSTEM_CONFIGS_DIR / f"{request.name}.json"
    
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(current_config.dict(), f, indent=2, ensure_ascii=False)
    
    return {"status": "success", "message": f"Configuration saved as '{request.name}'"}


@app.post("/api/config/load")
async def load_config(request: ConfigNameRequest):
    """Load configuration from file by name"""
    global current_config
    
    config_file = SYSTEM_CONFIGS_DIR / f"{request.name}.json"
    if not config_file.exists():
        raise HTTPException(status_code=404, detail=f"Configuration '{request.name}' not found")
    
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    
    current_config = SystemConfig(**config_data)
    return {"status": "success", "config": current_config.dict()}


@app.delete("/api/config/{config_name}")
async def delete_config(config_name: str):
    """Delete a saved configuration"""
    config_file = SYSTEM_CONFIGS_DIR / f"{config_name}.json"
    if not config_file.exists():
        raise HTTPException(status_code=404, detail=f"Configuration '{config_name}' not found")
    
    config_file.unlink()
    return {"status": "success", "message": f"Configuration '{config_name}' deleted"}


@app.get("/api/tasks")
async def get_tasks():
    """Get current task list"""
    return {"tasks": current_tasks.dict()}


@app.get("/api/tasks/list")
async def list_tasks():
    """List all saved task configurations"""
    tasks_list = []
    for tasks_file in TASKS_CONFIGS_DIR.glob("*.json"):
        task_name = tasks_file.stem
        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)
            collect_count = len(tasks_data.get("collect_tasks", []))
            analysis_count = len(tasks_data.get("analysis_tasks", []))
            tasks_list.append({
                "name": task_name,
                "collect_count": collect_count,
                "analysis_count": analysis_count,
                "modified_time": datetime.fromtimestamp(tasks_file.stat().st_mtime).isoformat()
            })
        except Exception as e:
            print(f"Error reading tasks {task_name}: {e}")
    
    # Sort by modified time, newest first
    tasks_list.sort(key=lambda x: x["modified_time"], reverse=True)
    return {"tasks_list": tasks_list}


@app.post("/api/tasks")
async def update_tasks(tasks: TaskList):
    """Update current task list (in memory only)"""
    global current_tasks
    current_tasks = tasks
    return {"status": "success", "message": "Tasks updated in memory"}


@app.post("/api/tasks/save")
async def save_tasks(request: ConfigNameRequest):
    """Save current tasks with a specific name"""
    if current_tasks is None:
        raise HTTPException(status_code=400, detail="No tasks to save")
    
    tasks_file = TASKS_CONFIGS_DIR / f"{request.name}.json"
    
    with open(tasks_file, "w", encoding="utf-8") as f:
        json.dump(current_tasks.dict(), f, indent=2, ensure_ascii=False)
    
    return {"status": "success", "message": f"Tasks saved as '{request.name}'"}


@app.post("/api/tasks/load")
async def load_tasks(request: ConfigNameRequest):
    """Load tasks from file by name"""
    global current_tasks
    
    tasks_file = TASKS_CONFIGS_DIR / f"{request.name}.json"
    if not tasks_file.exists():
        raise HTTPException(status_code=404, detail=f"Tasks '{request.name}' not found")
    
    with open(tasks_file, "r", encoding="utf-8") as f:
        tasks_data = json.load(f)
    
    current_tasks = TaskList(**tasks_data)
    return {"status": "success", "tasks": current_tasks.dict()}


@app.delete("/api/tasks/{task_name}")
async def delete_tasks(task_name: str):
    """Delete a saved task configuration"""
    tasks_file = TASKS_CONFIGS_DIR / f"{task_name}.json"
    if not tasks_file.exists():
        raise HTTPException(status_code=404, detail=f"Tasks '{task_name}' not found")
    
    tasks_file.unlink()
    return {"status": "success", "message": f"Tasks '{task_name}' deleted"}


@app.get("/api/execution/status")
async def get_execution_status():
    """Get current execution status"""
    return {
        "is_running": execution_state["is_running"],
        "agents": execution_state["agents"],
        "current_priority": execution_state["current_priority"]
    }


def save_execution_state():
    """Save current config and tasks for resume functionality"""
    if current_config is None or current_tasks is None:
        return
    
    state = {
        "config": current_config.dict(),
        "tasks": current_tasks.dict(),
        "timestamp": datetime.now().isoformat()
    }
    
    with open(LAST_EXECUTION_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_execution_state() -> bool:
    """Load last execution state for resume. Returns True if successful."""
    global current_config, current_tasks
    
    if not LAST_EXECUTION_FILE.exists():
        return False
    
    try:
        with open(LAST_EXECUTION_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        current_config = SystemConfig(**state["config"])
        current_tasks = TaskList(**state["tasks"])
        return True
    except Exception as e:
        print(f"Failed to load execution state: {e}")
        return False


@app.get("/api/execution/last")
async def get_last_execution():
    """Get information about the last execution for resume"""
    if not LAST_EXECUTION_FILE.exists():
        return {"has_last_execution": False}
    
    try:
        with open(LAST_EXECUTION_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        return {
            "has_last_execution": True,
            "target_name": state["config"].get("target_name", ""),
            "timestamp": state.get("timestamp", ""),
            "collect_count": len(state["tasks"].get("collect_tasks", [])),
            "analysis_count": len(state["tasks"].get("analysis_tasks", []))
        }
    except Exception:
        return {"has_last_execution": False}


@app.post("/api/execution/start")
async def start_execution(request: ExecutionRequest, background_tasks: BackgroundTasks):
    """Start the report generation process"""
    global current_config, current_tasks
    
    if execution_state["is_running"]:
        raise HTTPException(status_code=400, detail="Execution already in progress")
    
    # For resume, try to load last execution state if current config is empty
    if request.resume:
        if current_config is None or (len(current_tasks.collect_tasks) == 0 and len(current_tasks.analysis_tasks) == 0):
            if not load_execution_state():
                raise HTTPException(status_code=400, detail="No previous execution state found. Please configure and run first.")
    
    if current_config is None:
        raise HTTPException(status_code=400, detail="Configuration not set")
    
    if len(current_tasks.collect_tasks) == 0 and len(current_tasks.analysis_tasks) == 0:
        raise HTTPException(status_code=400, detail="No tasks configured")
    
    # Save current state for future resume
    save_execution_state()
    
    # Reset state
    execution_state["is_running"] = True
    execution_state["agents"] = []
    execution_state["current_priority"] = None
    manager.clear_logs()
    
    # Start execution in background
    background_tasks.add_task(run_report_generation, request.resume)
    
    return {"status": "success", "message": "Execution started"}


@app.post("/api/execution/stop")
async def stop_execution():
    """Stop the report generation process"""
    execution_state["is_running"] = False
    return {"status": "success", "message": "Execution stop requested"}


@app.get("/api/reports")
async def list_reports():
    """List all generated reports"""
    reports = []
    
    # Get the base output directory from config or use default
    if current_config:
        output_base = Path(current_config.output_dir)
    else:
        output_base = Path("outputs/demo-fastapi")
    
    if not output_base.is_absolute():
        output_base = Path(__file__).parent / output_base
    
    if not output_base.exists():
        return {"reports": []}
    
    # Search for report files in all subdirectories
    for target_dir in output_base.iterdir():
        if not target_dir.is_dir():
            continue
        
        target_name = target_dir.name
        
        # Find docx and pdf files
        for report_file in target_dir.glob("*.docx"):
            reports.append({
                "id": f"{target_name}/{report_file.name}",
                "target_name": target_name,
                "filename": report_file.name,
                "type": "docx",
                "path": str(report_file),
                "size": report_file.stat().st_size,
                "modified_time": datetime.fromtimestamp(report_file.stat().st_mtime).isoformat()
            })
        
        for report_file in target_dir.glob("*.pdf"):
            reports.append({
                "id": f"{target_name}/{report_file.name}",
                "target_name": target_name,
                "filename": report_file.name,
                "type": "pdf",
                "path": str(report_file),
                "size": report_file.stat().st_size,
                "modified_time": datetime.fromtimestamp(report_file.stat().st_mtime).isoformat()
            })
        
        for report_file in target_dir.glob("*.md"):
            # Skip outline templates
            if "outline" in report_file.name.lower():
                continue
            reports.append({
                "id": f"{target_name}/{report_file.name}",
                "target_name": target_name,
                "filename": report_file.name,
                "type": "md",
                "path": str(report_file),
                "size": report_file.stat().st_size,
                "modified_time": datetime.fromtimestamp(report_file.stat().st_mtime).isoformat()
            })
    
    # Sort by modified time, newest first
    reports.sort(key=lambda x: x["modified_time"], reverse=True)
    return {"reports": reports}


@app.get("/api/reports/download/{target_name}/{filename}")
async def download_report(target_name: str, filename: str):
    """Download a specific report file"""
    # Get the base output directory
    if current_config:
        output_base = Path(current_config.output_dir)
    else:
        output_base = Path("outputs/demo-fastapi")
    
    # Handle relative paths
    if not output_base.is_absolute():
        output_base = Path(__file__).parent / output_base
    
    file_path = output_base / target_name / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Determine media type
    suffix = file_path.suffix.lower()
    media_types = {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pdf": "application/pdf",
        ".md": "text/markdown"
    }
    media_type = media_types.get(suffix, "application/octet-stream")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )


@app.get("/api/reports/preview/{target_name}/{filename}")
async def preview_report(target_name: str, filename: str):
    """Get markdown report content for preview"""
    # Get the base output directory
    if current_config:
        output_base = Path(current_config.output_dir)
    else:
        output_base = Path("outputs/demo-fastapi")
    
    # Handle relative paths
    if not output_base.is_absolute():
        output_base = Path(__file__).parent / output_base
    
    file_path = output_base / target_name / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Only markdown files can be previewed")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    return {"content": content, "filename": filename}


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive client messages if any
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_json({"type": "heartbeat", "message": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def run_report_generation(resume: bool = False):
    """Main report generation logic"""
    try:
        # Prepare config
        config_dict = {
            "output_dir": current_config.output_dir,
            "target_name": current_config.target_name,
            "target_type": "financial_company",
            "stock_code": current_config.stock_code,
            "reference_doc_path": current_config.reference_doc_path,
            "outline_template_path": current_config.outline_template_path,
            "llm_config_list": [
                {
                    "model_name": llm.model_name,
                    "api_key": llm.api_key,
                    "base_url": llm.base_url,
                    "generation_params": llm.generation_params or {}
                }
                for llm in current_config.llm_configs
            ]
        }
        
        config = Config(config_dict=config_dict)
        memory = Memory(config=config)
        
        # Setup logger with WebSocket handler
        log_dir = os.path.join(config.working_dir, 'logs')
        logger = setup_logger(log_dir=log_dir, log_level=logging.INFO)
        
        # Add WebSocket handler for real-time log broadcasting
        ws_handler = WebSocketLogHandler(manager)
        ws_handler.setLevel(logging.INFO)
        
        # Add formatter and filter to match the standard logger format
        from src.utils.logger import AgentContextFilter
        ws_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(agent_name)s:%(agent_id)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        ws_handler.setFormatter(ws_formatter)
        ws_handler.addFilter(AgentContextFilter())
        
        logger.addHandler(ws_handler)
        
        if resume:
            memory.load()
            logger.info("Memory state loaded")
        
        # Broadcast start event
        await manager.broadcast({
            "type": "execution_start",
            "timestamp": datetime.now().isoformat()
        })
        
        # Prepare task list
        tasks_to_run = []
        
        # Data collection tasks
        for task in current_tasks.collect_tasks:
            tasks_to_run.append({
                'agent_class': DataCollector,
                'task_input': {
                    'input_data': {
                        'task': f'Research target: {current_config.target_name} (ticker: {current_config.stock_code}), task: {task.content}'
                    },
                    'echo': True,
                    'max_iterations': 5,
                },
                'agent_kwargs': {
                    'use_llm_name': current_config.ds_model_name,
                },
                'priority': 1,
                'task_id': task.id,
                'task_content': task.content,
            })
        
        # Analysis tasks
        for task in current_tasks.analysis_tasks:
            tasks_to_run.append({
                'agent_class': DataAnalyzer,
                'task_input': {
                    'input_data': {
                        'task': f'Research target: {current_config.target_name} (ticker: {current_config.stock_code})',
                        'analysis_task': task.content
                    },
                    'echo': True,
                    'max_iterations': 5,
                },
                'agent_kwargs': {
                    'use_llm_name': current_config.ds_model_name,
                    'use_vlm_name': current_config.vlm_model_name,
                    'use_embedding_name': current_config.embedding_model_name,
                },
                'priority': 2,
                'task_id': task.id,
                'task_content': task.content,
            })
        
        # Report generation task
        tasks_to_run.append({
            'agent_class': ReportGenerator,
            'task_input': {
                'input_data': {
                    'task': f'Research target: {current_config.target_name} (ticker: {current_config.stock_code})',
                    'task_type': 'company',
                },
                'echo': True,
                'max_iterations': 5,
            },
            'agent_kwargs': {
                'use_llm_name': current_config.ds_model_name,
                'use_embedding_name': current_config.embedding_model_name,
            },
            'priority': 3,
            'task_id': 'report_generation',
            'task_content': 'Final Report Generation',
        })
        
        # Create agents
        agents_info = []
        for task_info in tasks_to_run:
            agent = await memory.get_or_create_agent(
                agent_class=task_info['agent_class'],
                task_input=task_info['task_input'],
                resume=resume,
                priority=task_info['priority'],
                **task_info['agent_kwargs']
            )
            
            actual_priority = task_info['priority']
            for saved_task in memory.task_mapping:
                if saved_task.get('agent_id') == agent.id:
                    actual_priority = saved_task.get('priority', task_info['priority'])
                    break
            
            agent_status = AgentStatus(
                agent_id=agent.id,
                agent_type=agent.AGENT_NAME,
                task_content=task_info['task_content'],
                status="pending",
                priority=actual_priority
            )
            
            agents_info.append({
                'agent': agent,
                'task_input': task_info['task_input'],
                'priority': actual_priority,
                'task_id': task_info['task_id'],
                'status': agent_status
            })
            
            execution_state["agents"].append(agent_status.dict())
        
        # Broadcast initial agent list
        await manager.broadcast({
            "type": "agents_initialized",
            "agents": execution_state["agents"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Execute by priority
        agents_info.sort(key=lambda x: x['priority'])
        priority_groups = defaultdict(list)
        for agent_info in agents_info:
            priority_groups[agent_info['priority']].append(agent_info)
        
        sorted_priorities = sorted(priority_groups.keys())
        
        for priority in sorted_priorities:
            if not execution_state["is_running"]:
                logger.info("Execution stopped by user")
                break
            
            execution_state["current_priority"] = priority
            group = priority_groups[priority]
            logger.info(f"Executing priority {priority} group ({len(group)} task(s))")
            
            await manager.broadcast({
                "type": "priority_start",
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            })
            
            # Skip completed tasks
            tasks_to_run_now = []
            for agent_info in group:
                agent = agent_info['agent']
                if resume and memory.is_agent_finished(agent.id):
                    logger.info(f"Agent {agent.id} already completed; skip")
                    agent_info['status'].status = "completed"
                    await update_agent_status(agent_info['status'])
                    continue
                tasks_to_run_now.append(agent_info)
            
            if not tasks_to_run_now:
                logger.info(f"All tasks with priority {priority} are complete")
                continue
            
            # Run tasks concurrently
            async_tasks = []
            for agent_info in tasks_to_run_now:
                agent = agent_info['agent']
                agent_info['status'].status = "running"
                await update_agent_status(agent_info['status'])
                
                logger.info(f"Starting agent {agent.id}")
                async_tasks.append(asyncio.create_task(
                    agent.async_run(resume=resume, **agent_info['task_input'])
                ))
            
            # Wait for completion
            if async_tasks:
                results = await asyncio.gather(*async_tasks, return_exceptions=True)
                for agent_info, result in zip(tasks_to_run_now, results):
                    agent = agent_info['agent']
                    if isinstance(result, Exception):
                        logger.error(f"Task failed: Agent {agent.id}, error: {result}")
                        agent_info['status'].status = "error"
                        agent_info['status'].progress = str(result)
                    else:
                        logger.info(f"Task finished: Agent {agent.id}")
                        agent_info['status'].status = "completed"
                    
                    await update_agent_status(agent_info['status'])
            
            logger.info(f"Priority {priority} group finished")
            await manager.broadcast({
                "type": "priority_complete",
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            })
        
        # Save final state
        memory.save()
        logger.info("All tasks completed")
        
        execution_state["is_running"] = False
        execution_state["current_priority"] = None
        
        await manager.broadcast({
            "type": "execution_complete",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Execution error: {e}", exc_info=True)
        execution_state["is_running"] = False
        await manager.broadcast({
            "type": "execution_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })


async def update_agent_status(status: AgentStatus):
    """Update agent status and broadcast to clients"""
    # Update in execution state
    for agent in execution_state["agents"]:
        if agent["agent_id"] == status.agent_id:
            agent["status"] = status.status
            agent["progress"] = status.progress
            break
    
    # Broadcast update
    await manager.broadcast({
        "type": "agent_status_update",
        "agent": status.dict(),
        "timestamp": datetime.now().isoformat()
    })


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

