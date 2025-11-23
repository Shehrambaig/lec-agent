# Lecture Assistant Agent

A sophisticated AI-powered research system that generates comprehensive lecture briefs using **LangGraph** workflows with **Human-in-the-Loop (HITL)** checkpoints.

## 🎯 Features

- **Automated Research**: Intelligent web search and fact extraction using GPT-4
- **Human-in-the-Loop**: Two critical checkpoints for plan review and fact verification
- **Real-time Updates**: WebSocket-based communication for live progress tracking
- **Structured Output**: Professional markdown briefs with proper citations
- **Comprehensive Logging**: Detailed execution logs for audit and debugging
- **Disk-based Checkpoints**: Persistent state management using SQLite

## 🏗️ Architecture

### Backend (FastAPI + LangGraph)
- **LangGraph Workflow**: Stateful multi-agent graph with conditional edges
- **State Management**: Pydantic models for type-safe state handling
- **Checkpoint System**: SQLite-based persistence for workflow resumption
- **WebSocket Server**: Real-time bidirectional communication

### Frontend (React + Vite)
- **Simple UI**: Clean, functional interface for research control
- **Real-time Updates**: Live progress tracking and node execution status
- **Interactive HITL**: User-friendly feedback forms for plan review and fact verification

### Graph Workflow

```
input → search → extract → prioritize → synthesize → [HITL: Plan Review]
→ refine → [HITL: Fact Verification] → brief → format → END
```

## 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- OpenAI API Key
- Google Custom Search API Key & CSE ID

## 🚀 Installation

### 1. Clone the Repository

```bash
# Extract the ZIP file and navigate to the project directory
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
# Install Python dependencies
pip install -r requirements.txt
```

### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install
```

## ▶️ Running the Application

### Start Backend Server

```bash
# From project root
uvicorn backend.main:app --reload
```

Backend will run on: `http://localhost:8000`

### Start Frontend Development Server

```bash
# From project root/frontend
npm run dev
```

Frontend will run on: `http://localhost:5173`

## 📖 Usage

1. **Open Browser**: Navigate to `http://localhost:5173`

2. **Enter Topic**: Input your research topic (e.g., "Propagation of disinformation by LLMs")

3. **Start Research**: Click "Start Research" to begin the workflow

4. **Plan Review (HITL #1)**:
   - Review the generated lecture plan
   - Choose from options:
     - ✅ **Approve**: Continue with current plan
     - 🔍 **More Sources**: Request additional research
     - 🎯 **Emphasize Topics**: Focus on specific areas
     - 🔄 **Rework**: Completely restructure the plan
   - Optionally provide comments

5. **Fact Verification (HITL #2)**:
   - Review 6 key extracted facts
   - Verify their accuracy
   - Choose approval or request revisions

6. **Completion**: 
   - System generates final research brief
   - Output saved to `outputs/` directory
   - Execution log saved to `logs/` directory

## 📁 Project Structure

```
lecture-assistant-agent/
├── backend/
│   ├── main.py                 # FastAPI app with WebSocket
│   ├── graph.py                # LangGraph workflow definition
│   ├── state.py                # Pydantic state models
│   ├── logger.py               # Execution logging
│   ├── utils.py                # OpenAI & Google Search helpers
│   ├── nodes/                  # Node implementations
│   │   ├── input_node.py
│   │   ├── search_node.py
│   │   ├── extract_node.py
│   │   ├── author_prioritization_node.py
│   │   ├── synthesis_node.py
│   │   ├── refinement_node.py
│   │   ├── brief_node.py
│   │   └── formatting_node.py
│   └── prompts/                # LLM prompt templates
│       ├── search_prompt.txt
│       ├── extract_prompt.txt
│       ├── synthesis_prompt.txt
│       ├── refinement_prompt.txt
│       └── brief_prompt.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main application
│   │   ├── components/
│   │   │   ├── InputForm.jsx
│   │   │   ├── PlanReview.jsx
│   │   │   ├── FactVerification.jsx
│   │   │   └── ProgressTracker.jsx
│   │   └── services/
│   └── package.json
├── logs/                       # Execution logs (JSON)
├── checkpoints/                # LangGraph checkpoints (SQLite)
├── outputs/                    # Generated briefs (Markdown)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🧠 State Management

This project uses **Pydantic models** for state management, chosen for:

- **Type Safety**: Compile-time type checking and runtime validation
- **Serialization**: Automatic JSON serialization for checkpoints
- **IDE Support**: Full autocomplete and type hints
- **Validation**: Built-in data validation and error messages

### State Model

The `ResearchState` class includes:
- Topic and user metadata
- Search queries and results
- Extracted and prioritized claims
- Draft and refined plans
- Human feedback objects
- Final brief content
- Execution logs and metadata

## 📝 Logging System

Each node execution is logged with:
- Timestamp
- Input parameters
- Prompt used (if applicable)
- Output data
- Model settings (model name, temperature, seed)
- Human decisions (for HITL nodes)
- Execution time

Logs are saved to: `logs/{user_id}_{timestamp}.json`

## 🔄 Checkpointing

LangGraph checkpoints enable:
- **State Persistence**: Graph state saved to disk after each node
- **Resumability**: Can resume from any checkpoint after interruption
- **HITL Support**: Natural pause points for human feedback
- **Debugging**: Inspect state at any point in execution

Checkpoints stored in: `checkpoints/research_checkpoints.db`

## 📊 Output Format

Generated briefs include:

1. **Title**: Based on research topic
2. **Introduction**: Context and significance
3. **Summary**: High-level overview
4. **Key Findings**: 3-6 major discoveries with citations [n]
5. **Risks/Unknowns**: 3 critical concerns
6. **Further Reading**: 5-8 curated sources
7. **Sources**: Full citations with URLs

Example citation format: `[1] Source Title - URL`

## 🛠️ Customization

### Adding New Nodes

1. Create node file in `backend/nodes/`
2. Implement node function taking `ResearchState`
3. Add node to `backend/graph.py`
4. Update graph edges

### Modifying Prompts

Edit prompt templates in `backend/prompts/` to customize:
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

## 🐛 Troubleshooting

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
# Reinstall dependencies
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

## 📦 Deployment Considerations

For production deployment:

1. **Environment Variables**: Use secure secret management
2. **CORS**: Restrict allowed origins in `backend/main.py`
3. **Rate Limiting**: Add rate limiting for API endpoints
4. **Database**: Consider PostgreSQL for checkpoints at scale
5. **Logging**: Integrate with logging service (e.g., CloudWatch)
6. **Error Handling**: Add comprehensive error boundaries

## 🔐 Security Notes

- API keys should never be committed to version control
- `.gitignore` is configured to exclude `.env` files
- Consider using environment-specific configs for deployment
- Implement authentication for multi-user scenarios

## 📄 License

This project is for educational purposes.

## 🙏 Acknowledgments

- Built with LangGraph by LangChain
- Powered by OpenAI GPT-4
- Search via Google Custom Search API
- UI built with React and Vite

## 📧 Support

For issues or questions:
1. Check troubleshooting section
2. Review execution logs in `logs/` directory
3. Inspect checkpoint state in `checkpoints/`

---

**Note**: This system is designed for research and educational purposes. Always verify AI-generated content before use in production environments.
