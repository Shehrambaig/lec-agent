import time
import os
from datetime import datetime
from backend.state import ResearchState
from backend.logger import execution_logger


def formatting_node(state: ResearchState) -> ResearchState:
    """
    Formatting node: Final formatting and file export.
    
    This node:
    - Ensures proper Markdown formatting
    - Saves brief to file
    - Adds metadata
    """
    start_time = time.time()
    
    print(f"⚙ Formatting and saving brief...")
    
    # Add metadata header
    metadata = f"""<!-- 
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Topic: {state.topic}
Session: {execution_logger.current_session_id}
-->

"""
    
    formatted_brief = metadata + state.final_brief
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"brief_{state.topic.replace(' ', '_')}_{timestamp}.md"
    filepath = os.path.join("outputs", filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(formatted_brief)
    
    state.formatted_brief = formatted_brief
    
    # Update state
    state.current_node = "formatting"
    
    # Log execution
    execution_time = (time.time() - start_time) * 1000
    execution_logger.log_node_execution(
        node_name="formatting_node",
        inputs={"brief_length": len(state.final_brief)},
        output={
            "file_saved": filepath,
            "formatted": True
        },
        execution_time_ms=execution_time
    )
    
    # End logging session
    execution_logger.end_session(final_output=filepath)
    
    print(f"✓ Brief saved to: {filepath}")
    
    return state
