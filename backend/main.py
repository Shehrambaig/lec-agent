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


def extract_node_trace(node_name: str, state: ResearchState) -> dict:
    """Extract trace details for a specific node from the current state."""
    trace = {
        "node": node_name,
        "details": []
    }

    if node_name == "input":
        trace["details"] = [
            f"Topic: {state.topic}",
            f"User: {state.user_id}"
        ]

    elif node_name == "plan":
        if state.research_plan:
            plan = state.research_plan
            trace["details"] = [
                f"Generated {len(plan.search_queries)} search queries",
                f"Identified {len(plan.research_angles)} research angles"
            ]
            trace["search_queries"] = plan.search_queries
            trace["research_angles"] = [
                {"title": a.get("title", a["title"]) if isinstance(a, dict) else a.title,
                 "description": a.get("description", "") if isinstance(a, dict) else a.description}
                for a in plan.research_angles
            ]
            if plan.revision_count > 0:
                trace["details"].append(f"Revision #{plan.revision_count}")

    elif node_name == "search":
        trace["details"] = [
            f"Executed {len(state.search_queries)} search queries",
            f"Found {len(state.search_results)} results",
            f"Created {len(state.citations)} citations"
        ]
        trace["queries_executed"] = state.search_queries[:5]
        trace["sample_results"] = [
            {"title": r.get("title", ""), "url": r.get("link", "")}
            for r in state.search_results[:5]
        ]

    elif node_name == "extract":
        trace["details"] = [
            f"Extracted {len(state.extracted_claims)} claims from search results"
        ]
        trace["sample_claims"] = [
            {"claim": c.claim[:100] + "..." if len(c.claim) > 100 else c.claim,
             "confidence": c.confidence}
            for c in state.extracted_claims[:3]
        ] if state.extracted_claims else []

    elif node_name == "prioritize":
        trace["details"] = [
            f"Prioritized {len(state.prioritized_claims)} claims",
            f"Selected {len(state.facts_for_verification)} facts for verification"
        ]
        trace["top_claims"] = [
            {"claim": c.claim[:100] + "..." if len(c.claim) > 100 else c.claim,
             "confidence": c.confidence,
             "source": c.source}
            for c in state.prioritized_claims[:3]
        ] if state.prioritized_claims else []

    elif node_name == "synthesize":
        if state.draft_plan:
            trace["details"] = [
                f"Created lecture plan with {len(state.draft_plan.sections)} sections",
                f"Total time: {sum(state.draft_plan.time_allocation.values())} minutes"
            ]
            trace["sections"] = [s.get("title", "Untitled") for s in state.draft_plan.sections]

    elif node_name == "refine":
        if state.refined_plan:
            trace["details"] = [
                f"Refined plan based on feedback",
                f"Sections: {len(state.refined_plan.sections)}"
            ]

    elif node_name == "brief":
        if state.final_brief:
            trace["details"] = [
                f"Generated brief ({len(state.final_brief)} characters)",
                f"Includes citations from {len(state.citations)} sources"
            ]

    elif node_name == "format":
        trace["details"] = [
            "Formatted and saved final output",
            f"Brief saved to outputs folder"
        ]

    return trace

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

                # Extract trace details for this node
                trace_data = extract_node_trace(node_name, state)

                # Send node completion update with trace
                await send_message({
                    "type": "node_complete",
                    "node": node_name,
                    "state": {
                        "current_node": state_dict.get("current_node", node_name)
                    },
                    "trace": trace_data
                })

            # Check if we're at an interrupt point
            print("🔍 Checking for interrupts...")
            current_graph_state = research_graph.get_state(config)

            if current_graph_state.next:
                next_nodes = current_graph_state.next if isinstance(current_graph_state.next, tuple) else (
                    current_graph_state.next,)
                next_node = next_nodes[0] if next_nodes else None
                print(f"📍 Next node to execute: {next_node}")

                # ========================================
                # NEW FIRST INTERRUPT: Research Plan Approval (before search)
                # ========================================
                if next_node == "search":
                    print("⏸ Paused before search - requesting research plan approval")

                    # Loop for plan revision
                    plan_approved = False
                    while not plan_approved:
                        # Get current state values
                        state_values = current_graph_state.values
                        research_plan = state_values.get("research_plan")

                        if research_plan:
                            # Convert research plan to serializable format
                            if hasattr(research_plan, 'dict'):
                                plan_dict = research_plan.dict()
                            else:
                                plan_dict = research_plan

                            print(f"📋 Sending research plan for approval (revision #{plan_dict.get('revision_count', 0)})")

                            await send_message({
                                "type": "hitl_required",
                                "checkpoint": "research_plan",
                                "data": {
                                    "research_plan": plan_dict
                                }
                            })

                            await asyncio.sleep(0.1)

                            exec_context["status"] = "waiting_research_plan"
                            print("⏳ Waiting for research plan approval...")

                            # Wait for feedback
                            timeout = 0
                            while exec_context["status"] == "waiting_research_plan" and timeout < 600:
                                await asyncio.sleep(0.5)
                                timeout += 1

                                if timeout % 20 == 0:
                                    print(f"⏳ Still waiting for research plan feedback... ({timeout // 2}s elapsed)")

                            if timeout >= 600:
                                print("⏰ Timeout waiting for research plan approval")
                                await send_message({"type": "error", "message": "Timeout waiting for research plan approval"})
                                return

                            # Get updated state with feedback
                            state = exec_context["state"]
                            feedback = state.human_feedback_research_plan
                            feedback_decision = feedback.decision if feedback else 'None'
                            print(f"✓ Research plan feedback received: {feedback_decision}")

                            if feedback and feedback.decision == "approve":
                                plan_approved = True
                                state.plan_approved = True
                                exec_context["state"] = state

                                # Update graph state
                                research_graph.update_state(
                                    config,
                                    {
                                        "human_feedback_research_plan": state.human_feedback_research_plan,
                                        "plan_approved": True
                                    },
                                    as_node="plan"
                                )
                            else:
                                # Revision requested - re-run plan node
                                print("🔄 Revision requested - regenerating research plan...")

                                # Update graph state with feedback for revision
                                research_graph.update_state(
                                    config,
                                    {
                                        "human_feedback_research_plan": state.human_feedback_research_plan,
                                        "plan_approved": False
                                    },
                                    as_node="input"  # Go back before plan
                                )

                                # Re-run the plan node
                                await send_message({
                                    "type": "status",
                                    "message": "Revising research plan based on feedback..."
                                })

                                async for plan_event in research_graph.astream(None, config, stream_mode="updates"):
                                    plan_node = list(plan_event.keys())[0]
                                    plan_state = plan_event.get(plan_node, {})

                                    if isinstance(plan_state, ResearchState):
                                        state = plan_state
                                        exec_context["state"] = state

                                    await send_message({
                                        "type": "node_complete",
                                        "node": plan_node,
                                        "trace": extract_node_trace(plan_node, state)
                                    })

                                # Get updated state for next loop iteration
                                current_graph_state = research_graph.get_state(config)
                        else:
                            print("⚠️ No research plan found, skipping approval")
                            plan_approved = True

                    # After plan approved, resume to search
                    print("▶ Research plan approved, resuming to search...")
                    async for search_event in research_graph.astream(None, config, stream_mode="updates"):
                        search_node_name = list(search_event.keys())[0]
                        search_state = search_event.get(search_node_name, {})

                        if isinstance(search_state, ResearchState):
                            state = search_state
                            exec_context["state"] = state

                        await send_message({
                            "type": "node_complete",
                            "node": search_node_name,
                            "trace": extract_node_trace(search_node_name, state)
                        })

                    # Check for next interrupt (synthesize)
                    current_graph_state = research_graph.get_state(config)
                    if current_graph_state.next:
                        next_nodes = current_graph_state.next if isinstance(current_graph_state.next, tuple) else (
                            current_graph_state.next,)
                        next_node = next_nodes[0] if next_nodes else None

                # ========================================
                # SECOND INTERRUPT: Plan Review (before synthesize)
                # ========================================
                if next_node == "synthesize":
                    print("⏸ Paused before synthesis - requesting fact check")

                    # Get current state values
                    state_values = current_graph_state.values
                    facts = state_values.get("facts_for_verification", [])
                    citations = state_values.get("citations", [])

                    # Build citation lookup by id
                    citation_lookup = {}
                    for citation in citations:
                        if hasattr(citation, 'id'):
                            citation_lookup[citation.id] = citation
                        elif isinstance(citation, dict):
                            citation_lookup[citation.get('id')] = citation

                    # Convert facts to serializable format with URLs
                    serialized_facts = []
                    for fact in (facts[:6] if isinstance(facts, list) else []):
                        try:
                            # Get URL from citation
                            citation_id = fact.citation_id if hasattr(fact, 'citation_id') else None
                            citation = citation_lookup.get(citation_id)
                            url = ""
                            if citation:
                                url = citation.url if hasattr(citation, 'url') else citation.get('url', '')

                            serialized_facts.append({
                                "claim": fact.claim if hasattr(fact, 'claim') else str(fact),
                                "source": fact.source if hasattr(fact, 'source') else "",
                                "confidence": fact.confidence if hasattr(fact, 'confidence') else 0.0,
                                "url": url
                            })
                        except Exception as e:
                            print(f"⚠️ Error serializing fact: {e}")

                    print(f"📋 Sending {len(serialized_facts)} facts for fact check")

                    hitl_message = {
                        "type": "hitl_required",
                        "checkpoint": "plan_review",
                        "data": {
                            "facts_for_verification": serialized_facts
                        }
                    }

                    await send_message(hitl_message)
                    await asyncio.sleep(0.1)

                    exec_context["status"] = "waiting_plan_review"
                    print("⏳ Waiting for plan review feedback...")

                    # Wait for feedback
                    timeout = 0
                    while exec_context["status"] == "waiting_plan_review" and timeout < 600:
                        await asyncio.sleep(0.5)
                        timeout += 1

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
                        },
                        as_node="prioritize"
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
                            "node": resume_node,
                            "trace": extract_node_trace(resume_node, state)
                        })

                    # ========================================
                    # SECOND INTERRUPT: Plan Approval (before refine)
                    # ========================================
                    print("🔍 Checking for second interrupt (plan approval)...")
                    current_graph_state = research_graph.get_state(config)

                    if current_graph_state.next:
                        next_nodes = current_graph_state.next if isinstance(current_graph_state.next, tuple) else (
                            current_graph_state.next,)
                        next_node = next_nodes[0] if next_nodes else None
                        print(f"📍 Next node after synthesis: {next_node}")

                        # Handle plan approval interrupt (BEFORE refine runs)
                        if next_node == "refine":
                            print("⏸ Graph paused before refine - checking for plan approval")

                            state_values = current_graph_state.values
                            draft_plan = state_values.get("draft_plan")

                            # ALWAYS ask for approval when we have a draft plan
                            if draft_plan:
                                print("⏸ Requesting plan approval from user")

                                # Convert draft_plan to string if it's an object
                                if hasattr(draft_plan, 'dict'):
                                    plan_dict = draft_plan.dict()
                                    draft_plan_str = f"""
Introduction:
{plan_dict.get('introduction', 'N/A')}

Sections:
{chr(10).join([f"{i + 1}. {s.get('title', 'Untitled')}: {s.get('content', 'No content')}" for i, s in enumerate(plan_dict.get('sections', []))])}

Key Points:
{chr(10).join([f"• {point}" for point in plan_dict.get('key_points', [])])}

Time Allocation:
{chr(10).join([f"• {k}: {v} minutes" for k, v in plan_dict.get('time_allocation', {}).items()])}
"""
                                else:
                                    draft_plan_str = str(draft_plan)

                                await send_message({
                                    "type": "hitl_required",
                                    "checkpoint": "plan_approval",
                                    "data": {
                                        "draft_plan": draft_plan_str
                                    }
                                })

                                await asyncio.sleep(0.1)

                                exec_context["status"] = "waiting_plan_approval"
                                print("⏳ Waiting for plan approval...")

                                # Wait for approval feedback
                                timeout = 0
                                while exec_context["status"] == "waiting_plan_approval" and timeout < 600:
                                    await asyncio.sleep(0.5)
                                    timeout += 1

                                    if timeout % 20 == 0:
                                        print(f"⏳ Still waiting for approval... ({timeout // 2}s elapsed)")

                                if timeout >= 600:
                                    print("⏰ Timeout waiting for plan approval")
                                    await send_message(
                                        {"type": "error", "message": "Timeout waiting for plan approval"})
                                    return

                                state = exec_context["state"]
                                approval_decision = state.human_feedback_approval.decision if state.human_feedback_approval else 'None'
                                print(f"✓ Plan approval received: {approval_decision}")

                                # Update graph state with approval feedback
                                research_graph.update_state(
                                    config,
                                    {
                                        "human_feedback_approval": state.human_feedback_approval
                                    },
                                    as_node="synthesize",
                                )

                                # Resume from refine
                                print("▶ Resuming graph from refine...")
                                async for refine_event in research_graph.astream(None, config, stream_mode="updates"):
                                    refine_node = list(refine_event.keys())[0]
                                    refine_state = refine_event.get(refine_node, {})

                                    if isinstance(refine_state, ResearchState):
                                        state = refine_state
                                        exec_context["state"] = state

                                    await send_message({
                                        "type": "node_complete",
                                        "node": refine_node,
                                        "trace": extract_node_trace(refine_node, state)
                                    })

                                # ========================================
                                # THIRD INTERRUPT: Fact Verification (before brief)
                                # ========================================
                                print("🔍 Checking for third interrupt (fact verification)...")
                                current_graph_state = research_graph.get_state(config)

                                if current_graph_state.next:
                                    next_nodes = current_graph_state.next if isinstance(current_graph_state.next,
                                                                                        tuple) else (
                                        current_graph_state.next,)
                                    next_node = next_nodes[0] if next_nodes else None
                                    print(f"📍 Next node after refine: {next_node}")

                                    if next_node == "brief":
                                        state_values = current_graph_state.values
                                        requires_verification = state_values.get("requires_human_input", False)
                                        checkpoint_id = state_values.get("checkpoint_id")

                                        if requires_verification and checkpoint_id == "fact_verification":
                                            print("⏸ Paused for fact verification")

                                            facts = state_values.get("facts_for_verification", [])

                                            serialized_facts = []
                                            for fact in (facts[:6] if isinstance(facts, list) else []):
                                                try:
                                                    serialized_facts.append({
                                                        "claim": fact.claim if hasattr(fact, 'claim') else str(fact),
                                                        "source": fact.source if hasattr(fact, 'source') else "",
                                                        "confidence": fact.confidence if hasattr(fact,
                                                                                                 'confidence') else 0.0
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

                                            await asyncio.sleep(0.1)

                                            exec_context["status"] = "waiting_fact_verification"
                                            print("⏳ Waiting for fact verification feedback...")

                                            timeout = 0
                                            while exec_context[
                                                "status"] == "waiting_fact_verification" and timeout < 600:
                                                await asyncio.sleep(0.5)
                                                timeout += 1

                                                if timeout % 20 == 0:
                                                    print(f"⏳ Still waiting for feedback... ({timeout // 2}s elapsed)")

                                            if timeout >= 600:
                                                print("⏰ Timeout waiting for fact verification")
                                                await send_message(
                                                    {"type": "error",
                                                     "message": "Timeout waiting for fact verification"})
                                                return

                                            state = exec_context["state"]
                                            feedback_decision = state.human_feedback_facts.decision if state.human_feedback_facts else 'None'
                                            print(f"✓ Fact verification feedback received: {feedback_decision}")

                                            # Update graph state and resume final execution
                                            research_graph.update_state(
                                                config,
                                                {
                                                    "human_feedback_facts": state.human_feedback_facts,
                                                    "requires_human_input": False,
                                                    "checkpoint_id": None
                                                },
                                                as_node="refine"
                                            )

                                            print("▶ Resuming graph to completion...")
                                            async for final_event in research_graph.astream(None, config,
                                                                                            stream_mode="updates"):
                                                final_node = list(final_event.keys())[0]
                                                final_state = final_event.get(final_node, {})

                                                if isinstance(final_state, ResearchState):
                                                    state = final_state
                                                    exec_context["state"] = state

                                                await send_message({
                                                    "type": "node_complete",
                                                    "node": final_node,
                                                    "trace": extract_node_trace(final_node, state)
                                                })
                                        else:
                                            # No fact verification needed, just continue to completion
                                            print("▶ No fact verification needed, resuming to completion...")
                                            async for final_event in research_graph.astream(None, config,
                                                                                            stream_mode="updates"):
                                                final_node = list(final_event.keys())[0]
                                                final_state = final_event.get(final_node, {})

                                                if isinstance(final_state, ResearchState):
                                                    state = final_state
                                                    exec_context["state"] = state

                                                await send_message({
                                                    "type": "node_complete",
                                                    "node": final_node,
                                                    "trace": extract_node_trace(final_node, state)
                                                })
                            else:
                                print("⚠️ No draft plan found, skipping approval")

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

        # Try to get the brief content from various possible fields
        if hasattr(state, 'formatted_brief') and state.formatted_brief:
            brief_content = state.formatted_brief
            print(f"📄 Using formatted_brief: {len(brief_content)} chars")
        elif hasattr(state, 'final_brief') and state.final_brief:
            brief_content = state.final_brief
            print(f"📄 Using final_brief: {len(brief_content)} chars")
        else:
            # Try to read from the saved file as fallback
            print("⚠️ Brief not found in state, attempting to read from saved file...")
            try:
                import os
                import glob

                # Find the most recent brief file
                output_files = glob.glob("outputs/brief_*.md")
                if output_files:
                    latest_file = max(output_files, key=os.path.getctime)
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        brief_content = f.read()
                    print(f"📄 Read brief from file: {latest_file} ({len(brief_content)} chars)")
                else:
                    print("⚠️ No brief files found in outputs folder")
            except Exception as e:
                print(f"❌ Error reading brief file: {e}")

        print(f"📄 Sending completion with brief length: {len(brief_content) if brief_content else 0}")

        if not brief_content:
            # Debug: print what's actually in the state
            print("🔍 DEBUG - State contents:")
            print(
                f"  - formatted_brief: {getattr(state, 'formatted_brief', 'NOT SET')[:100] if hasattr(state, 'formatted_brief') else 'MISSING'}")
            print(
                f"  - final_brief: {getattr(state, 'final_brief', 'NOT SET')[:100] if hasattr(state, 'final_brief') else 'MISSING'}")

        await send_message({
            "type": "complete",
            "message": "Research brief generated successfully" if brief_content else "Brief saved to outputs folder",
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

    if request.checkpoint_type == "research_plan":
        state.human_feedback_research_plan = feedback
        state.requires_human_input = False
        exec_context["status"] = "processing"
        print(f"📝 Research plan feedback received: {request.decision}")
    elif request.checkpoint_type == "plan_review":
        state.human_feedback_plan = feedback
        state.requires_human_input = False
        exec_context["status"] = "processing"
        print(f"📝 Plan review feedback received: {request.decision}")
    elif request.checkpoint_type == "plan_approval":
        state.human_feedback_approval = feedback
        state.requires_human_input = False
        exec_context["status"] = "processing"
        print(f"📝 Plan approval feedback received: {request.decision}")
    elif request.checkpoint_type == "fact_verification":
        state.human_feedback_facts = feedback
        state.requires_human_input = False
        exec_context["status"] = "processing"
        print(f"📝 Fact verification feedback received: {request.decision}")

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