from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware import SubAgentMiddleware

load_dotenv()

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

workspace_dir = "./"

print("=" * 70)
print("SUBAGENT CONTEXT ISOLATION DEMO")
print("=" * 70)

print("""
THE CONCEPT:

Main Agent Context:          Subagent Context:
┌─────────────────────┐      ┌─────────────────────┐
│ User: "Review all   │      │ (FRESH - empty!)    │
│ Python files"       │      │                     │
│                     │      │ Task: "Analyze      │
│ Assistant: "I'll    │  →   │ hello_agent.py"     │
│ spawn subagent..."  │      │                     │
│                     │      │ [Reads file]        │
│ [Spawns subagent]   │      │ [Analyzes code]     │
│                     │      │ [Returns summary]   │
│ Subagent result:    │  ←   │                     │
│ "Found 3 issues..." │      └─────────────────────┘
└─────────────────────┘

KEY INSIGHT:
- Subagent does NOT see "Review all Python files"
- Subagent ONLY sees its specific task
- Main agent ONLY gets final output, not subagent's full trace
- Both contexts stay LEAN!
""")

# ============================================================
# CREATE MAIN AGENT WITH SUBAGENT CAPABILITY
# ============================================================

# Define what subagents the main agent can spawn
subagents = [
    {
        "name": "code_analyzer",
        "description": "Analyzes a single Python file for issues and patterns",
        "system_prompt": """You are a code analysis expert.
When given a file path:
1. Read the file
2. Analyze for: code quality, patterns, potential issues
3. Return a concise summary (max 5 bullet points)

IMPORTANT: Only analyze the ONE file you're given.
Do NOT try to analyze other files or the whole codebase."""
    }
]

agent = create_deep_agent(
    model=model,
    backend=FilesystemBackend(root_dir=workspace_dir, virtual_mode=True),
    memory=["./AGENTS.md"],
    subagents=subagents  # Enable subagent spawning
)

# ============================================================
# DEMONSTRATE CONTEXT ISOLATION
# ============================================================

print("=" * 70)
print("[MAIN AGENT] Orchestrating code review with subagent")
print("=" * 70)

task = """
I need you to review the file hello_agent.py.

Use the code_analyzer subagent to do a detailed analysis.
Then give me your overall assessment based on what the subagent found.

Note: I'm testing context isolation - the subagent should only see
its specific task, not this full message.
"""

response = agent.invoke({
    "messages": [{"role": "user", "content": task}]
},
config={"configurable": {"thread_id": "subagent-demo", "assistant_id": "test"}}
)

print("\n[MAIN AGENT RESPONSE]:")
print("-" * 70)
print(response["messages"][-1].content)

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("CONTEXT ISOLATION EXPLAINED")
print("=" * 70)
print("""
WHAT HAPPENED:

1. MAIN AGENT received full task:
   "I need you to review hello_agent.py. Use code_analyzer subagent..."

2. MAIN AGENT called task() tool with ONLY:
   "Analyze hello_agent.py for code quality issues"

3. SUBAGENT (code_analyzer) saw ONLY:
   - Its instructions (from subagents config)
   - The specific task from main agent
   - NOT the original user request
   - NOT main agent's conversation history

4. SUBAGENT returned summary to MAIN AGENT

5. MAIN AGENT's context now has:
   - Original user message
   - Subagent's summary (small!)
   - NOT subagent's full execution trace

WHY THIS MATTERS:

┌─────────────────────────────────────────────────────────────────┐
│ WITHOUT ISOLATION:                                              │
│ Main context = User request + All subagent tool calls + All    │
│ file contents subagent read + All intermediate reasoning       │
│ = HUGE CONTEXT (hits token limits fast!)                       │
├─────────────────────────────────────────────────────────────────┤
│ WITH ISOLATION:                                                 │
│ Main context = User request + Subagent summary only            │
│ = SMALL CONTEXT (can orchestrate many subagents!)              │
└─────────────────────────────────────────────────────────────────┘

PATTERN: Main orchestrates, subagents do deep work, only summaries bubble up.
""")
