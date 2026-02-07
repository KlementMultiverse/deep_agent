import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

print("=" * 70)
print("DAY 12: PRODUCTION PATTERNS")
print("=" * 70)

# ============================================================
# PRODUCTION CHECKLIST
# ============================================================

print("""
PRODUCTION CHECKLIST (FROM DOCS + BEST PRACTICES)
==================================================

Before deploying an agent to production, ensure:

┌─────────────────────────────────────────────────────────────────┐
│ □ OBSERVABILITY                                                 │
│   ├── LangSmith tracing enabled                                │
│   ├── Monitoring dashboards configured                         │
│   └── Alerts set for failures/latency                          │
├─────────────────────────────────────────────────────────────────┤
│ □ SECURITY                                                      │
│   ├── Sandbox for code execution                               │
│   ├── HITL for dangerous operations                            │
│   ├── virtual_mode=True for filesystem                         │
│   └── NO secrets in agent context                              │
├─────────────────────────────────────────────────────────────────┤
│ □ RELIABILITY                                                   │
│   ├── Persistent checkpointer (Postgres, not Memory)           │
│   ├── Error handling in tools                                  │
│   └── Retry logic for transient failures                       │
├─────────────────────────────────────────────────────────────────┤
│ □ PERFORMANCE                                                   │
│   ├── Streaming enabled for UX                                 │
│   ├── Subagents for heavy/parallel work                        │
│   └── Context management (offloading large data)               │
├─────────────────────────────────────────────────────────────────┤
│ □ DEPLOYMENT                                                    │
│   ├── LangSmith Agent Server (managed)                         │
│   ├── OR: Self-hosted with proper infra                        │
│   └── CI/CD for agent updates                                  │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# PATTERN 1: STREAMING
# ============================================================

print("=" * 70)
print("PATTERN 1: STREAMING (Better UX)")
print("=" * 70)

print("""
WHY STREAMING?
- LLMs are slow (2-10+ seconds for response)
- Users hate waiting without feedback
- Streaming shows output AS IT'S GENERATED

FROM DOCS:
"Streaming is crucial for enhancing the responsiveness of
 applications built on LLMs. By displaying output progressively,
 even before a complete response is ready, streaming significantly
 improves user experience."

STREAMING MODES:
┌─────────────────────────────────────────────────────────────────┐
│ Mode         │ What It Streams                                  │
├─────────────────────────────────────────────────────────────────┤
│ "values"     │ Full state after each step                       │
│ "updates"    │ Only changes (deltas) per step                   │
│ "messages"   │ LLM tokens as they're generated                  │
│ "custom"     │ Your own custom events                           │
│ "debug"      │ Detailed traces for debugging                    │
└─────────────────────────────────────────────────────────────────┘

CODE EXAMPLE:
┌─────────────────────────────────────────────────────────────────┐
│ # Instead of invoke() (waits for full response):               │
│ response = agent.invoke({"messages": [...]})                   │
│                                                                 │
│ # Use stream() for real-time updates:                          │
│ for mode, chunk in agent.stream(                               │
│     {"messages": [...]},                                        │
│     config=config,                                              │
│     stream_mode=["updates", "messages"],  # Multiple modes!    │
│ ):                                                              │
│     if mode == "messages":                                      │
│         token, metadata = chunk                                 │
│         if token.content:                                       │
│             print(token.content, end="", flush=True)           │
│     elif mode == "updates":                                     │
│         if "__interrupt__" in chunk:                           │
│             print(f"Interrupt: {chunk['__interrupt__']}")      │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# PATTERN 2: ERROR HANDLING
# ============================================================

print("=" * 70)
print("PATTERN 2: ERROR HANDLING")
print("=" * 70)

print("""
TOOL ERROR HANDLING:
┌─────────────────────────────────────────────────────────────────┐
│ from langchain_core.tools import tool                           │
│                                                                 │
│ @tool                                                           │
│ def risky_operation(input: str) -> str:                        │
│     '''Do something that might fail.'''                        │
│     try:                                                        │
│         result = do_risky_thing(input)                         │
│         return f"Success: {result}"                            │
│     except SpecificError as e:                                 │
│         # Return error message - agent will adapt              │
│         return f"Error: {e}. Try a different approach."        │
│     except Exception as e:                                     │
│         # Log for debugging, return safe message               │
│         logger.error(f"Unexpected error: {e}")                 │
│         return "An unexpected error occurred. Please retry."   │
└─────────────────────────────────────────────────────────────────┘

KEY INSIGHT:
- Don't raise exceptions from tools (crashes the loop)
- Return error messages - agent can adapt its strategy
- Log errors for debugging in LangSmith
""")

# Demo: Tool with error handling
@tool
def safe_divide(a: float, b: float) -> str:
    """Divide two numbers safely."""
    try:
        if b == 0:
            return "Error: Cannot divide by zero. Please use a non-zero divisor."
        result = a / b
        return f"Result: {a} / {b} = {result}"
    except Exception as e:
        return f"Error during calculation: {e}"

@tool
def fetch_user_data(user_id: str) -> str:
    """Fetch user data from database (simulated)."""
    try:
        # Simulated database lookup
        if not user_id.isdigit():
            return f"Error: Invalid user ID '{user_id}'. Must be numeric."
        if int(user_id) > 1000:
            return f"Error: User {user_id} not found in database."
        return f"User {user_id}: Name=John, Email=john@example.com"
    except Exception as e:
        return f"Database error: {e}. Please try again."

print("Created tools with error handling: safe_divide, fetch_user_data")

# ============================================================
# PATTERN 3: PERSISTENT CHECKPOINTER
# ============================================================

print("\n" + "=" * 70)
print("PATTERN 3: PERSISTENT CHECKPOINTER (Production)")
print("=" * 70)

print("""
CHECKPOINTER COMPARISON:
┌─────────────────────────────────────────────────────────────────┐
│ Type              │ Persistence    │ Use Case                  │
├─────────────────────────────────────────────────────────────────┤
│ MemorySaver()     │ RAM only       │ Development, testing      │
│ SqliteSaver()     │ Local file     │ Local apps, prototypes    │
│ PostgresSaver()   │ Database       │ Production, scalable      │
│ AsyncPostgresSaver│ Database+Async │ High-throughput prod      │
└─────────────────────────────────────────────────────────────────┘

WHY PERSISTENT CHECKPOINTER?
- Resume conversations after server restart
- HITL requires saving state during pause
- Multiple server instances can share state
- Audit trail of all interactions

PRODUCTION SETUP:
┌─────────────────────────────────────────────────────────────────┐
│ from langgraph.checkpoint.postgres import PostgresSaver        │
│ import psycopg                                                  │
│                                                                 │
│ DB_URI = os.getenv("DATABASE_URL")                             │
│                                                                 │
│ with psycopg.Connection.connect(DB_URI) as conn:               │
│     checkpointer = PostgresSaver(conn)                         │
│     # Setup tables on first run:                               │
│     checkpointer.setup()                                        │
│                                                                 │
│ agent = create_deep_agent(                                      │
│     model=model,                                                │
│     checkpointer=checkpointer,                                 │
│     interrupt_on={...}                                         │
│ )                                                               │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# PATTERN 4: DEPLOYMENT OPTIONS
# ============================================================

print("=" * 70)
print("PATTERN 4: DEPLOYMENT OPTIONS")
print("=" * 70)

print("""
FROM DOCS:
"LangSmith provides a managed hosting platform designed for
 agent workloads. Traditional hosting platforms are built for
 stateless, short-lived web applications, while LangGraph is
 purpose-built for stateful, long-running agents."

DEPLOYMENT OPTIONS:
┌─────────────────────────────────────────────────────────────────┐
│ Option                │ Best For                                │
├─────────────────────────────────────────────────────────────────┤
│ 1. LangSmith Platform │ Managed, easiest, includes observability│
│    (Agent Server)     │ - Deploy from GitHub                    │
│                       │ - Built-in scaling, persistence         │
│                       │ - API: /threads, /runs, /assistants     │
├─────────────────────────────────────────────────────────────────┤
│ 2. Self-hosted        │ Full control, data privacy              │
│    LangGraph Server   │ - Docker / Kubernetes                   │
│                       │ - Manage your own infra                 │
│                       │ - Optional LangSmith tracing            │
├─────────────────────────────────────────────────────────────────┤
│ 3. Standalone         │ Simple deployments, microservices       │
│    Agent Server       │ - No control plane                      │
│                       │ - Requires Postgres + Redis             │
│                       │ - Run anywhere (ECS, EC2, etc.)         │
└─────────────────────────────────────────────────────────────────┘

AGENT SERVER API ENDPOINTS:
┌─────────────────────────────────────────────────────────────────┐
│ Endpoint            │ Purpose                                   │
├─────────────────────────────────────────────────────────────────┤
│ /assistants         │ Create/manage agent configurations        │
│ /threads            │ Manage conversation threads               │
│ /threads/{id}/runs  │ Execute agent on a thread                 │
│ /runs/stream        │ Stream run output in real-time            │
│ /store              │ Key-value store for long-term memory      │
│ /crons              │ Schedule periodic agent runs              │
│ /docs               │ API documentation                         │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# PATTERN 5: PRODUCTION AGENT SETUP
# ============================================================

print("=" * 70)
print("PATTERN 5: PRODUCTION-READY AGENT")
print("=" * 70)

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# Production checkpointer (use Postgres in real prod)
checkpointer = MemorySaver()  # Replace with PostgresSaver in prod

# Production agent with all safety patterns
production_agent = create_deep_agent(
    model=model,
    tools=[safe_divide, fetch_user_data],
    backend=FilesystemBackend(
        root_dir="./",
        virtual_mode=True  # Security!
    ),
    checkpointer=checkpointer,
    interrupt_on={
        # Review any file modifications
        "write_file": True,
        "edit_file": True,
    },
    # skills=["./skills/"],  # Load domain knowledge
    # memory=["./AGENTS.md"],  # Load project context
)

print("""
PRODUCTION AGENT CREATED:
┌─────────────────────────────────────────────────────────────────┐
│ agent = create_deep_agent(                                      │
│     model=model,                                                │
│     tools=[...],  # With error handling                        │
│     backend=FilesystemBackend(                                 │
│         root_dir="./",                                          │
│         virtual_mode=True  # Blocks path traversal             │
│     ),                                                          │
│     checkpointer=PostgresSaver(...),  # Persistent state       │
│     interrupt_on={                                              │
│         "write_file": True,  # Review file writes              │
│         "edit_file": True,   # Review file edits               │
│     },                                                          │
│     skills=["./skills/"],   # Domain expertise                 │
│     memory=["./AGENTS.md"], # Project context                  │
│ )                                                               │
│                                                                 │
│ # Enable observability:                                         │
│ # LANGSMITH_TRACING=true                                        │
│ # LANGSMITH_API_KEY=...                                         │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# MENTAL MODEL
# ============================================================

print("=" * 70)
print("MENTAL MODEL (MM-013): Production Patterns")
print("=" * 70)

print("""
PRODUCTION = Observability + Security + Reliability + Performance

LAYER BY LAYER:
┌─────────────────────────────────────────────────────────────────┐
│ 1. OBSERVABILITY (See what's happening)                         │
│    └── LangSmith tracing + dashboards + alerts                 │
│                                                                 │
│ 2. SECURITY (Protect the system)                                │
│    └── Sandbox + HITL + virtual_mode + no secrets in context   │
│                                                                 │
│ 3. RELIABILITY (Keep it running)                                │
│    └── Postgres checkpointer + error handling + retries        │
│                                                                 │
│ 4. PERFORMANCE (Make it fast)                                   │
│    └── Streaming + subagents + context offloading              │
│                                                                 │
│ 5. DEPLOYMENT (Ship it)                                         │
│    └── LangSmith Platform OR self-hosted LangGraph Server      │
└─────────────────────────────────────────────────────────────────┘

QUICK REFERENCE:
┌─────────────────────────────────────────────────────────────────┐
│ Problem                    │ Solution                           │
├─────────────────────────────────────────────────────────────────┤
│ "Why did agent fail?"      │ LangSmith traces                   │
│ "Agent deleted wrong file" │ HITL on dangerous tools            │
│ "Lost conversation state"  │ Postgres checkpointer              │
│ "Response too slow"        │ Streaming                          │
│ "Context too large"        │ Subagents + offloading             │
│ "How do I deploy?"         │ LangSmith Agent Server             │
└─────────────────────────────────────────────────────────────────┘
""")

print("=" * 70)
print("Demo complete! Day 12: Production Patterns")
print("=" * 70)
