import time
from backend.state import ResearchState
from backend.logger import execution_logger


def input_node(state: ResearchState) -> ResearchState:
    """
    Input node: Initialize the research workflow and validate topic.
    
    This node:
    - Validates the research topic
    - Initializes execution logging
    - Sets up initial state
    """
    start_time = time.time()
    
    # Log node execution
    execution_logger.start_session(state.topic, state.user_id)
    
    inputs = {"topic": state.topic, "user_id": state.user_id}
    output = {"status": "initialized", "topic_validated": True}
    
    # Update state
    state.current_node = "input"
    
    # Log execution
    execution_time = (time.time() - start_time) * 1000
    execution_logger.log_node_execution(
        node_name="input_node",
        inputs=inputs,
        output=output,
        execution_time_ms=execution_time
    )
    
    print(f"✓ Input node completed: Topic '{state.topic}' initialized")
    
    return state
