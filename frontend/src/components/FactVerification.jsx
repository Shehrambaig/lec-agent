import { useState } from 'react';
import './FactVerification.css';

function FactVerification({ facts, onSubmit }) {
  const [decision, setDecision] = useState('');
  const [comments, setComments] = useState('');

  const handleSubmit = () => {
    if (decision) {
      onSubmit(decision, comments || null);
    }
  };

  return (
    <div className="fact-verification">
      <h2>Fact Verification</h2>
      <p className="subtitle">Review the key facts that will be used in the lecture</p>

      <div className="facts-list">
        {facts && facts.map((fact, idx) => (
          <div key={idx} className="fact-card">
            <div className="fact-number">{idx + 1}</div>
            <div className="fact-content">
              <p className="fact-claim">{fact.claim}</p>
              <div className="fact-details">
                <span className="fact-source">{fact.source}</span>
                <span className="fact-confidence">
                  Confidence: {(fact.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="verification-section">
        <h3>Verification Decision</h3>
        
        <div className="decision-buttons">
          <button 
            className={`decision-btn ${decision === 'approve' ? 'active' : ''}`}
            onClick={() => setDecision('approve')}
          >
            All Facts Verified
          </button>
          <button 
            className={`decision-btn ${decision === 'request_more_sources' ? 'active' : ''}`}
            onClick={() => setDecision('request_more_sources')}
          >
            Need More Verification
          </button>
          <button 
            className={`decision-btn ${decision === 'rework' ? 'active' : ''}`}
            onClick={() => setDecision('rework')}
          >
            Facts Need Review
          </button>
        </div>

        <div className="form-group">
          <label>Comments (Optional)</label>
          <textarea
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            placeholder="Note any concerns or specific facts that need attention..."
            rows="3"
          />
        </div>

        <button 
          className="btn-primary"
          onClick={handleSubmit}
          disabled={!decision}
        >
          Submit Verification
        </button>
      </div>
    </div>
  );
}

export default FactVerification;
