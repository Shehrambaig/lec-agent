import { useState } from 'react';
import './PlanApproval.css';

function PlanApproval({ draftPlan, onSubmit }) {
  const [decision, setDecision] = useState('');
  const [comments, setComments] = useState('');

  const handleSubmit = () => {
    if (!decision) {
      alert('Please make a decision');
      return;
    }
    onSubmit(decision, comments || null);
  };

  return (
    <div className="plan-approval-container">
      <h2>Plan Approval Required</h2>
      <p className="subtitle">Please review the generated lecture plan</p>

      <div className="plan-content">
        <h3>Draft Lecture Plan:</h3>
        <pre className="plan-text">{draftPlan || 'No plan available'}</pre>
      </div>

      <div className="feedback-section">
        <h3>Your Decision:</h3>

        <div className="decision-buttons">
          <button
            className={`decision-btn approve ${decision === 'approve' ? 'active' : ''}`}
            onClick={() => setDecision('approve')}
          >
            Approve Plan
          </button>
          <button
            className={`decision-btn rework ${decision === 'rework' ? 'active' : ''}`}
            onClick={() => setDecision('rework')}
          >
            Request Rework
          </button>
          <button
            className={`decision-btn reject ${decision === 'reject' ? 'active' : ''}`}
            onClick={() => setDecision('reject')}
          >
            Reject
          </button>
        </div>

        <div className="comments-section">
          <label>Additional Comments (optional):</label>
          <textarea
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            placeholder="Provide specific feedback or suggestions..."
            rows={4}
          />
        </div>

        <button
          className="submit-btn"
          onClick={handleSubmit}
          disabled={!decision}
        >
          Submit Decision
        </button>
      </div>
    </div>
  );
}

export default PlanApproval;