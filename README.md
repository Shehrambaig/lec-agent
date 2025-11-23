# Lecture Assistant Agent

A sophisticated AI-powered research system that generates comprehensive lecture briefs using **LangGraph** workflows with **Human-in-the-Loop (HITL)** checkpoints.

## Features

- **Automated Research**: Intelligent web search and fact extraction using GPT-4
- **Human-in-the-Loop**: Three critical checkpoints for research plan approval, fact review, and plan approval
- **Real-time Updates**: WebSocket-based communication for live progress tracking
- **Structured Output**: Professional markdown briefs with proper citations
- **Comprehensive Logging**: Detailed execution logs for audit and debugging
- **Dark Theme UI**: Clean black/grey enterprise interface
- **Render Deployment Ready**: Configured for easy cloud deployment

## Architecture

### Backend (FastAPI + LangGraph)
- **LangGraph Workflow**: Stateful multi-agent graph with conditional edges
- **State Management**: Pydantic models for type-safe state handling
- **Checkpoint System**: Memory-based persistence for workflow resumption
- **WebSocket Server**: Real-time bidirectional communication

### Frontend (React + Vite)
- **Dark Theme UI**: Clean black/grey enterprise interface
- **Real-time Updates**: Live progress tracking and node execution status
- **Interactive HITL**: User-friendly feedback forms for all checkpoints
- **Environment Configurable**: Supports local and production API URLs

### Graph Workflow

```
input -> plan -> [HITL: Research Plan Approval] -> search -> extract -> prioritize
-> [HITL: Fact Review] -> synthesize -> [HITL: Plan Approval] -> refine -> brief -> format -> END
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- OpenAI API Key
- Google Custom Search API Key & CSE ID

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd lecture-assistant-agent
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id_here
```

### 3. Backend Setup

```bash
# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### Start Backend Server

```bash
# From project root
uvicorn backend.main:app --reload
```

Backend will run on: `http://localhost:8000`

### Start Frontend Development Server

```bash
# From frontend directory
cd frontend
npm run dev
```

Frontend will run on: `http://localhost:5173`

## Usage

1. **Open Browser**: Navigate to `http://localhost:5173`

2. **Enter Topic**: Input your research topic (e.g., "Propagation of disinformation by LLMs")

3. **Start Research**: Click "Start Research" to begin the workflow

4. **Research Plan Approval (HITL #1)**:
   - Review the proposed search queries and research angles
   - Choose to approve or request revisions
   - Provide feedback for plan adjustments

5. **Fact Review (HITL #2)**:
   - Review extracted facts with sources and confidence scores
   - Options available:
     - **Approve**: Continue with current facts
     - **More Sources**: Request additional research
     - **Emphasize Topics**: Focus on specific areas
     - **Rework**: Request more research
   - Optionally provide comments

6. **Plan Approval (HITL #3)**:
   - Review the generated lecture plan
   - Approve, request rework, or reject
   - Provide specific feedback

7. **Completion**:
   - System generates final research brief
   - View rendered markdown output
   - Download as markdown file
   - Output also saved to `outputs/` directory

## Project Structure

```
lecture-assistant-agent/
├── backend/
│   ├── main.py                 # FastAPI app with WebSocket
│   ├── graph.py                # LangGraph workflow definition
│   ├── state.py                # Pydantic state models
│   ├── logger.py               # Execution logging
│   ├── utils.py                # OpenAI & Google Search helpers
│   ├── nodes/                  # Node implementations
│   │   ├── __init__.py
│   │   ├── input_node.py
│   │   ├── research_plan_node.py
│   │   ├── search_node.py
│   │   ├── extract_node.py
│   │   ├── author_prioritization_node.py
│   │   ├── synthesis_node.py
│   │   ├── refinement_node.py
│   │   ├── brief_node.py
│   │   └── formatting_node.py
│   └── prompts/                # LLM prompt templates
│       ├── research_plan_prompt.txt
│       ├── search_prompt.txt
│       ├── extract_prompt.txt
│       ├── synthesis_prompt.txt
│       ├── refinement_prompt.txt
│       └── brief_prompt.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main application
│   │   ├── App.css             # Global styles (dark theme)
│   │   ├── index.css           # Base styles
│   │   └── components/
│   │       ├── InputForm.jsx
│   │       ├── InputForm.css
│   │       ├── ResearchPlanReview.jsx
│   │       ├── ResearchPlanReview.css
│   │       ├── PlanReview.jsx
│   │       ├── PlanReview.css
│   │       ├── PlanApproval.jsx
│   │       ├── PlanApproval.css
│   │       ├── FactVerification.jsx
│   │       ├── FactVerification.css
│   │       ├── ProgressTracker.jsx
│   │       └── ProgressTracker.css
│   ├── vite.config.js
│   └── package.json
├── logs/                       # Execution logs (JSON)
├── checkpoints/                # LangGraph checkpoints
├── outputs/                    # Generated briefs (Markdown)
├── render.yaml                 # Render deployment config
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Deployment

### Render Deployment

This project includes a `render.yaml` for easy deployment to Render.

#### Using Blueprint (Recommended)

1. Push your code to GitHub
2. Go to [render.com](https://render.com) and sign in
3. Click **New** > **Blueprint**
4. Connect your GitHub repo
5. Render will auto-detect `render.yaml` and create both services
6. Add environment variables in the Render dashboard:
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY`
   - `GOOGLE_CSE_ID`

#### Manual Setup

**Backend (Web Service):**
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

**Frontend (Static Site):**
- Build Command: `cd frontend && npm install && npm run build`
- Publish Directory: `frontend/dist`
- Environment Variables:
  - `VITE_API_URL` = `https://your-backend.onrender.com`
  - `VITE_WS_URL` = `wss://your-backend.onrender.com`

## State Management

This project uses **Pydantic models** for state management:

- **Type Safety**: Compile-time type checking and runtime validation
- **Serialization**: Automatic JSON serialization for checkpoints
- **IDE Support**: Full autocomplete and type hints
- **Validation**: Built-in data validation and error messages

### State Model

The `ResearchState` class includes:
- Topic and user metadata
- Research plan with search queries and angles
- Search queries and results
- Extracted and prioritized claims
- Draft and refined plans
- Human feedback objects for each checkpoint
- Final brief content
- Execution logs and metadata

## Logging System

Each node execution is logged with:
- Timestamp
- Input parameters
- Prompt used (if applicable)
- Output data
- Model settings (model name, temperature, seed)
- Human decisions (for HITL nodes)
- Execution time

Logs are saved to: `logs/{user_id}_{timestamp}.json`

## Output Format

Generated briefs include:

1. **Title**: Based on research topic
2. **Introduction**: Context and significance
3. **Summary**: High-level overview
4. **Key Findings**: 3-6 major discoveries with citations [n]
5. **Risks/Unknowns**: 3 critical concerns
6. **Further Reading**: 5-8 curated sources
7. **Sources**: Full citations with URLs

Example citation format: `[1] Source Title - URL`

## Customization

### Adding New Nodes

1. Create node file in `backend/nodes/`
2. Implement node function taking `ResearchState`
3. Add node to `backend/graph.py`
4. Update graph edges

### Modifying Prompts

Edit prompt templates in `backend/prompts/` to customize:
- Research plan generation
- Search query generation
- Claim extraction criteria
- Synthesis approach
- Refinement logic

### Adjusting Model Parameters

Edit `.env` file:
```env
OPENAI_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.7
SEED=42
```

## Troubleshooting

### Backend Issues

**Connection Refused**:
```bash
# Ensure backend is running
uvicorn backend.main:app --reload
```

**API Key Errors**:
- Check `.env` file exists and has valid keys
- Verify API key format (no quotes, no spaces)

**Import Errors**:
```bash
pip install -r requirements.txt --force-reinstall
```

### Frontend Issues

**Module Not Found**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**WebSocket Connection Failed**:
- Ensure backend is running on port 8000
- Check CORS settings in `backend/main.py`

### Google Search Issues

**No Search Results**:
- Verify Google API key is valid
- Check CSE ID is correct
- Ensure Custom Search Engine is configured

## Security Notes

- API keys should never be committed to version control
- `.gitignore` is configured to exclude `.env` files
- Consider using environment-specific configs for deployment
- Implement authentication for multi-user scenarios

## License

This project is for educational purposes.

## Acknowledgments

- Built with LangGraph by LangChain
- Powered by OpenAI GPT-4
- Search via Google Custom Search API
- UI built with React and Vite

## Support

For issues or questions:
1. Check troubleshooting section
2. Review execution logs in `logs/` directory
3. Inspect checkpoint state in `checkpoints/`

---

**Note**: This system is designed for research and educational purposes. Always verify AI-generated content before use in production environments.
