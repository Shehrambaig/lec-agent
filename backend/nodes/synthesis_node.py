import time
import json
from backend.state import ResearchState, DraftPlan
from backend.utils import call_openai, load_prompt, get_model_settings
from backend.logger import execution_logger


def synthesis_node(state: ResearchState) -> ResearchState:
    """
    Synthesis node: Create initial lecture plan from prioritized research.

    This node:
    - Synthesizes research into structured lecture plan
    - Allocates time across sections
    - Identifies key learning points
    """
    start_time = time.time()

    # Prepare prioritized claims summary
    claims_summary = ""
    for idx, claim in enumerate(state.prioritized_claims, 1):
        claims_summary += f"\n[Claim {idx}]\n"
        claims_summary += f"Content: {claim.claim}\n"
        claims_summary += f"Source: {claim.source}\n"
        claims_summary += f"Confidence: {claim.confidence}\n"

    # Load prompt template
    prompt_template = load_prompt("synthesis_prompt")

    # Check if there's human feedback to incorporate
    feedback_text = ""
    if state.human_feedback_plan:
        feedback_text = f"\n\nHUMAN FEEDBACK TO ADDRESS:\n"
        feedback_text += f"Decision: {state.human_feedback_plan.decision}\n"
        if state.human_feedback_plan.comments:
            feedback_text += f"Comments: {state.human_feedback_plan.comments}\n"
        if state.human_feedback_plan.emphasis_areas:
            feedback_text += f"Areas to emphasize: {', '.join(state.human_feedback_plan.emphasis_areas)}\n"
        feedback_text += "\nPlease revise the plan to address the above feedback.\n"

    prompt = prompt_template.format(
        topic=state.topic,
        prioritized_claims=claims_summary
    ) + feedback_text

    print(f"⚙ Synthesizing lecture plan...")
    plan_response = call_openai(prompt, max_tokens=2500)

    # Parse plan
    try:
        plan_str = plan_response.strip()
        if "```json" in plan_str:
            plan_str = plan_str.split("```json")[1].split("```")[0].strip()
        elif "```" in plan_str:
            plan_str = plan_str.split("```")[1].split("```")[0].strip()

        plan_data = json.loads(plan_str)

        # Validate and clean the data
        introduction = plan_data.get('introduction', '')
        if not isinstance(introduction, str):
            introduction = str(introduction) if introduction else "Introduction to the topic"

        sections = plan_data.get('sections', [])
        if not isinstance(sections, list):
            sections = []

        time_allocation = plan_data.get('time_allocation', {})
        if not isinstance(time_allocation, dict):
            time_allocation = {
                "introduction": 10,
                "main_content": 50,
                "applications": 10,
                "risks": 10,
                "qa": 10
            }

        key_points = plan_data.get('key_points', [])
        if not isinstance(key_points, list):
            key_points = []

        state.draft_plan = DraftPlan(
            introduction=introduction,
            sections=sections,
            time_allocation=time_allocation,
            key_points=key_points
        )

    except json.JSONDecodeError as e:
        print(f"⚠ Failed to parse plan, creating fallback: {e}")

        # Create simple fallback plan
        state.draft_plan = DraftPlan(
            introduction="Introduction to " + state.topic,
            sections=[
                {
                    "title": "Core Concepts",
                    "time_minutes": 20,
                    "key_points": [claim.claim for claim in state.prioritized_claims[:3]],
                    "supporting_claims": [0, 1, 2]
                },
                {
                    "title": "Applications and Implications",
                    "time_minutes": 20,
                    "key_points": [claim.claim for claim in state.prioritized_claims[3:6]],
                    "supporting_claims": [3, 4, 5]
                },
                {
                    "title": "Risks and Challenges",
                    "time_minutes": 15,
                    "key_points": [claim.claim for claim in state.prioritized_claims[6:9]],
                    "supporting_claims": [6, 7, 8]
                }
            ],
            time_allocation={
                "introduction": 10,
                "main_content": 55,
                "applications": 0,
                "risks": 0,
                "qa": 15
            },
            key_points=[claim.claim[:100] for claim in state.prioritized_claims[:5]]
        )

    # Mark that we need human input
    state.requires_human_input = True
    state.checkpoint_id = "plan_review"

    # Update state
    state.current_node = "synthesis"

    # Log execution
    execution_time = (time.time() - start_time) * 1000
    execution_logger.log_node_execution(
        node_name="synthesis_node",
        inputs={"prioritized_claims_count": len(state.prioritized_claims)},
        prompt=prompt,
        output={
            "plan_created": True,
            "sections_count": len(state.draft_plan.sections),
            "total_minutes": sum(state.draft_plan.time_allocation.values())
        },
        model_settings=get_model_settings(),
        execution_time_ms=execution_time
    )

    print(f"✓ Synthesis completed: Draft plan created with {len(state.draft_plan.sections)} sections")
    print(f"⏸ Waiting for human review of plan...")

    return state