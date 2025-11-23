import time
import json
from backend.state import ResearchState, Citation
from backend.utils import google_search, call_openai, load_prompt, get_model_settings
from backend.logger import execution_logger


def search_node(state: ResearchState) -> ResearchState:
    """
    Search node: Generate search queries and perform web searches.
    
    This node:
    - Uses LLM to generate targeted search queries
    - Performs Google searches
    - Collects and structures results
    - Creates citation objects
    """
    start_time = time.time()
    
    # Load prompt template
    prompt_template = load_prompt("search_prompt")
    prompt = prompt_template.format(topic=state.topic)
    
    # Generate search queries using LLM
    print(f"⚙ Generating search queries for: {state.topic}")
    queries_response = call_openai(prompt, max_tokens=500)
    
    # Parse queries
    try:
        # Try to extract JSON from response
        queries_str = queries_response.strip()
        if "```json" in queries_str:
            queries_str = queries_str.split("```json")[1].split("```")[0].strip()
        elif "```" in queries_str:
            queries_str = queries_str.split("```")[1].split("```")[0].strip()
        
        search_queries = json.loads(queries_str)
    except json.JSONDecodeError:
        # Fallback: use topic-based queries
        print("⚠ Failed to parse LLM queries, using fallback")
        search_queries = [
            state.topic,
            f"{state.topic} research papers",
            f"{state.topic} risks challenges",
            f"{state.topic} industry applications",
            f"{state.topic} expert analysis"
        ]
    
    state.search_queries = search_queries
    print(f"✓ Generated {len(search_queries)} search queries")
    
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
        inputs={"topic": state.topic},
        prompt=prompt,
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
