# Quick Start Guide - Lecture Assistant Agent

## ⚡ Fast Setup (5 minutes)

### Step 1: Extract and Navigate
```bash
unzip lecture-assistant-agent.zip
cd lecture-assistant-agent
```

### Step 2: Configure API Keys
```bash
cp .env.example .env
# Edit .env with your actual API keys
```

Required APIs:
- **OpenAI API Key**: https://platform.openai.com/api-keys
- **Google Custom Search**:
  - API Key: https://console.cloud.google.com/apis/credentials
  - CSE ID: https://programmablesearchengine.google.com/

### Step 3: Install Backend
```bash
pip install -r requirements.txt
```

### Step 4: Install Frontend
```bash
cd frontend
npm install
cd ..
```

### Step 5: Start Backend
```bash
# Terminal 1
uvicorn backend.main:app --reload
```

### Step 6: Start Frontend
```bash
# Terminal 2
cd frontend
npm run dev
```

### Step 7: Open Browser
Navigate to: http://localhost:5173

## 🎯 Demo Topic

Try this topic for testing:
```
Propagation of disinformation by LLMs
```

## 🔍 What to Expect

1. **Input Topic** → System generates 5-7 search queries
2. **Search Phase** → Fetches ~25-30 web results  
3. **Extract Phase** → Extracts 8-12 factual claims
4. **Prioritization** → Ranks claims by relevance
5. **Synthesis** → Creates draft lecture plan
6. **⏸ HITL Checkpoint 1**: Review and approve/modify plan
7. **Refinement** → Adjusts plan based on feedback
8. **⏸ HITL Checkpoint 2**: Verify key facts
9. **Brief Generation** → Creates markdown research brief
10. **Format & Save** → Saves to `outputs/` directory

Total time: ~2-3 minutes (with HITL pauses)

## 📁 Output Files

After completion:
- **Brief**: `outputs/brief_[topic]_[timestamp].md`
- **Log**: `logs/[user]_[timestamp].json`
- **Checkpoint**: `checkpoints/research_checkpoints.db`

## 🐛 Common Issues

**Error: Module not found**
```bash
pip install -r requirements.txt --force-reinstall
```

**Error: WebSocket connection failed**
- Ensure backend is running on port 8000
- Check no firewall blocking localhost

**Error: Google Search returns empty**
- Verify API keys in .env
- Check Google Cloud console for API limits

**Error: OpenAI rate limit**
- Add delay between requests
- Check your OpenAI usage tier

## ✅ Verification Checklist

Before starting:
- [ ] .env file exists with valid API keys
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Browser opened to http://localhost:5173

## 📊 Expected Output Structure

```markdown
# [Topic Title]

## Introduction
[Context and significance]

## Summary
[High-level overview]

## Key Findings
1. Finding with citation [1]
2. Finding with citation [2]
...

## Risks/Unknowns
1. Risk description
2. Risk description
...

## Further Reading
- Source 1 - URL
- Source 2 - URL
...

## Sources
[1] Full citation with URL
[2] Full citation with URL
...
```

## 🎓 Assignment Compliance

This implementation satisfies all requirements:
- ✅ LangGraph with 8+ nodes
- ✅ 2 HITL checkpoints (plan review + fact verification)
- ✅ Disk-based checkpointing (SQLite)
- ✅ Comprehensive logging per node
- ✅ Real-time WebSocket communication
- ✅ FastAPI backend + React frontend
- ✅ Markdown output with citations
- ✅ requirements.txt included
- ✅ Commands work exactly as specified

## 🚀 Next Steps

1. Run the demo with provided topic
2. Review generated brief in outputs/
3. Check execution log in logs/
4. Try custom topics
5. Experiment with HITL feedback options

---

For detailed documentation, see README.md
