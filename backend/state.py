from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Citation(BaseModel):
    """A single citation with source information."""
    id: int
    title: str
    url: str
    snippet: str
    relevance_score: float = 0.0


class ExtractedClaim(BaseModel):
    """An extracted factual claim from research."""
    claim: str
    source: str
    citation_id: int
    confidence: float
    author: Optional[str] = None
    date: Optional[str] = None


class ResearchPlan(BaseModel):
    """Research action plan generated before conducting searches."""
    search_queries: List[str]
    research_angles: List[Dict[str, str]]  # Each angle has 'title' and 'description'
    topic: str
    revision_count: int = 0
    revision_feedback: Optional[str] = None


class DraftPlan(BaseModel):
    """Initial lecture plan structure."""
    introduction: str
    sections: List[Dict[str, Any]]
    time_allocation: Dict[str, int]
    key_points: List[str]


class HumanFeedback(BaseModel):
    """Feedback from human-in-the-loop checkpoint."""
    checkpoint_type: str  # "plan_review", "plan_approval", or "fact_verification"
    decision: str  # "approve", "request_more_sources", "emphasize_topic", "rework", "reject"
    comments: Optional[str] = None
    emphasis_areas: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ResearchState(BaseModel):
    """Complete state for the research graph workflow."""
    # Input
    topic: str
    user_id: str = "default_user"

    # Research Planning (before search)
    research_plan: Optional[ResearchPlan] = None
    human_feedback_research_plan: Optional[HumanFeedback] = None
    plan_approved: bool = False

    # Search & Extraction
    search_queries: List[str] = []
    search_results: List[Dict[str, Any]] = []
    citations: List[Citation] = []
    extracted_claims: List[ExtractedClaim] = []
    prioritized_claims: List[ExtractedClaim] = []

    # Planning & Synthesis
    draft_plan: Optional[DraftPlan] = None
    human_feedback_plan: Optional[HumanFeedback] = None  # Feedback on facts before synthesis
    human_feedback_approval: Optional[HumanFeedback] = None  # Feedback on generated plan
    refined_plan: Optional[DraftPlan] = None

    # Fact Verification
    facts_for_verification: List[ExtractedClaim] = []
    human_feedback_facts: Optional[HumanFeedback] = None  # Feedback on facts after refinement

    # Final Output
    final_brief: Optional[str] = None
    formatted_brief: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    current_node: str = "input"
    execution_log: List[Dict[str, Any]] = []

    # Control Flow
    requires_human_input: bool = False
    checkpoint_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NodeLog(BaseModel):
    """Log entry for a single node execution."""
    node_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    inputs: Dict[str, Any]
    prompt: Optional[str] = None
    output: Any
    model_settings: Dict[str, Any] = {}
    human_decision: Optional[str] = None
    execution_time_ms: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }