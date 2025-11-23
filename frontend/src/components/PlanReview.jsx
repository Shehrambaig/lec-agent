import { useState } from 'react';
import './PlanReview.css';

function PlanReview({ draftPlan, facts, onSubmit }) {
  const [decision, setDecision] = useState('');
  const [comments, setComments] = useState('');
  const [emphasisAreas, setEmphasisAreas] = useState([]);

  const handleSubmit = () => {
    if (decision) {
      onSubmit(decision, comments || null, emphasisAreas.length > 0 ? emphasisAreas : null);
    }
  };

  const toggleEmphasis = (area) => {
    setEmphasisAreas(prev =>
      prev.includes(area)
        ? prev.filter(a => a !== area)
        : [...prev, area]
    );
  };

  return (
    <div className="plan-review">
      <h2>📋 Plan Review Required</h2>
      <p className="subtitle">Review the key facts found and provide direction for the lecture plan</p>

      {/* Only show draft plan if it exists */}
      {draftPlan && (
        <div className="plan-content">
          <h3>Draft Lecture Plan</h3>

          {draftPlan.introduction && (
            <div className="plan-section">
              <h4>Introduction</h4>
              <p>{draftPlan.introduction}</p>
            </div>
          )}

          {draftPlan.sections && draftPlan.sections.map((section, idx) => (
            <div key={idx} className="plan-section">
              <h4>{section.title} ({section.time_minutes} min)</h4>
              <ul>
                {section.key_points && section.key_points.map((point, pidx) => (
                  <li key={pidx}>{point}</li>
                ))}
              </ul>
            </div>
          ))}

          {draftPlan.time_allocation && (
            <div className="time-allocation">
              <h4>Time Allocation</h4>
              <ul>
                {Object.entries(draftPlan.time_allocation).map(([key, value]) => (
                  <li key={key}>{key}: {value} minutes</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Always show facts */}
      <div className="facts-preview">
        <h3>Key Facts Found ({facts?.length || 0})</h3>
        {facts && facts.length > 0 ? (
          facts.slice(0, 6).map((fact, idx) => (
            <div key={idx} className="fact-item">
              <p><strong>Claim #{idx + 1}:</strong> {fact.claim}</p>
              <span className="fact-meta">
                Source: {fact.source || 'N/A'} |
                Confidence: {fact.confidence ? (fact.confidence * 100).toFixed(0) : 0}%
              </span>
            </div>
          ))
        ) : (
          <p className="no-facts">No facts available for review.</p>
        )}
      </div>

      <div className="feedback-section">
        <h3>Your Feedback</h3>

        <div className="decision-buttons">
          <button
            className={`decision-btn ${decision === 'approve' ? 'active' : ''}`}
            onClick={() => setDecision('approve')}
          >
            ✅ Approve & Continue
          </button>
          <button
            className={`decision-btn ${decision === 'request_more_sources' ? 'active' : ''}`}
            onClick={() => setDecision('request_more_sources')}
          >
            🔍 Need More Sources
          </button>
          <button
            className={`decision-btn ${decision === 'emphasize_topic' ? 'active' : ''}`}
            onClick={() => setDecision('emphasize_topic')}
          >
            🎯 Emphasize Topics
          </button>
          <button
            className={`decision-btn ${decision === 'rework' ? 'active' : ''}`}
            onClick={() => setDecision('rework')}
          >
            🔄 Rework & Research More
          </button>
        </div>

        {decision === 'emphasize_topic' && (
          <div className="emphasis-selection">
            <h4>Select areas to emphasize:</h4>
            <div className="emphasis-chips">
              {['Applications', 'Risks', 'Examples', 'Ethics', 'Technical Details', 'Recent Developments'].map(area => (
                <button
                  key={area}
                  className={`chip ${emphasisAreas.includes(area) ? 'active' : ''}`}
                  onClick={() => toggleEmphasis(area)}
                >
                  {area}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="form-group">
          <label>Additional Comments (Optional)</label>
          <textarea
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            placeholder="Provide any specific feedback, topics to emphasize, or areas to explore..."
            rows="4"
          />
        </div>

        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={!decision}
        >
          Submit Feedback & Continue
        </button>
      </div>
    </div>
  );
}

export default PlanReview;