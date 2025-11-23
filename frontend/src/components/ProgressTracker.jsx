import './ProgressTracker.css';

function ProgressTracker({ logs, currentNode, completedNodes = [] }) {
  const nodes = [
    'input',
    'search',
    'extract',
    'prioritize',
    'synthesize',
    'wait_plan_review',
    'refine',
    'wait_fact_verification',
    'brief',
    'format'
  ];

  const getNodeStatus = (node) => {
    // Check if node is completed
    if (completedNodes.includes(node)) return 'completed';
    // Check if node is currently active
    if (node === currentNode) return 'active';
    // Otherwise it's pending
    return 'pending';
  };

  const getNodeLabel = (node) => {
    const labels = {
      'input': 'Input',
      'search': 'Search',
      'extract': 'Extract',
      'prioritize': 'Prioritize',
      'synthesize': 'Synthesize',
      'wait_plan_review': 'Plan Review (HITL)',
      'refine': 'Refine',
      'wait_fact_verification': 'Fact Check (HITL)',
      'brief': 'Generate Brief',
      'format': 'Format'
    };
    return labels[node] || node;
  };

  return (
    <div className="progress-tracker">
      <h3>Execution Progress</h3>
      
      <div className="node-progress">
        {nodes.map((node, idx) => (
          <div key={node} className={`node-item ${getNodeStatus(node)}`}>
            <div className="node-indicator">
              {getNodeStatus(node) === 'completed' && '✓'}
              {getNodeStatus(node) === 'active' && '●'}
              {getNodeStatus(node) === 'pending' && '○'}
            </div>
            <div className="node-label">{getNodeLabel(node)}</div>
          </div>
        ))}
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
