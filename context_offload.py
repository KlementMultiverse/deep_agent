from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

load_dotenv()

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

workspace_dir = "./"

print("=" * 70)
print("CONTEXT OFFLOAD DEMO")
print("=" * 70)

print("""
TWO OFFLOADING MECHANISMS IN DEEP AGENTS:

1. AUTOMATIC EVICTION (Built-in safety net)
   - FilesystemMiddleware auto-evicts tool results > 20K tokens
   - Happens behind the scenes - no config needed
   - Replaces large output with: "truncated, saved to file..."

2. PROMPT-BASED OFFLOADING (What we demo here)
   - YOU instruct agent: "Save to file, return summary"
   - YOU control file path and summary format
   - Intentional design pattern
""")

# ============================================================
# PROMPT-BASED OFFLOADING DEMO
# ============================================================

agent = create_deep_agent(
    model=model,
    backend=FilesystemBackend(root_dir=workspace_dir, virtual_mode=True),
    memory=["./AGENTS.md"]
)

print("=" * 70)
print("[CALL 1] Generate large output, save to file, return summary")
print("=" * 70)

task_1 = """
Read all Python files in this workspace:
- hello_agent.py
- calculator_agent.py
- backend_default.py
- backend_filesystem.py
- backend_store.py
- backend_composite.py
- context_memory.py

Create ONE production-grade Python module combining all patterns.

Apply these standards:
1. Organize into classes (AgentFactory, BackendManager, etc.)
2. Add type hints to ALL functions
3. Add exception handling
4. Add Google-style docstrings
5. Follow PEP8 formatting

OFFLOADING INSTRUCTIONS:
- Save the FULL code to /output/production_agents.py
- Return to me ONLY:
  - File path where code is saved
  - List of classes created
  - Total line count
- Do NOT include any code in your response
"""

response_1 = agent.invoke({
    "messages": [{"role": "user", "content": task_1}]
},
config={"configurable": {"thread_id": "offload-demo", "assistant_id": "test"}}
)

print("\n[CALL 1 RESPONSE] Summary only (full code in file):")
print("-" * 70)
print(response_1["messages"][-1].content)

# ============================================================
# VERIFY: Ask about specific class (agent must read file)
# ============================================================

print("\n" + "=" * 70)
print("[CALL 2] Ask about specific class - agent must READ file")
print("=" * 70)

task_2 = """
What methods does the first class in /output/production_agents.py have?
Just list the method names.
"""

response_2 = agent.invoke({
    "messages": [
        {"role": "user", "content": task_1},
        {"role": "assistant", "content": response_1["messages"][-1].content},
        {"role": "user", "content": task_2}
    ]
},
config={"configurable": {"thread_id": "offload-demo", "assistant_id": "test"}}
)

print("\n[CALL 2 RESPONSE] Agent had to read file to answer:")
print("-" * 70)
print(response_2["messages"][-1].content)

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("KEY INSIGHT")
print("=" * 70)
print("""
CALL 1 Context:
┌────────────────────────────────────────────────────┐
│ User: "Create production code..."                 │
│ Assistant: "Saved to /output/prod.py              │
│            3 classes, 150 lines"                  │
│                                                   │
│ NO CODE HERE - just summary!                      │
└────────────────────────────────────────────────────┘

CALL 2 Context:
┌────────────────────────────────────────────────────┐
│ Previous messages (small)                         │
│ User: "What methods in first class?"              │
│ Agent: [reads file] → extracts answer             │
│ Assistant: "Methods: X, Y, Z"                     │
│                                                   │
│ Only the ANSWER added, not full file!             │
└────────────────────────────────────────────────────┘

RESULT: Conversation history stays SMALL across all turns.
""")
