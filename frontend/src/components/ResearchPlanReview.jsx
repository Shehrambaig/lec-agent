import { useState } from 'react';
import './ResearchPlanReview.css';

function ResearchPlanReview({ researchPlan, onSubmit }) {
  const [decision, setDecision] = useState('');
  const [comments, setComments] = useState('');

  const handleSubmit = () => {
    if (decision) {
      onSubmit(decision, comments || null);
    }
  };

  const revisionCount = researchPlan?.revision_count || 0;

  return (
    <div className="research-plan-review">
      <h2>Research Plan Review</h2>
      <p className="subtitle">
        Review the proposed research strategy before searches begin
        {revisionCount > 0 && (
          <span className="revision-badge">Revision #{revisionCount}</span>
        )}
      </p>

      {researchPlan?.revision_feedback && (
        <div className="revision-feedback-box">
          <h4>Previous Feedback</h4>
          <p>{researchPlan.revision_feedback}</p>
        </div>
      )}

      <div className="plan-content">
        <div className="plan-section">
          <h3>Proposed Search Queries</h3>
          <p className="section-description">
            These queries will be used to find relevant information:
          </p>
          <ol className="search-queries-list">
            {researchPlan?.search_queries?.map((query, idx) => (
              <li key={idx} className="search-query-item">
                {query}
              </li>
            ))}
          </ol>
        </div>

        <div className="plan-section">
          <h3>Research Angles</h3>
          <p className="section-description">
            The research will focus on these aspects of the topic:
          </p>
          <div className="research-angles-list">
            {researchPlan?.research_angles?.map((angle, idx) => (
              <div key={idx} className="research-angle-item">
                <h4>{angle.title}</h4>
                <p>{angle.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="feedback-section">
        <h3>Your Decision</h3>

        <div className="decision-buttons">
          <button
            className={`decision-btn approve ${decision === 'approve' ? 'active' : ''}`}
            onClick={() => setDecision('approve')}
          >
            Approve Plan
          </button>
          <button
            className={`decision-btn revise ${decision === 'revise' ? 'active' : ''}`}
            onClick={() => setDecision('revise')}
          >
            Request Revision
          </button>
        </div>

        {decision === 'revise' && (
          <div className="revision-input">
            <label>What changes would you like?</label>
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Describe what you'd like changed in the research plan...&#10;&#10;Examples:&#10;- Add more focus on historical context&#10;- Include queries about specific actors/organizations&#10;- Cover the economic impact angle"
              rows="5"
            />
          </div>
        )}

        {decision === 'approve' && (
          <div className="approval-note">
            <p>The research will proceed with the queries and angles shown above.</p>
          </div>
        )}

        <button
          className="btn-primary submit-btn"
          onClick={handleSubmit}
          disabled={!decision || (decision === 'revise' && !comments.trim())}
        >
          {decision === 'approve' ? 'Approve & Start Research' : 'Submit Revision Request'}
        </button>
      </div>
    </div>
  );
}

export default ResearchPlanReview;
