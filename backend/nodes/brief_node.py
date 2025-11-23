import time
import json
from backend.state import ResearchState
from backend.utils import call_openai, load_prompt, get_model_settings
from backend.logger import execution_logger


def brief_node(state: ResearchState) -> ResearchState:
    """
    Brief node: Generate final research brief in Markdown format.
    
    This node:
    - Takes refined plan and verified facts
    - Generates comprehensive research brief
    - Includes proper citations
    - Formats in Markdown
    """
    start_time = time.time()
    
    print(f"⚙ Generating final research brief...")
    
    # Prepare verified claims (or use prioritized if no verification feedback)
    verified_claims = state.prioritized_claims
    
    claims_summary = ""
    for idx, claim in enumerate(verified_claims, 1):
        claims_summary += f"\n[Claim {idx}]\n"
        claims_summary += f"Content: {claim.claim}\n"
        claims_summary += f"Source: {claim.source}\n"
        claims_summary += f"Citation ID: {claim.citation_id}\n"
    
    # Prepare citations
    citations_list = ""
    for citation in state.citations[:20]:  # Limit to prevent context overflow
        citations_list += f"\n[{citation.id}] {citation.title}\n"
        citations_list += f"    URL: {citation.url}\n"
        citations_list += f"    Snippet: {citation.snippet[:100]}...\n"
    
    # Load prompt template
    prompt_template = load_prompt("brief_prompt")
    prompt = prompt_template.format(
        topic=state.topic,
        refined_plan=json.dumps(state.refined_plan.dict(), indent=2) if state.refined_plan else "{}",
        verified_claims=claims_summary,
        citations=citations_list
    )
    
    brief_response = call_openai(prompt, max_tokens=3000)
    
    state.final_brief = brief_response
    
    # Update state
    state.current_node = "brief"
    state.requires_human_input = False
    
    # Log execution
    execution_time = (time.time() - start_time) * 1000
    execution_logger.log_node_execution(
        node_name="brief_node",
        inputs={
            "verified_claims_count": len(verified_claims),
            "citations_count": len(state.citations)
        },
        prompt=prompt,
        output={
            "brief_length": len(brief_response),
            "brief_generated": True
        },
        model_settings=get_model_settings(),
        execution_time_ms=execution_time
    )
    
    print(f"✓ Brief generation completed ({len(brief_response)} characters)")
    
    return state
