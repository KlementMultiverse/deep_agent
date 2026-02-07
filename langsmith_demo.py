import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from deepagents import create_deep_agent

load_dotenv()

print("=" * 70)
print("DAY 11: LANGSMITH INTEGRATION")
print("=" * 70)

# ============================================================
# WHAT IS LANGSMITH?
# ============================================================

print("""
WHAT IS LANGSMITH?
==================
FROM DOCS: "A platform for capturing, debugging, evaluating,
and monitoring LLM application behavior."

WHY YOU NEED IT:
┌─────────────────────────────────────────────────────────────────┐
│ Problem: LLMs are NON-DETERMINISTIC                             │
│          Same prompt → Different responses                      │
│          Hard to debug, hard to reproduce issues                │
│                                                                 │
│ Solution: TRACING                                               │
│          Record EVERY step of agent execution                   │
│          - Initial user input                                   │
│          - All tool calls                                       │
│          - Model interactions                                   │
│          - Decision points                                      │
│          - Final response                                       │
└─────────────────────────────────────────────────────────────────┘

KEY CONCEPTS:
┌─────────────────────────────────────────────────────────────────┐
│ TRACE = Full record of what happened (input → output)          │
│ RUN   = Individual step within a trace (LLM call, tool call)   │
│                                                                 │
│ Example trace:                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ User: "What's the weather in Tokyo?"                        │ │
│ │   └─ Run 1: LLM decides to call weather tool               │ │
│ │       └─ Run 2: weather_tool("Tokyo") → "25°C, sunny"      │ │
│ │           └─ Run 3: LLM generates response                 │ │
│ │               └─ Output: "The weather in Tokyo is 25°C..." │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# ENABLING TRACING (SIMPLE WAY)
# ============================================================

print("=" * 70)
print("ENABLING TRACING (FROM DOCS)")
print("=" * 70)

print("""
METHOD 1: Environment Variables (Recommended)
┌─────────────────────────────────────────────────────────────────┐
│ # In your .env file or shell:                                  │
│ export LANGSMITH_TRACING=true                                   │
│ export LANGSMITH_API_KEY=lsv2_...                              │
│                                                                 │
│ # Optional:                                                     │
│ export LANGSMITH_PROJECT=my-project-name                        │
│ export LANGSMITH_ENDPOINT=https://api.smith.langchain.com      │
│                                                                 │
│ That's it! All LangChain/Deep Agents automatically traced.     │
└─────────────────────────────────────────────────────────────────┘

METHOD 2: Programmatic (For fine control)
┌─────────────────────────────────────────────────────────────────┐
│ from langsmith import Client, tracing_context                   │
│                                                                 │
│ client = Client(                                                │
│     api_key="YOUR_LANGSMITH_API_KEY",                          │
│     api_url="https://api.smith.langchain.com",                 │
│ )                                                               │
│                                                                 │
│ # Trace specific code blocks:                                   │
│ with tracing_context(enabled=True):                            │
│     agent.invoke(...)  # Only this is traced                   │
│                                                                 │
│ # Or disable for specific blocks:                               │
│ with tracing_context(enabled=False):                           │
│     agent.invoke(...)  # This is NOT traced                    │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# CHECK CURRENT TRACING STATUS
# ============================================================

print("=" * 70)
print("CHECKING YOUR TRACING STATUS")
print("=" * 70)

langsmith_key = os.getenv("LANGSMITH_API_KEY")
langsmith_tracing = os.getenv("LANGSMITH_TRACING", "false")
langsmith_project = os.getenv("LANGSMITH_PROJECT", "default")

print(f"""
Your current configuration:
- LANGSMITH_API_KEY: {"✅ Set" if langsmith_key else "❌ NOT SET"}
- LANGSMITH_TRACING: {langsmith_tracing}
- LANGSMITH_PROJECT: {langsmith_project}
""")

if not langsmith_key:
    print("""
⚠️  LANGSMITH_API_KEY not set!

To enable tracing:
1. Go to https://smith.langchain.com
2. Create account / Sign in
3. Go to Settings → API Keys
4. Create new API key
5. Add to your .env:
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=lsv2_...
""")

# ============================================================
# DEMO: Agent with Tracing
# ============================================================

print("=" * 70)
print("DEMO: Create Agent (Tracing Auto-Enabled if API key set)")
print("=" * 70)

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"

@tool
def get_weather(city: str) -> str:
    """Get weather for a city (simulated)."""
    # Simulated weather data
    weather_data = {
        "tokyo": "25°C, Sunny",
        "london": "15°C, Cloudy",
        "new york": "20°C, Partly cloudy",
    }
    return weather_data.get(city.lower(), f"Weather data not available for {city}")

agent = create_deep_agent(
    model=model,
    tools=[calculate, get_weather],
)

print("""
Agent created with tools: calculate, get_weather

If LANGSMITH_TRACING=true and LANGSMITH_API_KEY is set,
every invoke() call will be automatically traced!
""")

# Only run if tracing is enabled
if langsmith_key and langsmith_tracing.lower() == "true":
    print("-" * 70)
    print("Running agent (will be traced to LangSmith)...")
    print("-" * 70)

    response = agent.invoke({
        "messages": [{"role": "user", "content": "What's the weather in Tokyo?"}]
    }, config={"configurable": {"thread_id": "langsmith-demo"}})

    print(f"Response: {response['messages'][-1].content}")
    print(f"\n✅ Trace sent to LangSmith! View at: https://smith.langchain.com")
else:
    print("-" * 70)
    print("Skipping invoke (tracing not enabled)")
    print("To see traces, add to .env:")
    print("  LANGSMITH_TRACING=true")
    print("  LANGSMITH_API_KEY=your_key_here")
    print("-" * 70)

# ============================================================
# LANGSMITH FEATURES
# ============================================================

print("\n" + "=" * 70)
print("LANGSMITH FEATURES")
print("=" * 70)

print("""
1. TRACING (Observability)
┌─────────────────────────────────────────────────────────────────┐
│ • See every step of agent execution                             │
│ • Debug why agent made specific decisions                       │
│ • View tool calls, inputs, outputs                              │
│ • Track latency per step                                        │
│ • Filter by project, tags, metadata                             │
└─────────────────────────────────────────────────────────────────┘

2. EVALUATION
┌─────────────────────────────────────────────────────────────────┐
│ • Run agent over test datasets                                  │
│ • Score outputs with custom evaluators                          │
│ • Compare different model versions                              │
│ • A/B test prompts                                              │
└─────────────────────────────────────────────────────────────────┘

3. MONITORING
┌─────────────────────────────────────────────────────────────────┐
│ • Create dashboards for key metrics                             │
│ • Set alerts for performance issues                             │
│ • Track usage patterns in production                            │
└─────────────────────────────────────────────────────────────────┘

4. FEEDBACK
┌─────────────────────────────────────────────────────────────────┐
│ • Collect user feedback on outputs                              │
│ • Annotation queues for human review                            │
│ • Use feedback to improve prompts                               │
└─────────────────────────────────────────────────────────────────┘

5. PROMPT ENGINEERING
┌─────────────────────────────────────────────────────────────────┐
│ • Playground for testing prompts                                │
│ • Version control for prompts                                   │
│ • Share prompts via Prompt Hub                                  │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# CUSTOM TRACING WITH @traceable
# ============================================================

print("=" * 70)
print("CUSTOM TRACING WITH @traceable")
print("=" * 70)

print("""
You can trace ANY function, not just agents:

┌─────────────────────────────────────────────────────────────────┐
│ from langsmith import traceable                                 │
│                                                                 │
│ @traceable(run_type="tool", name="My Custom Tool")             │
│ def my_custom_function(input: str) -> str:                     │
│     # Your code here                                            │
│     return result                                               │
│                                                                 │
│ @traceable(run_type="chain", name="My Pipeline")               │
│ def my_pipeline(question: str):                                │
│     context = retrieve_context(question)                        │
│     response = generate_response(context)                       │
│     return response                                             │
│                                                                 │
│ # run_type options:                                             │
│ # - "llm"   : LLM calls                                        │
│ # - "tool"  : Tool/function calls                              │
│ # - "chain" : Multi-step pipelines                             │
│ # - "agent" : Agent invocations                                │
└─────────────────────────────────────────────────────────────────┘

ADDING METADATA:
┌─────────────────────────────────────────────────────────────────┐
│ @traceable(                                                     │
│     name="search_documents",                                    │
│     run_type="tool",                                            │
│     tags=["search", "rag"],                                    │
│     metadata={"version": "1.0"}                                │
│ )                                                               │
│ def search_documents(query: str):                              │
│     ...                                                         │
│                                                                 │
│ # Tags and metadata help filter traces in UI                   │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# DEEP AGENTS SPECIFIC TRACING
# ============================================================

print("=" * 70)
print("DEEP AGENTS + LANGSMITH (FROM DOCS)")
print("=" * 70)

print("""
FROM DOCS:
"Deep agents supports native LangSmith tracing.
 Traces are emitted automatically when LangSmith tracing is enabled."

WHAT GETS TRACED AUTOMATICALLY:
┌─────────────────────────────────────────────────────────────────┐
│ ✅ All LLM calls                                                │
│ ✅ All tool executions                                          │
│ ✅ Subagent invocations                                         │
│ ✅ File operations (read, write, edit)                          │
│ ✅ Planning steps                                               │
│ ✅ Human-in-the-loop decisions                                  │
└─────────────────────────────────────────────────────────────────┘

CUSTOMIZE DEEP AGENTS TRACING:
┌─────────────────────────────────────────────────────────────────┐
│ # Install langsmith for customization                           │
│ pip install langsmith                                           │
│                                                                 │
│ from langsmith import traceable                                 │
│                                                                 │
│ # Trace specific invocations with custom metadata:              │
│ @traceable(name="my_agent_run", tags=["production"])           │
│ def run_agent(user_input: str):                                │
│     return agent.invoke({                                       │
│         "messages": [{"role": "user", "content": user_input}]  │
│     })                                                          │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# MENTAL MODEL
# ============================================================

print("=" * 70)
print("MENTAL MODEL (MM-012): LangSmith Integration")
print("=" * 70)

print("""
LANGSMITH = Observability platform for LLM applications

QUICK START:
┌─────────────────────────────────────────────────────────────────┐
│ 1. Get API key from https://smith.langchain.com                │
│ 2. Add to .env:                                                 │
│    LANGSMITH_TRACING=true                                       │
│    LANGSMITH_API_KEY=lsv2_...                                  │
│ 3. Run your agent - traces appear automatically!               │
└─────────────────────────────────────────────────────────────────┘

WHEN TO USE:
┌─────────────────────────────────────────────────────────────────┐
│ Development  → Debug why agent made wrong decisions            │
│ Testing      → Evaluate agent on test datasets                 │
│ Production   → Monitor performance, catch issues               │
│ Improvement  → Collect feedback, improve prompts               │
└─────────────────────────────────────────────────────────────────┘

KEY INSIGHT:
┌─────────────────────────────────────────────────────────────────┐
│ LLMs are BLACK BOXES - you can't see inside                    │
│ LangSmith OPENS the box - see every decision                   │
│                                                                 │
│ Without tracing: "Why did it do that?" 🤷                      │
│ With tracing:    "Ah, it chose tool X because..." 💡           │
└─────────────────────────────────────────────────────────────────┘

COMPARISON TO CLAUDE CODE:
┌─────────────────────────────────────────────────────────────────┐
│ Deep Agents         │ Claude Code                               │
├─────────────────────────────────────────────────────────────────┤
│ LangSmith tracing   │ Built-in observability                   │
│ @traceable decorator│ Automatic tool logging                   │
│ Custom dashboards   │ /tasks command                           │
│ Evaluation datasets │ --debug flag                             │
│ Prompt Hub          │ Skills system                            │
└─────────────────────────────────────────────────────────────────┘
""")

print("=" * 70)
print("Demo complete! Day 11: LangSmith Integration")
print("=" * 70)
