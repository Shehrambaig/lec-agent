from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.state import ResearchState
from backend.nodes import (
    input_node,
    research_plan_node,
    search_node,
    extract_node,
    author_prioritization_node,
    synthesis_node,
    refinement_node,
    brief_node,
    formatting_node
)


def should_continue_after_plan(state: ResearchState) -> Literal["search", "plan"]:
    """
    After research plan review, check if approved or needs revision.
    If approved, continue to search. If revision needed, loop back to plan.
    """
    if state.plan_approved:
        return "search"
    # If not approved, it means revision was requested - loop back to plan
    # But on first run, plan_approved will be False and we wait for HITL
    # The main.py will handle setting plan_approved based on feedback
    return "search"  # Default to search, HITL interrupt will pause before this


def should_continue_after_prioritize(state: ResearchState) -> Literal["synthesize"]:
    """
    After prioritization, always continue to synthesis.
    The synthesis node will handle the plan review if needed.
    """
    return "synthesize"


def should_wait_for_fact_verification(state: ResearchState) -> Literal["wait", "brief"]:
    """Conditional edge to determine if we should wait for fact verification."""
    if state.requires_human_input and state.checkpoint_id == "fact_verification":
        return "wait"
    return "brief"


def create_research_graph():
    """
    Create the LangGraph workflow for lecture research.

    Workflow:
    INPUT → PLAN → [HITL: approve/revise loop] → SEARCH → EXTRACT → PRIORITIZE → SYNTHESIZE → REFINE → BRIEF → FORMAT → END
    """
    checkpointer = MemorySaver()
    print("ℹ️  Using MemorySaver (checkpoints in memory only)")

    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("input", input_node)
    workflow.add_node("plan", research_plan_node)
    workflow.add_node("search", search_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("prioritize", author_prioritization_node)
    workflow.add_node("synthesize", synthesis_node)
    workflow.add_node("refine", refinement_node)
    workflow.add_node("brief", brief_node)
    workflow.add_node("format", formatting_node)

    # Set entry point
    workflow.set_entry_point("input")

    # Add edges
    # Input -> Plan (new research planning step)
    workflow.add_edge("input", "plan")

    # Plan -> Search (after HITL approval)
    # The interrupt_before on "search" will pause for human approval
    workflow.add_edge("plan", "search")

    # Continue with rest of workflow
    workflow.add_edge("search", "extract")
    workflow.add_edge("extract", "prioritize")

    # After prioritize, always go to synthesize
    # The interrupt will happen because of interrupt_before
    workflow.add_edge("prioritize", "synthesize")

    # After synthesis, go to refinement
    workflow.add_edge("synthesize", "refine")

    # After refinement, check if we need fact verification
    workflow.add_conditional_edges(
        "refine",
        should_wait_for_fact_verification,
        {
            "wait": "refine",  # Loop back to wait (pause execution)
            "brief": "brief"  # Continue to brief generation
        }
    )

    # Final steps
    workflow.add_edge("brief", "format")
    workflow.add_edge("format", END)

    # Compile with interrupt points:
    # 1. Before search - for research plan approval (NEW)
    # 2. Before synthesize - for fact review
    # 3. Before refine - for plan approval
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["search", "synthesize", "refine"]
    )

    return app


# Create the compiled graph
research_graph = create_research_graph()