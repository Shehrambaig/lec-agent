import time
from typing import List
from backend.state import ResearchState, ExtractedClaim
from backend.logger import execution_logger


def author_prioritization_node(state: ResearchState) -> ResearchState:
    """
    Author Prioritization node: Rank and prioritize extracted claims.

    This node:
    - Scores claims based on confidence, recency, author credibility
    - Prioritizes claims for synthesis
    - Identifies top claims for fact verification

    Note: The graph will automatically pause before 'synthesize' node
    due to interrupt_before configuration for plan review.
    """
    start_time = time.time()

    print(f"⚙ Prioritizing {len(state.extracted_claims)} claims...")

    # Score claims
    scored_claims: List[tuple[float, ExtractedClaim]] = []

    for claim in state.extracted_claims:
        score = 0.0

        # Base confidence score
        score += claim.confidence * 40

        # Author bonus
        if claim.author:
            score += 20

        # Recency bonus (if date available and recent)
        if claim.date:
            try:
                if '2024' in claim.date or '2025' in claim.date:
                    score += 15
                elif '2023' in claim.date or '2022' in claim.date:
                    score += 10
            except:
                pass

        # Length bonus (detailed claims are valuable)
        if len(claim.claim) > 100:
            score += 10

        # Specificity bonus (contains numbers/data)
        if any(char.isdigit() for char in claim.claim):
            score += 15

        scored_claims.append((score, claim))

    # Sort by score descending
    scored_claims.sort(key=lambda x: x[0], reverse=True)

    # Take top claims for prioritization
    state.prioritized_claims = [claim for score, claim in scored_claims[:12]]

    # Select top 6 for fact verification HITL
    state.facts_for_verification = [claim for score, claim in scored_claims[:6]]

    # Update state
    state.current_node = "author_prioritization"

    # DON'T set HITL flags here - interrupt_before handles the pause
    # The graph will automatically pause before synthesize node
    # state.requires_human_input = True  # NOT NEEDED
    # state.checkpoint_id = "plan_review"  # NOT NEEDED

    # Log execution
    execution_time = (time.time() - start_time) * 1000
    execution_logger.log_node_execution(
        node_name="author_prioritization_node",
        inputs={"claims_count": len(state.extracted_claims)},
        output={
            "prioritized_count": len(state.prioritized_claims),
            "verification_count": len(state.facts_for_verification),
            "top_scores": [score for score, _ in scored_claims[:6]]
        },
        execution_time_ms=execution_time
    )

    print(
        f"✓ Prioritization completed: {len(state.prioritized_claims)} prioritized, {len(state.facts_for_verification)} for verification")
    print(f"📌 Ready for plan review - graph will pause before synthesis")

    return state