import time
import json
from backend.state import ResearchState, Citation
from backend.utils import google_search, call_openai, load_prompt, get_model_settings
from backend.logger import execution_logger


def search_node(state: ResearchState) -> ResearchState:
    """
    Search node: Use approved research plan queries to perform web searches.

    This node:
    - Uses the search queries from the approved research plan
    - Performs Google searches
    - Collects and structures results
    - Creates citation objects
    """
    start_time = time.time()

    # Use search queries from the approved research plan
    if state.research_plan and state.research_plan.search_queries:
        search_queries = state.research_plan.search_queries
        print(f"⚙ Using approved research plan queries for: {state.topic}")
        print(f"  📋 Plan revision: #{state.research_plan.revision_count}")
    else:
        # Fallback: generate queries if no research plan exists
        print(f"⚠ No research plan found, generating fallback queries for: {state.topic}")
        search_queries = [
            state.topic,
            f"{state.topic} research papers",
            f"{state.topic} risks challenges",
            f"{state.topic} industry applications",
            f"{state.topic} expert analysis"
        ]

    state.search_queries = search_queries
    print(f"✓ Using {len(search_queries)} search queries from approved plan")
    
    # Perform searches
    all_results = []
    citation_id = 1
    
    for query in search_queries[:5]:  # Limit to 5 queries to avoid API limits
        print(f"  🔍 Searching: {query}")
        results = google_search(query, num_results=5)
        
        for result in results:
            # Create citation
            citation = Citation(
                id=citation_id,
                title=result['title'],
                url=result['link'],
                snippet=result['snippet'],
                relevance_score=0.8  # Will be refined in prioritization
            )
            state.citations.append(citation)
            
            # Add to results
            result['citation_id'] = citation_id
            all_results.append(result)
            citation_id += 1
    
    state.search_results = all_results
    
    # Update state
    state.current_node = "search"
    
    # Log execution
    execution_time = (time.time() - start_time) * 1000
    execution_logger.log_node_execution(
        node_name="search_node",
        inputs={
            "topic": state.topic,
            "plan_revision": state.research_plan.revision_count if state.research_plan else 0
        },
        prompt="Using approved research plan queries",
        output={
            "queries": search_queries,
            "results_count": len(all_results),
            "citations_count": len(state.citations)
        },
        model_settings=get_model_settings(),
        execution_time_ms=execution_time
    )
    
    print(f"✓ Search completed: {len(all_results)} results, {len(state.citations)} citations")
    
    return state
