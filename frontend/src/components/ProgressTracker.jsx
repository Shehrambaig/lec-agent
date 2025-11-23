import { useState } from 'react';
import './ProgressTracker.css';

function ProgressTracker({ logs, currentNode, completedNodes = [], nodeTraces = {} }) {
  const [expandedNodes, setExpandedNodes] = useState({});

  const nodes = [
    'input',
    'plan',
    'search',
    'extract',
    'prioritize',
    'synthesize',
    'refine',
    'brief',
    'format'
  ];

  const getNodeStatus = (node) => {
    if (completedNodes.includes(node)) return 'completed';
    if (node === currentNode) return 'active';
    return 'pending';
  };

  const getNodeLabel = (node) => {
    const labels = {
      'input': 'Initialize',
      'plan': 'Research Plan',
      'search': 'Web Search',
      'extract': 'Extract Claims',
      'prioritize': 'Prioritize',
      'synthesize': 'Synthesize',
      'refine': 'Refine Plan',
      'brief': 'Generate Brief',
      'format': 'Format Output'
    };
    return labels[node] || node;
  };

  const toggleExpand = (node) => {
    setExpandedNodes(prev => ({
      ...prev,
      [node]: !prev[node]
    }));
  };

  const renderTraceDetails = (trace) => {
    if (!trace) return null;

    return (
      <div className="trace-details">
        {trace.details && trace.details.length > 0 && (
          <ul className="trace-list">
            {trace.details.map((detail, idx) => (
              <li key={idx}>{detail}</li>
            ))}
          </ul>
        )}

        {trace.search_queries && (
          <div className="trace-section">
            <strong>Search Queries:</strong>
            <ul className="trace-queries">
              {trace.search_queries.map((q, idx) => (
                <li key={idx}>{q}</li>
              ))}
            </ul>
          </div>
        )}

        {trace.research_angles && (
          <div className="trace-section">
            <strong>Research Angles:</strong>
            <div className="trace-angles">
              {trace.research_angles.map((angle, idx) => (
                <div key={idx} className="trace-angle">
                  <span className="angle-title">{angle.title}</span>
                  <span className="angle-desc">{angle.description}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {trace.queries_executed && (
          <div className="trace-section">
            <strong>Queries Executed:</strong>
            <ul className="trace-queries">
              {trace.queries_executed.map((q, idx) => (
                <li key={idx}>{q}</li>
              ))}
            </ul>
          </div>
        )}

        {trace.sample_results && trace.sample_results.length > 0 && (
          <div className="trace-section">
            <strong>Sample Results:</strong>
            <div className="trace-results">
              {trace.sample_results.map((r, idx) => (
                <div key={idx} className="trace-result">
                  <a href={r.url} target="_blank" rel="noopener noreferrer">
                    {r.title || r.url}
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {trace.sample_claims && trace.sample_claims.length > 0 && (
          <div className="trace-section">
            <strong>Sample Claims:</strong>
            <div className="trace-claims">
              {trace.sample_claims.map((c, idx) => (
                <div key={idx} className="trace-claim">
                  <span className="claim-text">{c.claim}</span>
                  <span className="claim-confidence">
                    {(c.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {trace.top_claims && trace.top_claims.length > 0 && (
          <div className="trace-section">
            <strong>Top Prioritized Claims:</strong>
            <div className="trace-claims">
              {trace.top_claims.map((c, idx) => (
                <div key={idx} className="trace-claim">
                  <span className="claim-text">{c.claim}</span>
                  <span className="claim-meta">
                    {(c.confidence * 100).toFixed(0)}% | {c.source}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {trace.sections && (
          <div className="trace-section">
            <strong>Lecture Sections:</strong>
            <ul className="trace-sections">
              {trace.sections.map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="progress-tracker">
      <h3>Execution Progress</h3>

      <div className="node-progress">
        {nodes.map((node) => {
          const status = getNodeStatus(node);
          const trace = nodeTraces[node];
          const hasTrace = trace && (trace.details?.length > 0 || trace.search_queries || trace.sample_results);
          const isExpanded = expandedNodes[node];

          return (
            <div key={node} className={`node-item ${status}`}>
              <div
                className={`node-header ${hasTrace ? 'expandable' : ''}`}
                onClick={() => hasTrace && toggleExpand(node)}
              >
                <div className="node-indicator">
                  {status === 'completed' && 'Done'}
                  {status === 'active' && '...'}
                  {status === 'pending' && '-'}
                </div>
                <div className="node-label">{getNodeLabel(node)}</div>
                {hasTrace && (
                  <div className="node-expand-icon">
                    {isExpanded ? '▼' : '▶'}
                  </div>
                )}
              </div>
              {isExpanded && renderTraceDetails(trace)}
            </div>
          );
        })}
      </div>

      <div className="logs-section">
        <h4>Activity Log</h4>
        <div className="logs-container">
          {logs.map((log, idx) => (
            <div key={idx} className={`log-entry log-${log.type}`}>
              <span className="log-time">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span className="log-message">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default ProgressTracker;
