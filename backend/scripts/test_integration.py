import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv; load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from agents.orchestrator import OrchestratorAgent

async def main():
    print("--- FlowMind Runner-based Integration Test ---")
    
    orch = OrchestratorAgent()
    session_service = InMemorySessionService()
    
    # Initialize Runner
    runner = Runner(
        app_name="FlowMind",
        agent=orch,
        session_service=session_service,
        auto_create_session=True
    )
    
    user_id = "test_user_123"
    session_id = "session_456"

    print("\n[Test 1] Natural Language Task Creation")
    # Wrap message in types.Content
    msg1 = types.Content(role="user", parts=[types.Part(text="Create a task to buy groceries with high priority.")])
    
    print("FlowMind is thinking...")
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=msg1
    ):
        if event.content:
            text = "".join([p.text for p in event.content.parts if p.text])
            if text:
                print(f"Agent: {text}")

    print("\n[Test 2] Follow-up Question")
    msg2 = types.Content(role="user", parts=[types.Part(text="What task did I just create?")])
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=msg2
    ):
        if event.content:
            text = "".join([p.text for p in event.content.parts if p.text])
            if text:
                print(f"Agent: {text}")

    print("\nIntegration test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
