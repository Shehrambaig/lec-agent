import time
import json
from backend.state import ResearchState, ResearchPlan
from backend.utils import call_openai, load_prompt, get_model_settings
from backend.logger import execution_logger


def research_plan_node(state: ResearchState) -> ResearchState:
    """
    Research Plan node: Generate a research action plan for human review.

    This node:
    - Creates search queries and research angles based on the topic
    - Incorporates revision feedback if provided
    - Prepares the plan for human approval before searches begin
    """
    start_time = time.time()

    # Load prompt template
    prompt_template = load_prompt("research_plan_prompt")

    # Build revision section if this is a revision
    revision_section = ""
    if state.human_feedback_research_plan and state.human_feedback_research_plan.decision == "revise":
        revision_count = state.research_plan.revision_count + 1 if state.research_plan else 1
        feedback_text = state.human_feedback_research_plan.comments or 'No specific feedback provided'
        revision_section = f"""
============================================================
REVISION REQUEST (Attempt #{revision_count})
============================================================

The human reviewer has requested changes to the research plan.

USER FEEDBACK:
"{feedback_text}"

INSTRUCTIONS FOR REVISION:
1. Carefully read the user feedback above
2. Modify your search queries to directly address what the user is asking for
3. Add new research angles if the feedback suggests new areas to explore
4. If the user mentions comparisons, contrasts, or additional topics, explicitly include them
5. Make sure the revised plan clearly shows how you're addressing the feedback

REMEMBER: The user feedback is the most important input. Your revised plan must show clear changes based on their comments.
============================================================
"""
    else:
        revision_section = ""

    prompt = prompt_template.format(
        topic=state.topic,
        revision_section=revision_section
    )

    # Generate research plan using LLM
    print(f"⚙ Generating research plan for: {state.topic}")
    if revision_section:
        print(f"  📝 This is a revision based on human feedback")

    plan_response = call_openai(prompt, max_tokens=1500)

    # Parse the response
    try:
        plan_str = plan_response.strip()
        if "```json" in plan_str:
            plan_str = plan_str.split("```json")[1].split("```")[0].strip()
        elif "```" in plan_str:
            plan_str = plan_str.split("```")[1].split("```")[0].strip()

        plan_data = json.loads(plan_str)

        search_queries = plan_data.get("search_queries", [])
        research_angles = plan_data.get("research_angles", [])

    except json.JSONDecodeError as e:
        print(f"⚠ Failed to parse LLM response, using fallback: {e}")
        # Fallback plan
        search_queries = [
            f"{state.topic} overview",
            f"{state.topic} latest research",
            f"{state.topic} analysis",
            f"{state.topic} impact",
            f"{state.topic} expert opinions"
        ]
        research_angles = [
            {"title": "Background & Context", "description": "Historical context and foundational concepts"},
            {"title": "Current State", "description": "Latest developments and current situation"},
            {"title": "Key Players & Actors", "description": "Main entities involved and their roles"},
            {"title": "Impact & Implications", "description": "Effects and broader implications"}
        ]

    # Calculate revision count
    revision_count = 0
    if state.research_plan:
        revision_count = state.research_plan.revision_count + 1

    # Create research plan object
    research_plan = ResearchPlan(
        search_queries=search_queries,
        research_angles=research_angles,
        topic=state.topic,
        revision_count=revision_count,
        revision_feedback=state.human_feedback_research_plan.comments if state.human_feedback_research_plan else None
    )

    state.research_plan = research_plan
    state.current_node = "plan"
    state.plan_approved = False  # Reset approval status for new/revised plan

    # Log execution
    execution_time = (time.time() - start_time) * 1000
    execution_logger.log_node_execution(
        node_name="research_plan_node",
        inputs={"topic": state.topic, "revision_count": revision_count},
        prompt=prompt,
        output={
            "search_queries": search_queries,
            "research_angles": research_angles,
            "revision_count": revision_count
        },
        model_settings=get_model_settings(),
        execution_time_ms=execution_time
    )

    print(f"✓ Research plan generated: {len(search_queries)} queries, {len(research_angles)} angles")
    if revision_count > 0:
        print(f"  📝 Revision #{revision_count}")

    return state
