from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

load_dotenv()

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

print("=" * 70)
print("HUMAN-IN-THE-LOOP (HITL) DEMO")
print("=" * 70)

# ============================================================
# STEP 1: DEFINE TOOLS (some safe, some dangerous)
# ============================================================

@tool
def read_file(path: str) -> str:
    """Read a file from the filesystem."""
    print(f"    [TOOL] Reading: {path}")
    return f"Contents of {path}: Hello World!"

@tool
def delete_file(path: str) -> str:
    """Delete a file from the filesystem."""
    print(f"    [TOOL] DELETING: {path}")
    return f"Deleted {path}"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to someone."""
    print(f"    [TOOL] SENDING EMAIL to: {to}")
    return f"Email sent to {to} with subject '{subject}'"

print("""
TOOLS DEFINED:
- read_file    → SAFE (no approval needed)
- delete_file  → DANGEROUS (needs approval)
- send_email   → DANGEROUS (needs approval)
""")

# ============================================================
# STEP 2: CREATE AGENT WITH HITL
# ============================================================

# Checkpointer is REQUIRED for HITL (saves state during pause)
checkpointer = MemorySaver()

agent = create_deep_agent(
    model=model,
    tools=[read_file, delete_file, send_email],
    checkpointer=checkpointer,  # REQUIRED!
    interrupt_on={
        "read_file": False,     # Safe → auto-execute
        "delete_file": True,    # Dangerous → pause and ask
        "send_email": True,     # Dangerous → pause and ask
    }
)

print("Agent created with HITL enabled!")
print("- read_file: auto-execute")
print("- delete_file: will PAUSE for approval")
print("- send_email: will PAUSE for approval")

# ============================================================
# STEP 3: TEST - Trigger a pause
# ============================================================

print("\n" + "=" * 70)
print("TEST: Ask agent to delete a file")
print("=" * 70)

# Thread ID identifies this conversation (needed for resume)
config = {"configurable": {"thread_id": "hitl-demo-001"}}

# First call - this will PAUSE when agent tries to delete
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Delete the file called temp.txt"
    }]
}, config=config)

# ============================================================
# STEP 4: CHECK IF PAUSED
# ============================================================

if result.get("__interrupt__"):
    print("\n⏸️  AGENT PAUSED - Waiting for your decision!")
    print("-" * 70)

    # Extract what's pending
    interrupt_info = result["__interrupt__"][0].value
    action_requests = interrupt_info["action_requests"]

    for i, action in enumerate(action_requests):
        print(f"\nPending Action #{i+1}:")
        print(f"  Tool: {action['name']}")
        print(f"  Args: {action['args']}")

    print("\n" + "-" * 70)
    print("OPTIONS:")
    print("  [1] APPROVE - Execute as-is")
    print("  [2] REJECT  - Don't execute")
    print("-" * 70)

    # ============================================================
    # STEP 5: SIMULATE USER DECISION (in real app, this is UI)
    # ============================================================

    # Let's demonstrate APPROVE
    print("\n>>> Simulating user choice: APPROVE")

    decisions = [{"type": "approve"}]

    # Resume with the decision
    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config  # SAME thread_id!
    )

    print("\n✅ Agent resumed and completed!")
    print("-" * 70)
    print("Final response:", result["messages"][-1].content)

else:
    print("No interrupt - agent completed directly")
    print("Response:", result["messages"][-1].content)

# ============================================================
# STEP 6: DEMONSTRATE REJECT
# ============================================================

print("\n" + "=" * 70)
print("TEST 2: Same request, but REJECT this time")
print("=" * 70)

# New thread for fresh conversation
config2 = {"configurable": {"thread_id": "hitl-demo-002"}}

result2 = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Delete the file called important_data.txt"
    }]
}, config=config2)

if result2.get("__interrupt__"):
    print("\n⏸️  AGENT PAUSED - Waiting for decision...")

    interrupt_info = result2["__interrupt__"][0].value
    action = interrupt_info["action_requests"][0]
    print(f"  Tool: {action['name']}")
    print(f"  Args: {action['args']}")

    print("\n>>> Simulating user choice: REJECT")

    decisions = [{"type": "reject"}]

    result2 = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config2
    )

    print("\n❌ Action REJECTED!")
    print("-" * 70)
    print("Agent response:", result2["messages"][-1].content)

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
WHAT YOU SAW:

TEST 1: Agent tried to delete temp.txt
        → PAUSED (because delete_file: True in interrupt_on)
        → We chose APPROVE
        → Agent executed the delete

TEST 2: Agent tried to delete important_data.txt
        → PAUSED
        → We chose REJECT
        → Agent did NOT delete (skipped the tool)

KEY COMPONENTS:
┌─────────────────────────────────────────────────────────────────┐
│ checkpointer = MemorySaver()      # Saves state during pause   │
│                                                                 │
│ interrupt_on = {                                                │
│     "delete_file": True,          # Pause for this tool        │
│     "read_file": False,           # Auto-execute               │
│ }                                                               │
│                                                                 │
│ config = {"configurable": {"thread_id": "unique-id"}}          │
│                                                                 │
│ # Check for pause:                                              │
│ if result.get("__interrupt__"):                                │
│     # Show pending action to user                               │
│     # Get decision                                              │
│     agent.invoke(Command(resume={"decisions": [...]}), config) │
└─────────────────────────────────────────────────────────────────┘
""")
