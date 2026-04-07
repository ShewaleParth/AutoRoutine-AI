import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv; load_dotenv()

async def main():
    print("Testing ADK Agents Initialization...")
    
    from agents.task_agent import TaskAgent
    print("  ✅ TaskAgent imported")
    task_agent = TaskAgent()
    print("  ✅ TaskAgent initialized with", len(task_agent.tools), "tools")

    from agents.calendar_agent import CalendarAgent
    print("  ✅ CalendarAgent imported")
    cal_agent = CalendarAgent()
    print("  ✅ CalendarAgent initialized with", len(cal_agent.tools), "tools")

    from agents.notes_agent import NotesAgent
    print("  ✅ NotesAgent imported")
    notes_agent = NotesAgent()
    print("  ✅ NotesAgent initialized with", len(notes_agent.tools), "tools")

    from agents.insight_agent import InsightAgent
    print("  ✅ InsightAgent imported")
    insight_agent = InsightAgent()
    print("  ✅ InsightAgent initialized with", len(insight_agent.tools), "tools")

    from agents.orchestrator import OrchestratorAgent
    print("  ✅ OrchestratorAgent imported")
    orch_agent = OrchestratorAgent()
    print("  ✅ OrchestratorAgent initialized with", len(orch_agent.tools), "tools")
    print("  ✅ Total agents in Orchestrator:", orch_agent.agent_count())

    print("\n🎉 All 5 AI Agents loaded successfully!")

if __name__ == "__main__":
    asyncio.run(main())
