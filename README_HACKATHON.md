# 🚀 FlowMind AI - Hackathon Launch Guide

Congratulations! You've built a multi-agent productivity OS. Below is everything you need to launch, demonstrate, and impress the judges.

---

## 🛠️ Project Architecture (Key Features)

1.  **Multi-Agent Context Graph**: A central "Brain" (Orchestrator) that uses Google ADK to delegate to 4 specialized agents (Task, Calendar, Notes, Insight).
2.  **Live Firestore Backbone**: Every action (task created, event scheduled, note taken) is persisted to your cloud database `dakshgrid` in real-time.
3.  **Proactive Workflow Engine**: Predefined agent-to-agent workflows (like **Morning Briefing**) that cross-reference different data types to surface conflicts.
4.  **Premium Glassmorphic UI**: High-fidelity React dashboard with animated thinking states and real-time state synchronization.

---

## 🚀 How to Launch (Presentation Ready)

### 1. Terminal A: Backend (FastAPI + ADK Agents)
The backend manages the AI logic and database connection.
```powershell
cd backend
venv\Scripts\activate
# Start the production-ready FastAPI server
uvicorn api.main:app --reload --port 8080
```
*Wait for: `startup.agents.ready (count=5)`.*

### 2. Terminal B: Frontend (React + Vite)
The beautiful dashboard interface.
```powershell
cd frontend
npm run dev
```
*Open `http://localhost:5173`.*

---

## 🎭 Presentation Talk Tracks (Show, Don't Just Tell)

### Scenario 1: The "I Forget Things" Demo
**Action**: Type into the FlowMind chat: *"I need to buy high quality coffee before Friday and prioritize it high."*
**Explain**: "Watch how the Orchestrator identifies this as a Task intent and delegates it to the TaskAgent. It's not just a chat; it's already written to our live Firestore database."
**Check**: Point to the **Pending Tasks** widget on the right.

### Scenario 2: The "Morning Briefing" Workflow
**Action**: Click the **Run Workflow** button on the **Proactive Insights** panel.
**Explain**: "Instead of a simple CRUD app, FlowMind runs a cross-agent sequence. The CalendarAgent checks my meetings, the TaskAgent checks my deadlines, and the InsightAgent builds a context graph to verify if I'm on track for the day."

### Scenario 3: Memory Recall
**Action**: Type into chat: *"Search my notes for anything about coffee."*
**Explain**: "The NotesAgent searches unstructured data and extracts entities automatically, ensuring I never lose a random thought."

---

## 📂 Project Structure Snapshot
```
flowmind/
├── backend/
│   ├── agents/          # Google ADK logic (Task, Cal, Notes, Insight, Orchestrator)
│   ├── api/             # FastAPI routes & App definition
│   ├── db/              # Firestore client & Pydantic models
│   ├── autoroutine_mcp/    # MCP Server (16 custom tools)
│   ├── scripts/         # Verification and Database seeding scripts
│   └── requirements.txt # Python dependencies
├── frontend/
│   ├── src/             # React logic & Glassmorphism UI components
│   └── package.json     # Node dependencies
└── docker-compose.yml   # One-click deployment
```

---

Good luck with your presentation! FlowMind is set to WOW. 🚀
