from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
import uuid

load_dotenv()

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

print("=" * 70)
print("COMPLETE HITL DEMO - All Tools, All Decisions")
print("=" * 70)

# ============================================================
# DEFINE 3 TOOLS WITH DIFFERENT RISK LEVELS
# ============================================================

@tool
def delete_file(path: str) -> str:
    """Delete a file from the filesystem."""
    print(f"    💀 [EXECUTED] delete_file({path})")
    return f"Deleted {path}"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to someone."""
    print(f"    📧 [EXECUTED] send_email(to={to}, subject={subject})")
    return f"Email sent to {to}"

@tool
def execute_sql(query: str) -> str:
    """Execute a SQL query on the database."""
    print(f"    🗄️  [EXECUTED] execute_sql({query[:50]}...)")
    return f"Query executed: {query}"

# ============================================================
# CREATE AGENT WITH HITL
# ============================================================

checkpointer = MemorySaver()

agent = create_deep_agent(
    model=model,
    tools=[delete_file, send_email, execute_sql],
    checkpointer=checkpointer,
    interrupt_on={
        "delete_file": True,  # All decisions: approve, edit, reject
        "send_email": {
            "allowed_decisions": ["approve", "edit", "reject"],
            "description": "Email will be sent externally"
        },
        "execute_sql": {
            "allowed_decisions": ["approve", "edit"],  # No reject allowed
            "description": "SQL will modify database"
        }
    }
)

print("""
CONFIGURATION:
┌─────────────────────────────────────────────────────────────────┐
│ Tool          │ Allowed Decisions                              │
├─────────────────────────────────────────────────────────────────┤
│ delete_file   │ approve, edit, reject  (all)                   │
│ send_email    │ approve, edit, reject  (all)                   │
│ execute_sql   │ approve, edit          (no reject!)            │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# HELPER FUNCTION: Run a test case
# ============================================================

def run_test(test_name: str, user_message: str, decision: dict, explanation: str):
    """Run a single HITL test case."""
    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)
    print(f"User: \"{user_message}\"")
    print(f"Decision: {decision}")
    print(f"Why: {explanation}")
    print("-" * 70)

    # Unique thread for each test
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # First invoke - will pause
    result = agent.invoke({
        "messages": [{"role": "user", "content": user_message}]
    }, config=config)

    if result.get("__interrupt__"):
        interrupt_info = result["__interrupt__"][0].value
        action = interrupt_info["action_requests"][0]

        print(f"\n⏸️  PAUSED!")
        print(f"   Tool: {action['name']}")
        print(f"   Args: {action['args']}")

        # Resume with decision
        result = agent.invoke(
            Command(resume={"decisions": [decision]}),
            config=config
        )

        print(f"\n   Decision Applied: {decision['type'].upper()}")
        if decision["type"] == "edit":
            print(f"   New Args: {decision.get('args', 'N/A')}")

        print(f"\n   Agent Response: {result['messages'][-1].content[:100]}...")
    else:
        print("   (No interrupt - completed directly)")

    return result


# ============================================================
# TOOL 1: delete_file - All 3 decisions
# ============================================================

print("\n" + "#" * 70)
print("# TOOL 1: delete_file")
print("#" * 70)

# Case 1.1: APPROVE
run_test(
    test_name="delete_file → APPROVE",
    user_message="Delete the file temp.txt",
    decision={"type": "approve"},
    explanation="File is safe to delete"
)

# Case 1.2: REJECT
run_test(
    test_name="delete_file → REJECT",
    user_message="Delete the file production_config.yaml",
    decision={"type": "reject"},
    explanation="This file is critical - don't delete!"
)

# Case 1.3: EDIT (change the path)
run_test(
    test_name="delete_file → EDIT",
    user_message="Delete the file data.csv",
    decision={
        "type": "edit",
        "args": {"path": "data_backup.csv"}  # Changed the path!
    },
    explanation="Delete backup instead of original"
)

# ============================================================
# TOOL 2: send_email - All 3 decisions
# ============================================================

print("\n" + "#" * 70)
print("# TOOL 2: send_email")
print("#" * 70)

# Case 2.1: APPROVE
run_test(
    test_name="send_email → APPROVE",
    user_message="Send email to alice@company.com with subject 'Meeting' and body 'See you at 3pm'",
    decision={"type": "approve"},
    explanation="Email looks correct"
)

# Case 2.2: REJECT
run_test(
    test_name="send_email → REJECT",
    user_message="Send email to wrong@person.com about the secret project",
    decision={"type": "reject"},
    explanation="Wrong recipient - don't send!"
)

# Case 2.3: EDIT (change recipient and subject)
run_test(
    test_name="send_email → EDIT",
    user_message="Send email to bob@old-email.com with subject 'Hello'",
    decision={
        "type": "edit",
        "args": {
            "to": "bob@new-email.com",      # Fixed email
            "subject": "Hello - Updated",    # Changed subject
            "body": "See you at 3pm"         # Keep body
        }
    },
    explanation="Bob changed his email address"
)

# ============================================================
# TOOL 3: execute_sql - Only approve/edit (no reject)
# ============================================================

print("\n" + "#" * 70)
print("# TOOL 3: execute_sql (no reject allowed)")
print("#" * 70)

# Case 3.1: APPROVE
run_test(
    test_name="execute_sql → APPROVE",
    user_message="Run this SQL: SELECT * FROM users LIMIT 10",
    decision={"type": "approve"},
    explanation="Safe read-only query"
)

# Case 3.2: EDIT (modify the query for safety)
run_test(
    test_name="execute_sql → EDIT",
    user_message="Delete all old records from the users table",
    decision={
        "type": "edit",
        "args": {
            "query": "DELETE FROM users WHERE created_at < '2024-01-01' LIMIT 100"
            # Added LIMIT 100 for safety!
        }
    },
    explanation="Added LIMIT 100 to prevent mass deletion"
)

# ============================================================
# SUMMARY: EDIT EXPLAINED
# ============================================================

print("\n" + "=" * 70)
print("WHAT EXACTLY DOES EDIT DO?")
print("=" * 70)
print("""
EDIT modifies the ARGS of the tool call before execution.

EXAMPLE 1: delete_file
┌─────────────────────────────────────────────────────────────────┐
│ ORIGINAL (from agent):                                          │
│   Tool: delete_file                                             │
│   Args: {"path": "data.csv"}                                    │
│                                                                 │
│ YOUR EDIT:                                                      │
│   {"type": "edit", "args": {"path": "data_backup.csv"}}        │
│                                                                 │
│ EXECUTED:                                                       │
│   delete_file(path="data_backup.csv")  ← Your modified args    │
└─────────────────────────────────────────────────────────────────┘

EXAMPLE 2: send_email
┌─────────────────────────────────────────────────────────────────┐
│ ORIGINAL (from agent):                                          │
│   Tool: send_email                                              │
│   Args: {"to": "bob@old.com", "subject": "Hi", "body": "..."}  │
│                                                                 │
│ YOUR EDIT:                                                      │
│   {"type": "edit", "args": {                                   │
│       "to": "bob@new.com",      ← Changed                      │
│       "subject": "Hi - Fixed",  ← Changed                      │
│       "body": "..."             ← Kept same                    │
│   }}                                                            │
│                                                                 │
│ EXECUTED:                                                       │
│   send_email(to="bob@new.com", subject="Hi - Fixed", ...)      │
└─────────────────────────────────────────────────────────────────┘

EXAMPLE 3: execute_sql
┌─────────────────────────────────────────────────────────────────┐
│ ORIGINAL (from agent):                                          │
│   Tool: execute_sql                                             │
│   Args: {"query": "DELETE FROM users WHERE old=true"}          │
│                                                                 │
│ YOUR EDIT (add safety):                                         │
│   {"type": "edit", "args": {                                   │
│       "query": "DELETE FROM users WHERE old=true LIMIT 100"    │
│   }}                              ↑ Added LIMIT                 │
│                                                                 │
│ EXECUTED:                                                       │
│   execute_sql(query="...LIMIT 100")  ← Safer!                  │
└─────────────────────────────────────────────────────────────────┘

KEY INSIGHT: You can change ANY argument of the tool call.
""")

# ============================================================
# TIED CONCEPTS
# ============================================================

print("\n" + "=" * 70)
print("TIED CONCEPTS (DEEPER LAYER)")
print("=" * 70)
print("""
1. CHECKPOINTER TYPES
┌─────────────────────────────────────────────────────────────────┐
│ Type              │ Use For              │ Persistence          │
├─────────────────────────────────────────────────────────────────┤
│ MemorySaver()     │ Testing, dev         │ Lost on restart      │
│ SqliteSaver()     │ Local apps           │ File-based           │
│ PostgresSaver()   │ Production           │ Database, survives   │
│ AsyncPostgresSaver│ Production (async)   │ Database, async      │
└─────────────────────────────────────────────────────────────────┘

2. THREAD_ID MANAGEMENT
┌─────────────────────────────────────────────────────────────────┐
│ Same thread_id    → Resume same conversation                   │
│ New thread_id     → Start fresh conversation                   │
│                                                                 │
│ In production:                                                  │
│ - Use user_id + session_id as thread_id                        │
│ - Store thread_id in your database                             │
│ - Retrieve when user returns to continue                       │
└─────────────────────────────────────────────────────────────────┘

3. MULTIPLE PENDING ACTIONS
┌─────────────────────────────────────────────────────────────────┐
│ If agent calls 2 tools that need approval:                      │
│                                                                 │
│ action_requests = [                                             │
│     {"name": "delete_file", "args": {...}},                    │
│     {"name": "send_email", "args": {...}}                      │
│ ]                                                               │
│                                                                 │
│ decisions = [                                                   │
│     {"type": "approve"},     # For delete_file                 │
│     {"type": "reject"}       # For send_email                  │
│ ]                                                               │
│                                                                 │
│ ORDER MATTERS! Decisions match action_requests by index.        │
└─────────────────────────────────────────────────────────────────┘

4. HITL IN SUBAGENTS
┌─────────────────────────────────────────────────────────────────┐
│ subagents = [                                                   │
│     {                                                           │
│         "name": "file_manager",                                 │
│         "system_prompt": "...",                                │
│         "tools": [delete_file],                                │
│         "interrupt_on": {                 ← Subagent has own!  │
│             "delete_file": True                                │
│         }                                                       │
│     }                                                           │
│ ]                                                               │
│                                                                 │
│ Checkpointer only needed on TOP-LEVEL agent.                   │
└─────────────────────────────────────────────────────────────────┘

5. CUSTOM DESCRIPTION (What human sees)
┌─────────────────────────────────────────────────────────────────┐
│ interrupt_on = {                                                │
│     "execute_sql": {                                           │
│         "allowed_decisions": ["approve", "edit"],              │
│         "description": "⚠️ This will modify production DB!"    │
│     }                             ↑ Custom warning message      │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘

6. REAL-WORLD PATTERNS
┌─────────────────────────────────────────────────────────────────┐
│ Pattern                    │ Tools that need HITL              │
├─────────────────────────────────────────────────────────────────┤
│ File Agent                 │ delete, move, overwrite           │
│ Email Agent                │ send_email, forward               │
│ Database Agent             │ DELETE, UPDATE, DROP              │
│ DevOps Agent               │ deploy, restart, terminate        │
│ Financial Agent            │ transfer, payment, refund         │
│ HR Agent                   │ offer_letter, terminate_access    │
│ Code Agent                 │ git push, merge, deploy           │
└─────────────────────────────────────────────────────────────────┘
""")
