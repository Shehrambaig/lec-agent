import time
import json
from backend.state import ResearchState, DraftPlan
from backend.utils import call_openai, load_prompt, get_model_settings
from backend.logger import execution_logger


def refinement_node(state: ResearchState) -> ResearchState:
    """
    Refinement node: Refine lecture plan based on human feedback.
    """
    start_time = time.time()

    # Get the appropriate feedback
    feedback = state.human_feedback_plan

    if not feedback:
        print("⚠ No human feedback received, using draft plan as-is")
        state.refined_plan = state.draft_plan
        state.current_node = "refinement"
        state.requires_human_input = False
        state.checkpoint_id = None  # Clear checkpoint
        return state

    print(f"⚙ Refining plan based on feedback: {feedback.decision}")

    # If approved, use draft as-is and move forward
    if feedback.decision == "approve":
        state.refined_plan = state.draft_plan
        state.requires_human_input = False
        state.checkpoint_id = None  # CLEAR THE CHECKPOINT!
        print("✓ Plan approved, proceeding to next stage")

    elif feedback.decision == "rework":
        # Prepare data for refinement prompt
        claims_summary = ""
        for idx, claim in enumerate(state.prioritized_claims, 1):
            claims_summary += f"[{idx}] {claim.claim}\n"

        # Load prompt template
        prompt_template = load_prompt("refinement_prompt")
        prompt = prompt_template.format(
            topic=state.topic,
            original_plan=json.dumps(state.draft_plan.dict(), indent=2),
            decision=feedback.decision,
            comments=feedback.comments or "None provided",
            emphasis_areas=", ".join(feedback.emphasis_areas) if feedback.emphasis_areas else "None",
            prioritized_claims=claims_summary
        )

        plan_response = call_openai(prompt, max_tokens=2500)

        # Parse refined plan
        try:
            plan_str = plan_response.strip()
            if "```json" in plan_str:
                plan_str = plan_str.split("```json")[1].split("```")[0].strip()
            elif "```" in plan_str:
                plan_str = plan_str.split("```")[1].split("```")[0].strip()

            plan_data = json.loads(plan_str)

            state.refined_plan = DraftPlan(
                introduction=plan_data['introduction'],
                sections=plan_data['sections'],
                time_allocation=plan_data['time_allocation'],
                key_points=plan_data['key_points']
            )

            # After rework, show the plan again for approval
            state.requires_human_input = True
            state.checkpoint_id = "plan_review"
            state.draft_plan = state.refined_plan
            print("✓ Plan refined, requesting review...")

        except json.JSONDecodeError as e:
            print(f"⚠ Failed to parse refined plan: {e}")
            state.refined_plan = state.draft_plan
            state.requires_human_input = False
            state.checkpoint_id = None

    elif feedback.decision == "emphasize_topic":
        # Handle emphasis request
        claims_summary = ""
        for idx, claim in enumerate(state.prioritized_claims, 1):
            claims_summary += f"[{idx}] {claim.claim}\n"

        prompt_template = load_prompt("refinement_prompt")
        prompt = prompt_template.format(
            topic=state.topic,
            original_plan=json.dumps(state.draft_plan.dict(), indent=2),
            decision="emphasize specific topics",
            comments=feedback.comments or "None provided",
            emphasis_areas=", ".join(feedback.emphasis_areas) if feedback.emphasis_areas else "None",
            prioritized_claims=claims_summary
        )

        plan_response = call_openai(prompt, max_tokens=2500)

        try:
            plan_str = plan_response.strip()
            if "```json" in plan_str:
                plan_str = plan_str.split("```json")[1].split("```")[0].strip()
            elif "```" in plan_str:
                plan_str = plan_str.split("```")[1].split("```")[0].strip()

            plan_data = json.loads(plan_str)

            state.refined_plan = DraftPlan(
                introduction=plan_data['introduction'],
                sections=plan_data['sections'],
                time_allocation=plan_data['time_allocation'],
                key_points=plan_data['key_points']
            )

            # Show the emphasized plan for review
            state.requires_human_input = True
            state.checkpoint_id = "plan_review"
            state.draft_plan = state.refined_plan
            print("✓ Plan emphasized, requesting review...")

        except json.JSONDecodeError as e:
            print(f"⚠ Failed to parse refined plan: {e}")
            state.refined_plan = state.draft_plan
            state.requires_human_input = False
            state.checkpoint_id = None

    # Update state
    state.current_node = "refinement"

    # Log execution
    execution_time = (time.time() - start_time) * 1000
    execution_logger.log_node_execution(
        node_name="refinement_node",
        inputs={
            "feedback_decision": feedback.decision,
            "feedback_comments": feedback.comments
        },
        prompt=prompt if feedback.decision != "approve" else None,
        output={
            "plan_refined": True,
            "sections_count": len(state.refined_plan.sections),
            "requires_human_input": state.requires_human_input
        },
        model_settings=get_model_settings(),
        human_decision=feedback.decision,
        execution_time_ms=execution_time
    )

    if state.requires_human_input:
        print(f"⏸ Waiting for review of refined plan...")
    else:
        print(f"✓ Refinement completed, moving to next stage")

    return state