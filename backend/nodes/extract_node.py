import time
import json
from backend.state import ResearchState, ExtractedClaim
from backend.utils import call_openai, load_prompt, get_model_settings
from backend.logger import execution_logger


def extract_node(state: ResearchState) -> ResearchState:
    """
    Extract node: Extract factual claims from search results.
    
    This node:
    - Analyzes search results
    - Extracts key factual claims
    - Links claims to citations
    - Assigns confidence scores
    """
    start_time = time.time()
    
    # Prepare search results summary
    results_summary = ""
    for idx, result in enumerate(state.search_results[:20], 1):  # Limit to first 20
        results_summary += f"\n[Result {idx}]\n"
        results_summary += f"Title: {result['title']}\n"
        results_summary += f"Snippet: {result['snippet']}\n"
        results_summary += f"Citation ID: {result['citation_id']}\n"
    
    # Load prompt template
    prompt_template = load_prompt("extract_prompt")
    prompt = prompt_template.format(
        topic=state.topic,
        search_results=results_summary
    )
    
    print(f"⚙ Extracting factual claims...")
    claims_response = call_openai(prompt, max_tokens=2000)
    
    # Parse claims
    try:
        claims_str = claims_response.strip()
        if "```json" in claims_str:
            claims_str = claims_str.split("```json")[1].split("```")[0].strip()
        elif "```" in claims_str:
            claims_str = claims_str.split("```")[1].split("```")[0].strip()
        
        claims_data = json.loads(claims_str)

        # Build a set of valid citation IDs for validation
        valid_citation_ids = {r['citation_id'] for r in state.search_results}
        default_citation_id = state.search_results[0]['citation_id'] if state.search_results else 1

        # Create ExtractedClaim objects
        for claim_data in claims_data:
            # Use citation_id from LLM response, validate it exists, fallback to default
            citation_id = claim_data.get('citation_id', default_citation_id)
            if citation_id not in valid_citation_ids:
                citation_id = default_citation_id

            claim = ExtractedClaim(
                claim=claim_data['claim'],
                source=claim_data['source'],
                citation_id=citation_id,
                confidence=claim_data.get('confidence', 0.7),
                author=claim_data.get('author'),
                date=claim_data.get('date')
            )
            state.extracted_claims.append(claim)
    
    except json.JSONDecodeError as e:
        print(f"⚠ Failed to parse claims: {e}")
        # Create fallback claims from search snippets
        for result in state.search_results[:8]:
            claim = ExtractedClaim(
                claim=result['snippet'],
                source=result['title'],
                citation_id=result['citation_id'],
                confidence=0.6
            )
            state.extracted_claims.append(claim)
    
    # Update state
    state.current_node = "extract"
    
    # Log execution
    execution_time = (time.time() - start_time) * 1000
    execution_logger.log_node_execution(
        node_name="extract_node",
        inputs={"search_results_count": len(state.search_results)},
        prompt=prompt,
        output={"extracted_claims_count": len(state.extracted_claims)},
        model_settings=get_model_settings(),
        execution_time_ms=execution_time
    )
    
    print(f"✓ Extraction completed: {len(state.extracted_claims)} claims extracted")
    
    return state
