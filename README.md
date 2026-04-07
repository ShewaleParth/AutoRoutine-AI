# 🤖 AutoRoutine AI (Powered by FlowMind)

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-orange?style=for-the-badge)](https://modelcontextprotocol.io/)

**AutoRoutine AI** is a next-generation, multi-agent productivity operating system designed to orchestrate your daily life. By leveraging a specialized ecosystem of AI agents, it doesn't just manage tasks—it understands your context, resolves schedule conflicts, and Surfaces proactive insights.

---

## 🌟 Key Features

### 🧠 Multi-Agent Orchestration
A central **Orchestrator Brain** powered by Google ADK delegates tasks to specialized domain experts:
*   **📅 CalendarAgent**: Manages schedules, detects meeting overlaps, and suggets optimal timings.
*   **✅ TaskAgent**: Handles goal tracking, prioritization, and deadline management.
*   **📝 NotesAgent**: Processes unstructured thoughts, extracts entities, and maintains long-term memory.
*   **💡 InsightAgent**: Analyzes the relationship between your tasks and time to provide proactive advice.

### 🔌 Model Context Protocol (MCP) Integration
Features a high-performance **MCP Server** with 16+ custom tools, allowing the agents to interact with external data sources and your local environment with extreme precision.

### ⚡ Proactive Workflow Engine
Automated sequences like the **"Morning Briefing"** cross-reference your upcoming meetings with pending high-priority tasks to identify "Impossible Days" before they happen.

### 🎨 Premium Glassmorphic UI
A stunning, high-fidelity React dashboard featuring:
*   **Real-time State Sync**: Powered by Cloud Firestore.
*   **Animated Thinking States**: Visual feedback while agents work.
*   **Responsive Desktop Layout**: Optimized for high-productivity environments.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, Vite, Axios, Lucide Icons, Vanilla CSS (Glassmorphism) |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| **AI/ML** | Google Generative AI (Gemini), Google ADK, Vertex AI |
| **Database** | Google Cloud Firestore (Real-time NoSQL) |
| **Protocol** | Model Context Protocol (MCP) |
| **DevOps** | Docker, Docker Compose |

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   Node.js 18+
*   Google Cloud Service Account (Firestore access)
*   Gemini API Key

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
```
Create a `.env` file in the `backend/` directory:
```env
GOOGLE_API_KEY=your_gemini_key
PROJECT_ID=your_gcp_project_id
FIRESTORE_DATABASE=your_db_name
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Running with Docker (Recommended)
Launch the entire stack with a single command:
```bash
docker-compose up --build
```

---

## 📂 Project Structure

```text
AutoRoutine-AI/
├── backend/
│   ├── agents/          # Agent logic (Task, Cal, Notes, Insight, Orchestrator)
│   ├── api/             # FastAPI routes & business logic
│   ├── autoroutine_mcp/ # MCP Server (Custom Tools)
│   ├── db/              # Firestore integration & Data Models
│   └── scripts/         # Verification and DB seeding tools
├── frontend/
│   ├── src/             # React dashboard components
│   └── public/          # Assets and icons
└── docker-compose.yml   # Container orchestration
```

---

## 🔒 Security & Privacy
*   **Environment Safety**: All API keys are managed via `.env` and are strictly excluded from version control.
*   **Service Accounts**: JSON keys are integrated into the pipeline but never stored in the repository (see `.gitignore`).
*   **Data Isolation**: Using Firestore security rules to ensure data integrity.

---

## 🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

---

*Built for the next generation of AI productivity.* 🚀
