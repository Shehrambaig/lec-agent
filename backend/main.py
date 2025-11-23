from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import json
from datetime import datetime
import uuid

from backend.state import ResearchState, HumanFeedback
from backend.graph import research_graph
from langgraph.checkpoint.memory import MemorySaver


app = FastAPI(title="Lecture Assistant Agent API")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections and execution states
active_connections: Dict[str, WebSocket] = {}
execution_states: Dict[str, Dict[str, Any]] = {}


class StartResearchRequest(BaseModel):
    topic: str
    user_id: str = "default_user"


class HumanFeedbackRequest(BaseModel):
    session_id: str
    checkpoint_type: str
    decision: str
    comments: Optional[str] = None
    emphasis_areas: Optional[list[str]] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Lecture Assistant Agent",
        "version": "1.0.0"
    }


@app.post("/research/start")
async def start_research(request: StartResearchRequest):
    """
    Start a new research workflow.
    Returns a session_id for tracking.
    """
    session_id = str(uuid.uuid4())

    # Initialize state
    initial_state = ResearchState(
        topic=request.topic,
        user_id=request.user_id
    )

    # Store execution context
    execution_states[session_id] = {
        "state": initial_state,
        "status": "initialized",
        "thread_id": session_id,
        "checkpoint": None
    }

    return {
        "session_id": session_id,
        "topic": request.topic,
        "status": "initialized",
        "message": "Research session created. Connect via WebSocket to start execution."
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket

    def json_serial(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, 'dict'):
            return obj.dict()
        raise TypeError(f"Type {type(obj)} not serializable")

    async def send_message(data: dict):
        try:
            message = json.dumps(data, default=json_serial)
            await websocket.send_text(message)
            print(f"📤 Sent message: {data.get('type', 'unknown')}")
        except Exception as e:
            print(f"❌ Error sending message: {e}")

    try:
        if session_id not in execution_states:
            await send_message({"type": "error", "message": "Invalid session_id"})
            await websocket.close()
            return

        exec_context = execution_states[session_id]
        state = exec_context["state"]

        await send_message({
            "type": "status",
            "message": "Starting research workflow...",
            "topic": state.topic
        })

        config = {"configurable": {"thread_id": session_id}}

        # Execute graph
        print(f"🚀 Starting graph execution for session {session_id}")

        try:
            # Initial execution until first interrupt
            async for event in research_graph.astream(state, config, stream_mode="updates"):
                print(f"📦 Received event: {list(event.keys())}")

                node_name = list(event.keys())[0] if event else "unknown"
                node_state = event.get(node_name, {})

                # Convert state to dict
                state_dict = {}
                if isinstance(node_state, dict):
                    for key, value in node_state.items():
                        if isinstance(value, datetime):
                            state_dict[key] = value.isoformat()
                        elif hasattr(value, 'dict'):
                            state_dict[key] = value.dict()
                        else:
                            state_dict[key] = value

                # Update our state reference
                if isinstance(node_state, ResearchState):
                    state = node_state
                    exec_context["state"] = state

                # Send node completion update
                await send_message({
                    "type": "node_complete",
                    "node": node_name,
                    "state": {
                        "current_node": state_dict.get("current_node", node_name)
                    }
                })

            # Check if we're at an interrupt point
            print("🔍 Checking for interrupts...")
            current_graph_state = research_graph.get_state(config)

            if current_graph_state.next:
                next_nodes = current_graph_state.next if isinstance(current_graph_state.next, tuple) else (
                    current_graph_state.next,)
                next_node = next_nodes[0] if next_nodes else None
                print(f"📍 Next node to execute: {next_node}")

                # Handle plan review interrupt (before synthesize)
                if next_node == "synthesize":
                    print("⏸ Paused before synthesis - requesting plan review")

                    # Get current state values
                    state_values = current_graph_state.values
                    facts = state_values.get("facts_for_verification", [])

                    # Convert facts to serializable format
                    serialized_facts = []
                    for fact in (facts[:6] if isinstance(facts, list) else []):
                        try:
                            serialized_facts.append({
                                "claim": fact.claim if hasattr(fact, 'claim') else str(fact),
                                "source": fact.source if hasattr(fact, 'source') else "",
                                "confidence": fact.confidence if hasattr(fact, 'confidence') else 0.0
                            })
                        except Exception as e:
                            print(f"⚠️ Error serializing fact: {e}")

                    print(f"📋 Sending {len(serialized_facts)} facts for review")

                    hitl_message = {
                        "type": "hitl_required",
                        "checkpoint": "plan_review",
                        "data": {
                            "facts_for_verification": serialized_facts
                        }
                    }

                    await send_message(hitl_message)

                    # Give the frontend a moment to process the message
                    await asyncio.sleep(0.1)

                    exec_context["status"] = "waiting_plan_review"
                    print("⏳ Waiting for plan review feedback...")

                    # Wait for feedback
                    timeout = 0
                    while exec_context["status"] == "waiting_plan_review" and timeout < 600:
                        await asyncio.sleep(0.5)
                        timeout += 1

                        # Print status every 10 seconds
                        if timeout % 20 == 0:
                            print(f"⏳ Still waiting for feedback... ({timeout // 2}s elapsed)")

                    if timeout >= 600:
                        print("⏰ Timeout waiting for plan review")
                        await send_message({"type": "error", "message": "Timeout waiting for plan review"})
                        return

                    # Get updated state with feedback
                    state = exec_context["state"]
                    feedback_decision = state.human_feedback_plan.decision if state.human_feedback_plan else 'None'
                    print(f"✓ Plan review feedback received: {feedback_decision}")

                    # Update graph state with feedback
                    research_graph.update_state(
                        config,
                        {
                            "human_feedback_plan": state.human_feedback_plan
                        }
                    )

                    # Resume execution from synthesis
                    print("▶ Resuming graph from synthesis...")
                    async for resume_event in research_graph.astream(None, config, stream_mode="updates"):
                        resume_node = list(resume_event.keys())[0]
                        resume_state = resume_event.get(resume_node, {})

                        if isinstance(resume_state, ResearchState):
                            state = resume_state
                            exec_context["state"] = state

                        await send_message({
                            "type": "node_complete",
                            "node": resume_node
                        })

                    # Check for second interrupt (fact verification)
                    print("🔍 Checking for second interrupt...")
                    current_graph_state = research_graph.get_state(config)

                    if current_graph_state.next:
                        next_nodes = current_graph_state.next if isinstance(current_graph_state.next, tuple) else (
                            current_graph_state.next,)
                        next_node = next_nodes[0] if next_nodes else None
                        print(f"📍 Next node after resume: {next_node}")

                        # Handle fact verification interrupt
                        if next_node == "brief":
                            # Check if refine node set the fact verification flag
                            state_values = current_graph_state.values
                            requires_verification = state_values.get("requires_human_input", False)
                            checkpoint_id = state_values.get("checkpoint_id")

                            if requires_verification and checkpoint_id == "fact_verification":
                                print("⏸ Paused for fact verification")

                                facts = state_values.get("facts_for_verification", [])

                                # Convert facts to serializable format
                                serialized_facts = []
                                for fact in (facts[:6] if isinstance(facts, list) else []):
                                    try:
                                        serialized_facts.append({
                                            "claim": fact.claim if hasattr(fact, 'claim') else str(fact),
                                            "source": fact.source if hasattr(fact, 'source') else "",
                                            "confidence": fact.confidence if hasattr(fact, 'confidence') else 0.0
                                        })
                                    except Exception as e:
                                        print(f"⚠️ Error serializing fact: {e}")

                                print(f"📋 Sending {len(serialized_facts)} facts for verification")

                                await send_message({
                                    "type": "hitl_required",
                                    "checkpoint": "fact_verification",
                                    "data": {
                                        "facts": serialized_facts
                                    }
                                })

                                # Give the frontend a moment to process
                                await asyncio.sleep(0.1)

                                exec_context["status"] = "waiting_fact_verification"
                                print("⏳ Waiting for fact verification feedback...")

                                # Wait for feedback
                                timeout = 0
                                while exec_context["status"] == "waiting_fact_verification" and timeout < 600:
                                    await asyncio.sleep(0.5)
                                    timeout += 1

                                    # Print status every 10 seconds
                                    if timeout % 20 == 0:
                                        print(f"⏳ Still waiting for feedback... ({timeout // 2}s elapsed)")

                                if timeout >= 600:
                                    print("⏰ Timeout waiting for fact verification")
                                    await send_message(
                                        {"type": "error", "message": "Timeout waiting for fact verification"})
                                    return

                                state = exec_context["state"]
                                feedback_decision = state.human_feedback_facts.decision if state.human_feedback_facts else 'None'
                                print(f"✓ Fact verification feedback received: {feedback_decision}")

                                # Update graph state with feedback and clear flags
                                research_graph.update_state(
                                    config,
                                    {
                                        "human_feedback_facts": state.human_feedback_facts,
                                        "requires_human_input": False,
                                        "checkpoint_id": None
                                    }
                                )

                                # Resume final execution
                                print("▶ Resuming graph to completion...")
                                async for final_event in research_graph.astream(None, config, stream_mode="updates"):
                                    final_node = list(final_event.keys())[0]
                                    final_state = final_event.get(final_node, {})

                                    if isinstance(final_state, ResearchState):
                                        state = final_state
                                        exec_context["state"] = state

                                    await send_message({
                                        "type": "node_complete",
                                        "node": final_node
                                    })

            print("✅ Graph execution completed")

        except Exception as graph_error:
            print(f"❌ Graph execution error: {graph_error}")
            import traceback
            traceback.print_exc()
            await send_message({
                "type": "error",
                "message": f"Graph execution failed: {str(graph_error)}"
            })
            return

        # Send completion
        # Send completion
        brief_content = ""
        if hasattr(state, 'formatted_brief') and state.formatted_brief:
            brief_content = state.formatted_brief
        elif hasattr(state, 'final_brief') and state.final_brief:
            brief_content = state.final_brief

        print(f"📄 Sending completion with brief length: {len(brief_content) if brief_content else 0}")

        await send_message({
            "type": "complete",
            "message": "Research brief generated successfully",
            "brief_content": brief_content if brief_content else "Brief generation completed. Check the outputs folder for the saved file."
        })

        exec_context["status"] = "completed"
        print("🎉 Workflow completed successfully")

    except WebSocketDisconnect:
        print(f"👋 Client disconnected: {session_id}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if session_id in active_connections:
            del active_connections[session_id]
            print(f"🧹 Cleaned up connection: {session_id}")

@app.post("/research/feedback")
async def submit_feedback(request: HumanFeedbackRequest):
    """
    Submit human feedback for HITL checkpoint.
    This resumes the paused workflow.
    """
    if request.session_id not in execution_states:
        raise HTTPException(status_code=404, detail="Session not found")

    exec_context = execution_states[request.session_id]

    # Create feedback object
    feedback = HumanFeedback(
        checkpoint_type=request.checkpoint_type,
        decision=request.decision,
        comments=request.comments,
        emphasis_areas=request.emphasis_areas
    )

    # Update state with feedback
    state = exec_context["state"]

    if request.checkpoint_type == "plan_review":
        state.human_feedback_plan = feedback
        state.requires_human_input = False
        exec_context["status"] = "processing"
    elif request.checkpoint_type == "fact_verification":
        state.human_feedback_facts = feedback
        state.requires_human_input = False
        exec_context["status"] = "processing"

    exec_context["state"] = state

    return {
        "status": "feedback_received",
        "session_id": request.session_id,
        "checkpoint": request.checkpoint_type,
        "decision": request.decision
    }


@app.get("/research/status/{session_id}")
async def get_status(session_id: str):
    """Get current status of a research session."""
    if session_id not in execution_states:
        raise HTTPException(status_code=404, detail="Session not found")

    exec_context = execution_states[session_id]
    state = exec_context["state"]

    return {
        "session_id": session_id,
        "status": exec_context["status"],
        "current_node": state.current_node,
        "checkpoint": exec_context.get("checkpoint"),
        "topic": state.topic
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)