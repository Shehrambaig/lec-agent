import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import InputForm from './components/InputForm';
import ResearchPlanReview from './components/ResearchPlanReview';
import PlanReview from './components/PlanReview';
import PlanApproval from './components/PlanApproval';
import FactVerification from './components/FactVerification';
import ProgressTracker from './components/ProgressTracker';
import './App.css';

// API configuration - uses environment variable in production
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [ws, setWs] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, running, waiting_research_plan, waiting_plan, waiting_approval, waiting_facts, complete
  const [currentNode, setCurrentNode] = useState('');
  const [completedNodes, setCompletedNodes] = useState([]);
  const [checkpoint, setCheckpoint] = useState(null);
  const [checkpointData, setCheckpointData] = useState(null);
  const [logs, setLogs] = useState([]);
  const [nodeTraces, setNodeTraces] = useState({});
  const [completedBrief, setCompletedBrief] = useState(null);
  const [showOutputModal, setShowOutputModal] = useState(false);
  const [slidesFile, setSlidesFile] = useState(null);

  const addLog = (message, type = 'info') => {
    setLogs(prev => [...prev, { message, type, timestamp: new Date().toISOString() }]);
  };

  const startResearch = async (topic) => {
    try {
      addLog(`Starting research on: ${topic}`, 'info');

      // Create session
      const response = await fetch(`${API_URL}/research/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic })
      });

      const data = await response.json();
      setSessionId(data.session_id);
      addLog(`Session created: ${data.session_id}`, 'success');

      // Connect WebSocket
      const websocket = new WebSocket(`${WS_URL}/ws/${data.session_id}`);

      websocket.onopen = () => {
        addLog('WebSocket connected', 'success');
        setStatus('running');
      };

      websocket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      };

      websocket.onerror = (error) => {
        addLog('WebSocket error: ' + error, 'error');
      };

      websocket.onclose = () => {
        addLog('WebSocket closed', 'info');
      };

      setWs(websocket);

    } catch (error) {
      addLog(`Error: ${error.message}`, 'error');
    }
  };

  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'status':
        addLog(message.message, 'info');
        break;

      case 'node_complete':
        addLog(`Node completed: ${message.node}`, 'success');
        setCurrentNode(message.state?.current_node || message.node);
        // Add to completed nodes if not already there
        setCompletedNodes(prev => {
          if (!prev.includes(message.node)) {
            return [...prev, message.node];
          }
          return prev;
        });
        // Store trace data for this node
        if (message.trace) {
          setNodeTraces(prev => ({
            ...prev,
            [message.node]: message.trace
          }));
        }
        break;

      case 'hitl_required':
        addLog(`Waiting for human input: ${message.checkpoint}`, 'warning');
        setCheckpoint(message.checkpoint);
        setCheckpointData(message.data);

        // Set appropriate status based on checkpoint type
        if (message.checkpoint === 'research_plan') {
          setStatus('waiting_research_plan');
        } else if (message.checkpoint === 'plan_review') {
          setStatus('waiting_plan');
        } else if (message.checkpoint === 'plan_approval') {
          setStatus('waiting_approval');
        } else if (message.checkpoint === 'fact_verification') {
          setStatus('waiting_facts');
        }
        break;

      case 'complete':
        addLog('Research complete!', 'success');
        setStatus('complete');
        setCompletedBrief(message.brief_content || message.brief_preview);
        setSlidesFile(message.slides_file || null);
        setShowOutputModal(true);
        break;

      case 'error':
        addLog(`Error: ${message.message}`, 'error');
        break;
    }
  };

  const submitFeedback = async (checkpointType, decision, comments = null, emphasisAreas = null) => {
    try {
      addLog(`Submitting feedback: ${decision}`, 'info');

      const response = await fetch(`${API_URL}/research/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          checkpoint_type: checkpointType,
          decision,
          comments,
          emphasis_areas: emphasisAreas
        })
      });

      const data = await response.json();
      addLog('Feedback submitted, continuing...', 'success');
      setStatus('running');
      setCheckpoint(null);
      setCheckpointData(null);

    } catch (error) {
      addLog(`Error submitting feedback: ${error.message}`, 'error');
    }
  };

  const downloadBrief = () => {
    const blob = new Blob([completedBrief], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research-brief-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadSlides = () => {
    if (!slidesFile) {
      addLog('No slides file available', 'error');
      return;
    }

    // Extract filename from path (e.g., "outputs/slides_topic_timestamp.pptx" -> "slides_topic_timestamp.pptx")
    const filename = slidesFile.split('/').pop();

    // Open download URL in new tab
    const downloadUrl = `${API_URL}/download/slides/${filename}`;
    window.open(downloadUrl, '_blank');
    addLog('Downloading slides...', 'success');
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Lecture Assistant Agent</h1>
        <p>LangGraph + Human-in-the-Loop Research System</p>
      </header>

      <div className="app-container">
        <div className="main-panel">
          {status === 'idle' && (
            <InputForm onSubmit={startResearch} />
          )}

          {status === 'waiting_research_plan' && checkpointData && (
            <ResearchPlanReview
              researchPlan={checkpointData.research_plan}
              onSubmit={(decision, comments) =>
                submitFeedback('research_plan', decision, comments)
              }
            />
          )}

          {status === 'waiting_plan' && checkpointData && (
            <PlanReview
              draftPlan={checkpointData.draft_plan}
              facts={checkpointData.facts_for_verification}
              onSubmit={(decision, comments, emphasisAreas) =>
                submitFeedback('plan_review', decision, comments, emphasisAreas)
              }
            />
          )}

          {status === 'waiting_approval' && checkpointData && (
            <PlanApproval
              draftPlan={checkpointData.draft_plan}
              onSubmit={(decision, comments) =>
                submitFeedback('plan_approval', decision, comments)
              }
            />
          )}

          {status === 'waiting_facts' && checkpointData && (
            <FactVerification
              facts={checkpointData.facts}
              onSubmit={(decision, comments) =>
                submitFeedback('fact_verification', decision, comments)
              }
            />
          )}

          {status === 'running' && (
            <div className="status-panel">
              <h2>Research in Progress</h2>
              <p className="current-node">Current node: <strong>{currentNode}</strong></p>
              <div className="spinner"></div>
            </div>
          )}

          {status === 'complete' && !showOutputModal && (
            <div className="complete-panel">
              <h2>Research Complete</h2>
              <p>Your research brief has been generated.</p>
              <button onClick={() => setShowOutputModal(true)} className="btn-primary">
                View Output
              </button>
              <button onClick={() => window.location.reload()} className="btn-secondary">
                Start New Research
              </button>
            </div>
          )}
        </div>

        <div className="side-panel">
          <ProgressTracker
            logs={logs}
            currentNode={currentNode}
            completedNodes={completedNodes}
            nodeTraces={nodeTraces}
          />
        </div>
      </div>

      {/* Output Modal */}
      {showOutputModal && completedBrief && (
        <div className="modal-overlay" onClick={() => setShowOutputModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Research Brief Output</h2>
              <button className="modal-close" onClick={() => setShowOutputModal(false)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="markdown-content">
                <ReactMarkdown>{completedBrief}</ReactMarkdown>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={downloadBrief} className="btn-primary">
                Download Brief (.md)
              </button>
              {slidesFile && (
                <button onClick={downloadSlides} className="btn-primary">
                  Download Slides (.pptx)
                </button>
              )}
              <button onClick={() => setShowOutputModal(false)} className="btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;