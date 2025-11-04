import os
import json
import re
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import traceback

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

from pathlib import Path
import pandas as pd
from sklearn.pipeline import Pipeline

from .ML.transformers import initial_process, drop_sparse_columns, drop_sparse_rows
from .sub_agents.feasibility_check import feasibility_check_agent
from .sub_agents.feature_engineering import feature_engineering_agent
from .sub_agents.drop_feature_dups import drop_feature_dups_agent
from .sub_agents.find_regression_kpi import find_regression_kpi_agent
from .sub_agents.find_classification_kpi import find_classification_kpi_agent

from .tools import (
    extract_tool_calls,
    agent_process,
    websocket_sender,
    listen_for_user_input,
    post_process
)

from .models import (
    FirstAgentDependencies,
    AgentDependencies,
    TaskSpecs,
    HealthStatus,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# Application configuration
LOG_LEVEL = os.getenv("LOG_LEVEL")
DEBUG = os.getenv("DEBUG")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set debug level for our module during development
if DEBUG == "true":
    logger.setLevel(logging.DEBUG)


# Create FastAPI app
app = FastAPI(
    title="Agentic autoML",
    description="training a tabular data prediction ml modelwith an agent",
    version="0.1.0",
    # lifespan=lifespan # create it if databases exist
)

# Add middleware with flexible CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# API Endpoints
@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    try:
        return HealthStatus(
            status='healthy',
            llm_connection=True,  # Assume OK if we can respond
            version="0.1.0",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Health check failed")


@app.websocket("/feasibility_check/ws")  # 👈 WebSocket endpoint
async def feasibility_check_ws(websocket: WebSocket):
    await websocket.accept()  # 👈 accept the WebSocket connection

    try:
        # load task_specs
        task_specs_path = Path(__file__).resolve().parents[1] / "task" / "task_specs.json"
        with open(task_specs_path, "r", encoding="utf-8") as f:
            task_specs = json.load(f)

        task_specs = TaskSpecs(**task_specs)

        deps = FirstAgentDependencies(
            task_specs=task_specs,
            user_reply_queue=asyncio.Queue(),
            send_queue=asyncio.Queue()
        )

        full_prompt = task_specs.overview

        input_task = asyncio.create_task(listen_for_user_input(websocket, deps))
        sender_task = asyncio.create_task(websocket_sender(websocket, deps))
                        
        # Stream using agent.iter() pattern
        async with feasibility_check_agent.iter(full_prompt, deps=deps) as run:
            await agent_process(run, feasibility_check_agent, send_func=deps.send_func)

        # terminate the tasks
        await deps.send_queue.put({"type": "end-of-queue"})
        input_task.cancel()
        await asyncio.gather(input_task, sender_task, return_exceptions=True)
        
        # Extract tools used from the final result
        result = run.result
        tools_used = extract_tool_calls(result)

        agent_result_str = result.output  # string returned by the LLM
        agent_result = post_process(agent_result_str)

        # if we needed to extract task_specs from deps (for example because it was changed in the agent process):
        task_specs = run.ctx.deps.user_deps.task_specs.model_dump()

        task_specs_processed=task_specs.copy()

        task_specs_processed['overview'] = {
            'original': task_specs_processed['overview'],
            'refined': agent_result["refined_overview"],
            'is_feasible': agent_result["is_feasible"],
            'decision_rationale': agent_result["decision_rationale"],
            'task_type': agent_result["task_type"],
        }

        task_specs_processed['target']['description'] = agent_result["target_description"]
        
        # save task_specs_processed
        task_specs_processed_path = Path(__file__).resolve().parents[1] / "task" / "task_specs_processed.json"
        with open(task_specs_processed_path, "w", encoding="utf-8") as f:
            json.dump(task_specs_processed, f, indent=4, ensure_ascii=False)

        if tools_used:
            tools_data = [
                {
                    "tool_name": tool.tool_name, 
                    "args": tool.args, 
                    "tool_call_id": tool.tool_call_id
                }
                for tool in tools_used
            ]
            await websocket.send_json({"type": "tools", "content": tools_data})

        # Signal end of stream
        await websocket.send_json({"type": "end"})

        await websocket.close()

    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected cleanly.")

    except Exception as e:
        logger.error(f"⚠️ WebSocket error: {e}")
        traceback.print_exc()
        try:
            # Only attempt to send if still open
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.send_json({"type": "error", "content": str(e)})
        except Exception as send_err:
            logger.warning(f"Could not send error message: {send_err}")

    finally:
        logger.info("✅ WebSocket session ended.")


@app.websocket("/find_kpi/ws")  # 👈 WebSocket endpoint
async def find_kpi_ws(websocket: WebSocket):
    await websocket.accept()  # 👈 accept the WebSocket connection

    try:
        # load task_specs
        task_specs_processed_path = Path(__file__).resolve().parents[1] / "task" / "task_specs_processed.json"
        with open(task_specs_processed_path, "r", encoding="utf-8") as f:
            task_specs_processed = json.load(f)

        deps = AgentDependencies(
            user_reply_queue=asyncio.Queue(),
            send_queue=asyncio.Queue()
        )

        task_type = task_specs_processed['overview']['task_type']
        agent = find_regression_kpi_agent if task_type == 'Regression' else find_classification_kpi_agent

        full_prompt = task_specs_processed['overview']['refined']

        input_task = asyncio.create_task(listen_for_user_input(websocket, deps))
        sender_task = asyncio.create_task(websocket_sender(websocket, deps))
                        
        # Stream using agent.iter() pattern
        async with agent.iter(full_prompt, deps=deps) as run:
            await agent_process(run, agent, send_func=deps.send_func)

        # terminate the tasks
        await deps.send_queue.put({"type": "end-of-queue"})
        input_task.cancel()
        await asyncio.gather(input_task, sender_task, return_exceptions=True)
        
        # Extract tools used from the final result
        result = run.result
        tools_used = extract_tool_calls(result)

        agent_result_str = result.output  # string returned by the LLM
        agent_result = post_process(agent_result_str)

        task_specs_processed['overview']['kpi'] = agent_result['chosen_metric']

        # save task_specs_processed
        with open(task_specs_processed_path, "w", encoding="utf-8") as f:
            json.dump(task_specs_processed, f, indent=4, ensure_ascii=False)

        if tools_used:
            tools_data = [
                {
                    "tool_name": tool.tool_name, 
                    "args": tool.args, 
                    "tool_call_id": tool.tool_call_id
                }
                for tool in tools_used
            ]
            await websocket.send_json({"type": "tools", "content": tools_data})

        # Signal end of stream
        await websocket.send_json({"type": "end"})

        await websocket.close()

    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected cleanly.")

    except Exception as e:
        logger.error(f"⚠️ WebSocket error: {e}")
        traceback.print_exc()
        try:
            # Only attempt to send if still open
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.send_json({"type": "error", "content": str(e)})
        except Exception as send_err:
            logger.warning(f"Could not send error message: {send_err}")

    finally:
        logger.info("✅ WebSocket session ended.")


@app.websocket("/feature_engineering/ws")  # 👈 WebSocket endpoint
async def feature_engineering_ws(websocket: WebSocket):
    await websocket.accept()  # 👈 accept the WebSocket connection

    try:
        # extract feature name
        # init_message = await websocket.receive_text()
        # request_data = json.loads(init_message)

        # # Now you can access request_data like a dict
        # feature_name = request_data.get("feature_name")

        # load task_specs
        task_specs_processed_path = Path(__file__).resolve().parents[1] / "task" / "task_specs_processed.json"
        with open(task_specs_processed_path, "r", encoding="utf-8") as f:
            task_specs_processed = json.load(f)

        target_description = task_specs_processed['target']['description']

        deps = AgentDependencies(
            user_reply_queue=asyncio.Queue(),
            send_queue=asyncio.Queue()
        )

        for feature_name in task_specs_processed['features']:
            feature_description = task_specs_processed['features'][feature_name]

            input_dict = {
                "feature_name": feature_name,
                "feature_description": feature_description,
                "target_description": target_description
            }

            full_prompt = json.dumps(input_dict, indent=2)

            input_task = asyncio.create_task(listen_for_user_input(websocket, deps))
            sender_task = asyncio.create_task(websocket_sender(websocket, deps))
                            
            # Stream using agent.iter() pattern
            async with feature_engineering_agent.iter(full_prompt, deps=deps) as run:
                await agent_process(run, feature_engineering_agent, send_func=deps.send_func)

            # terminate the tasks
            await deps.send_queue.put({"type": "end-of-queue"})
            input_task.cancel()
            await asyncio.gather(input_task, sender_task, return_exceptions=True)
            
            # Extract tools used from the final result
            result = run.result
            tools_used = extract_tool_calls(result)

            agent_result_str = result.output  # string returned by the LLM
            agent_result = post_process(agent_result_str)

            task_specs_processed['features'][feature_name] = {
                'original': task_specs_processed['features'][feature_name],
                'refined': agent_result["refined_description"],
                'feature_type': agent_result["feature_type"],
                'engineering_type': agent_result["feature_engineering_type"],
                'decision_rationale': agent_result["decision_rationale"],
            }

            # save task_specs_processed
            with open(task_specs_processed_path, "w", encoding="utf-8") as f:
                json.dump(task_specs_processed, f, indent=4, ensure_ascii=False)

            if tools_used:
                tools_data = [
                    {
                        "tool_name": tool.tool_name, 
                        "args": tool.args, 
                        "tool_call_id": tool.tool_call_id
                    }
                    for tool in tools_used
                ]
                await websocket.send_json({"type": "tools", "content": tools_data})

        # Signal end of stream
        await websocket.send_json({"type": "end"})

        await websocket.close()

    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected cleanly.")

    except Exception as e:
        logger.error(f"⚠️ WebSocket error: {e}")
        traceback.print_exc()
        try:
            # Only attempt to send if still open
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.send_json({"type": "error", "content": str(e)})
        except Exception as send_err:
            logger.warning(f"Could not send error message: {send_err}")

    finally:
        logger.info("✅ WebSocket session ended.")


@app.websocket("/drop_feature_dups/ws")  # 👈 WebSocket endpoint
async def drop_feature_dups_ws(websocket: WebSocket):
    await websocket.accept()  # 👈 accept the WebSocket connection

    try:
        # load task_specs
        task_specs_processed_path = Path(__file__).resolve().parents[1] / "task" / "task_specs_processed.json"
        with open(task_specs_processed_path, "r", encoding="utf-8") as f:
            task_specs_processed = json.load(f)

        deps = AgentDependencies(
            user_reply_queue=asyncio.Queue(),
            send_queue=asyncio.Queue()
        )

        input_dict = {
            "target_description": task_specs_processed['target']['description'],
            "features": {
                feature_name: task_specs_processed['features'][feature_name]['refined']
                for feature_name in task_specs_processed['features'] 
                if task_specs_processed['features'][feature_name]['feature_type'] != 'Unnecessary'
            }
        }

        full_prompt = json.dumps(input_dict, indent=2)

        input_task = asyncio.create_task(listen_for_user_input(websocket, deps))
        sender_task = asyncio.create_task(websocket_sender(websocket, deps))
                        
        # Stream using agent.iter() pattern
        async with drop_feature_dups_agent.iter(full_prompt, deps=deps) as run:
            await agent_process(run, drop_feature_dups_agent, send_func=deps.send_func)

        # terminate the tasks
        await deps.send_queue.put({"type": "end-of-queue"})
        input_task.cancel()
        await asyncio.gather(input_task, sender_task, return_exceptions=True)
        
        # Extract tools used from the final result
        result = run.result
        tools_used = extract_tool_calls(result)

        agent_result_str = result.output  # string returned by the LLM
        agent_result = post_process(agent_result_str)

        for feature in agent_result:
            task_specs_processed['features'][feature]['feature_type'] = 'Duplicate'
            task_specs_processed['features'][feature]['duplicate_of'] = agent_result[feature]

        # save task_specs_processed
        with open(task_specs_processed_path, "w", encoding="utf-8") as f:
            json.dump(task_specs_processed, f, indent=4, ensure_ascii=False)

        if tools_used:
            tools_data = [
                {
                    "tool_name": tool.tool_name, 
                    "args": tool.args, 
                    "tool_call_id": tool.tool_call_id
                }
                for tool in tools_used
            ]
            await websocket.send_json({"type": "tools", "content": tools_data})

        # Signal end of stream
        await websocket.send_json({"type": "end"})

        await websocket.close()

    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected cleanly.")

    except Exception as e:
        logger.error(f"⚠️ WebSocket error: {e}")
        traceback.print_exc()
        try:
            # Only attempt to send if still open
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.send_json({"type": "error", "content": str(e)})
        except Exception as send_err:
            logger.warning(f"Could not send error message: {send_err}")

    finally:
        logger.info("✅ WebSocket session ended.")


@app.websocket("/all_agents/ws")  # 👈 WebSocket endpoint
async def all_agents_ws(websocket: WebSocket):
    await websocket.accept()  # 👈 accept the WebSocket connection

    try:
        # load task_specs
        task_specs_path = Path(__file__).resolve().parents[1] / "task" / "task_specs.json"
        with open(task_specs_path, "r", encoding="utf-8") as f:
            task_specs = json.load(f)

        task_specs = TaskSpecs(**task_specs)
        task_specs_processed=task_specs.model_dump().copy()

        deps = AgentDependencies(
            user_reply_queue=asyncio.Queue(),
            send_queue=asyncio.Queue()
        )

        ################# 1. feasibility check:
        await deps.send_func({
            "type": "agent-start",
            "content": "feasibility check"
        })

        full_prompt = task_specs_processed['overview']

        input_task = asyncio.create_task(listen_for_user_input(websocket, deps))
        sender_task = asyncio.create_task(websocket_sender(websocket, deps))
                        
        # Stream using agent.iter() pattern
        async with feasibility_check_agent.iter(full_prompt, deps=deps) as run:
            await agent_process(run, feasibility_check_agent, send_func=deps.send_func)

        # Extract tools used from the final result
        result = run.result
        tools_used = extract_tool_calls(result)

        agent_result_str = result.output  # string returned by the LLM
        agent_result = post_process(agent_result_str)        

        task_specs_processed['overview'] = {
            'original': task_specs_processed['overview'],
            'refined': agent_result["refined_overview"],
            'is_feasible': agent_result["is_feasible"],
            'decision_rationale': agent_result["decision_rationale"],
            'task_type': agent_result["task_type"]
        }

        task_specs_processed['target']['description'] = agent_result["target_description"]

        if tools_used:
            tools_data = [
                {
                    "tool_name": tool.tool_name, 
                    "args": tool.args, 
                    "tool_call_id": tool.tool_call_id
                }
                for tool in tools_used
            ]
            await deps.send_func({
                "type": "tools",
                "content": tools_data
            })


        ################# 2. find kpi:
        await deps.send_func({
            "type": "agent-start",
            "content": "find kpi"
        })

        task_type = task_specs_processed['overview']['task_type']
        agent = find_regression_kpi_agent if task_type == 'Regression' else find_classification_kpi_agent
        full_prompt = task_specs_processed['overview']['refined']

        async with agent.iter(full_prompt, deps=deps) as run:
            await agent_process(run, agent, send_func=deps.send_func)

        result = run.result
        tools_used = extract_tool_calls(result)

        agent_result_str = result.output  # string returned by the LLM
        agent_result = post_process(agent_result_str)

        task_specs_processed['overview']['kpi'] = agent_result['chosen_metric']

        if tools_used:
            tools_data = [
                {
                    "tool_name": tool.tool_name, 
                    "args": tool.args, 
                    "tool_call_id": tool.tool_call_id
                }
                for tool in tools_used
            ]
            await deps.send_func({
                "type": "tools",
                "content": tools_data
            })


        ################# 3. feature engineering:
        await deps.send_func({
            "type": "agent-start",
            "content": "feature engineering"
        })

        target_description = task_specs_processed['target']['description']

        for feature_name in task_specs_processed['features']:
            feature_description = task_specs_processed['features'][feature_name]

            input_dict = {
                "feature_name": feature_name,
                "feature_description": feature_description,
                "target_description": target_description
            }

            full_prompt = json.dumps(input_dict, indent=2)
                            
            # Stream using agent.iter() pattern
            async with feature_engineering_agent.iter(full_prompt, deps=deps) as run:
                await agent_process(run, feature_engineering_agent, send_func=deps.send_func)
            
            # Extract tools used from the final result
            result = run.result
            tools_used = extract_tool_calls(result)

            agent_result_str = result.output  # string returned by the LLM
            agent_result = post_process(agent_result_str)

            task_specs_processed['features'][feature_name] = {
                'original': task_specs_processed['features'][feature_name],
                'refined': agent_result["refined_description"],
                'feature_type': agent_result["feature_type"],
                'engineering_type': agent_result["feature_engineering_type"],
                'decision_rationale': agent_result["decision_rationale"],
            }

            if tools_used:
                tools_data = [
                    {
                        "tool_name": tool.tool_name, 
                        "args": tool.args, 
                        "tool_call_id": tool.tool_call_id
                    }
                    for tool in tools_used
                ]
                await deps.send_func({
                    "type": "tools",
                    "content": tools_data
                })


        ################# 4. drop feature dups:
        await deps.send_func({
            "type": "agent-start",
            "content": "drop feature dups"
        })

        input_dict = {
            "target_description": task_specs_processed['target']['description'],
            "features": {
                feature_name: task_specs_processed['features'][feature_name]['refined']
                for feature_name in task_specs_processed['features'] 
                if task_specs_processed['features'][feature_name]['feature_type'] != 'Unnecessary'
            }
        }

        full_prompt = json.dumps(input_dict, indent=2)

        async with drop_feature_dups_agent.iter(full_prompt, deps=deps) as run:
            await agent_process(run, drop_feature_dups_agent, send_func=deps.send_func)

        result = run.result
        tools_used = extract_tool_calls(result)

        agent_result_str = result.output  # string returned by the LLM
        agent_result = post_process(agent_result_str)

        for feature in agent_result:
            task_specs_processed['features'][feature]['feature_type'] = 'Duplicate'
            task_specs_processed['features'][feature]['duplicate_of'] = agent_result[feature]

        if tools_used:
            tools_data = [
                {
                    "tool_name": tool.tool_name, 
                    "args": tool.args, 
                    "tool_call_id": tool.tool_call_id
                }
                for tool in tools_used
            ]
            await deps.send_func({
                "type": "tools",
                "content": tools_data
            })

        ########################## finales
        # terminate the tasks
        await deps.send_queue.put({"type": "end-of-queue"})
        input_task.cancel()
        await asyncio.gather(input_task, sender_task, return_exceptions=True)

        # save task_specs_processed
        task_specs_processed_path = Path(__file__).resolve().parents[1] / "task" / "task_specs_processed.json"
        with open(task_specs_processed_path, "w", encoding="utf-8") as f:
            json.dump(task_specs_processed, f, indent=4, ensure_ascii=False)

        # Signal end of stream
        await websocket.send_json({"type": "end"})

        await websocket.close()

    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected cleanly.")

    except Exception as e:
        logger.error(f"⚠️ WebSocket error: {e}")
        traceback.print_exc()
        try:
            # Only attempt to send if still open
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.send_json({"type": "error", "content": str(e)})
        except Exception as send_err:
            logger.warning(f"Could not send error message: {send_err}")

    finally:
        logger.info("✅ WebSocket session ended.")


@app.websocket("/pipeline/ws")  # 👈 WebSocket endpoint
async def pipeline_ws(websocket: WebSocket):
    await websocket.accept()  # 👈 accept the WebSocket connection

    try:
        # load task_specs
        task_specs_processed_path = Path(__file__).resolve().parents[1] / "task" / "task_specs_processed.json"
        with open(task_specs_processed_path, "r", encoding="utf-8") as f:
            task_specs_processed = json.load(f)

        # === 1️⃣ Load the dataset ===
        csv_path = Path(__file__).resolve().parents[1] / "task" / "dataset.csv"
        df = pd.read_csv(csv_path)
        # df = df.head(5)
        # print(df)

        # === 2️⃣ Separate features and target ===
        target_col = task_specs_processed['target']['field_name']
        y = df[target_col]
        X = df.drop(columns=[target_col])

        # === 3️⃣ Initialize and apply the transformer ===
        features_metadata = {
            feature_name: {"feature_type": task_specs_processed['features'][feature_name]['feature_type']}
            for feature_name in task_specs_processed['features']
        }

        pipeline = Pipeline([
            ("initial_process", initial_process(features_metadata)),
            ("drop_sparse_columns", drop_sparse_columns(task_specs_processed)),
            ("drop_sparse_rows", drop_sparse_rows(task_specs_processed))
        ])

        X_transformed = pipeline.fit_transform(X, y)

        # === 4️⃣ (Optional) View result ===
        print("Original shape:", X.shape)
        print("Transformed shape:", X_transformed.shape)
        # print(X_transformed)

        ############################


        # Signal end of stream
        await websocket.send_json({"type": "end"})

        await websocket.close()

    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected cleanly.")

    except Exception as e:
        logger.error(f"⚠️ WebSocket error: {e}")
        traceback.print_exc()
        try:
            # Only attempt to send if still open
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.send_json({"type": "error", "content": str(e)})
        except Exception as send_err:
            logger.warning(f"Could not send error message: {send_err}")

    finally:
        logger.info("✅ WebSocket session ended.")


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    
    return ErrorResponse(
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=str(uuid.uuid4())
    )