from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

load_dotenv()

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

workspace_dir = "./"

print("=" * 70)
print("SUBAGENTS DEEP DIVE - Code Review System")
print("=" * 70)

print("""
USE CASE: Code Review System

Main agent (Supervisor) coordinates 3 specialized subagents:
┌─────────────────────────────────────────────────────────────────┐
│                         MAIN AGENT                              │
│                    "Code Review Coordinator"                    │
│                                                                 │
│    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│    │   quality   │  │  security   │  │    test     │           │
│    │   checker   │  │   checker   │  │  suggester  │           │
│    └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                                 │
│ Each subagent:                                                  │
│ - Has FRESH context (doesn't see others' work)                  │
│ - Returns SUMMARY to main agent                                 │
│ - Can have different model/tools                                │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# DEFINE SPECIALIZED TOOLS FOR EACH SUBAGENT
# ============================================================

@tool
def analyze_code_style(code: str) -> str:
    """Analyze code for style issues like naming, formatting."""
    print("    [TOOL] analyze_code_style running...")
    # Simulated analysis
    issues = [
        "Line 5: Variable 'x' should have descriptive name",
        "Line 12: Missing docstring for function",
        "Line 20: Line too long (95 chars, max 88)"
    ]
    return f"Style issues found:\n" + "\n".join(f"- {i}" for i in issues)

@tool
def check_security_vulnerabilities(code: str) -> str:
    """Check code for security vulnerabilities."""
    print("    [TOOL] check_security_vulnerabilities running...")
    # Simulated analysis
    vulns = [
        "CRITICAL: SQL injection risk at line 15",
        "WARNING: Hardcoded secret at line 8",
        "INFO: Consider using parameterized queries"
    ]
    return f"Security scan results:\n" + "\n".join(f"- {v}" for v in vulns)

@tool
def suggest_test_cases(code: str) -> str:
    """Suggest test cases for the given code."""
    print("    [TOOL] suggest_test_cases running...")
    # Simulated suggestions
    tests = [
        "Test: Empty input handling",
        "Test: Boundary conditions (max/min values)",
        "Test: Error case - invalid user ID",
        "Test: Happy path - valid credentials"
    ]
    return f"Suggested test cases:\n" + "\n".join(f"- {t}" for t in tests)

# ============================================================
# DEFINE 3 SPECIALIZED SUBAGENTS
# ============================================================

subagents = [
    # SUBAGENT 1: Quality Checker
    {
        "name": "quality_checker",
        "description": "Analyzes code for quality issues like naming, formatting, and best practices",
        "system_prompt": """You are a code quality expert.
When given code to review:
1. Use the analyze_code_style tool
2. Summarize the findings
3. Return a brief quality report (max 5 bullet points)

Focus ONLY on code quality - not security or tests.""",
        "tools": [analyze_code_style],
        # Could use cheaper model for simple checks:
        # "model": "openai:gpt-4o-mini",
    },

    # SUBAGENT 2: Security Checker
    {
        "name": "security_checker",
        "description": "Scans code for security vulnerabilities and risks",
        "system_prompt": """You are a security expert.
When given code to review:
1. Use the check_security_vulnerabilities tool
2. Prioritize findings by severity (CRITICAL > WARNING > INFO)
3. Return a brief security report (max 5 bullet points)

Focus ONLY on security - not style or tests.""",
        "tools": [check_security_vulnerabilities],
    },

    # SUBAGENT 3: Test Suggester
    {
        "name": "test_suggester",
        "description": "Suggests test cases for code to ensure proper coverage",
        "system_prompt": """You are a testing expert.
When given code to review:
1. Use the suggest_test_cases tool
2. Organize tests by category (unit, integration, edge cases)
3. Return a brief test plan (max 5 bullet points)

Focus ONLY on testing - not style or security.""",
        "tools": [suggest_test_cases],
    },
]

print("SUBAGENTS DEFINED:")
for sa in subagents:
    print(f"  - {sa['name']}: {sa['description'][:50]}...")

# ============================================================
# CREATE MAIN AGENT WITH SUBAGENTS
# ============================================================

agent = create_deep_agent(
    model=model,
    backend=FilesystemBackend(root_dir=workspace_dir, virtual_mode=True),
    subagents=subagents,  # Enable all 3 subagents
)

print("\nMain agent created with 3 specialized subagents!")

# ============================================================
# TEST: Full Code Review
# ============================================================

print("\n" + "=" * 70)
print("TEST: Request a complete code review")
print("=" * 70)

# Sample code to review
sample_code = '''
def get_user(user_id):
    x = user_id
    query = "SELECT * FROM users WHERE id = " + x
    result = db.execute(query)
    pwd = "secret123"
    return result
'''

task = f"""
Please do a complete code review of this code:

```python
{sample_code}
```

Use ALL THREE of your specialized subagents:
1. quality_checker - for code style issues
2. security_checker - for security vulnerabilities
3. test_suggester - for test recommendations

Then combine their findings into a final review report.
"""

print(f"User request: Review this code with all 3 subagents\n")

response = agent.invoke({
    "messages": [{"role": "user", "content": task}]
},
config={"configurable": {"thread_id": "subagent-demo", "assistant_id": "test"}}
)

print("[MAIN AGENT RESPONSE]:")
print("-" * 70)
print(response["messages"][-1].content)

# ============================================================
# EXPLANATION
# ============================================================

print("\n" + "=" * 70)
print("WHAT HAPPENED (Behind the Scenes)")
print("=" * 70)
print("""
FLOW:
┌─────────────────────────────────────────────────────────────────┐
│ 1. User asks for code review                                    │
│                                                                 │
│ 2. Main agent sees 3 available subagents:                       │
│    - quality_checker: "Analyzes code for quality..."           │
│    - security_checker: "Scans code for security..."            │
│    - test_suggester: "Suggests test cases..."                  │
│                                                                 │
│ 3. Main agent calls task() for each:                           │
│    task(name="quality_checker", input="Review this code...")   │
│    task(name="security_checker", input="Scan this code...")    │
│    task(name="test_suggester", input="Suggest tests...")       │
│                                                                 │
│ 4. Each subagent runs in FRESH context:                         │
│    - Gets its system_prompt + the task                          │
│    - Uses its specialized tools                                 │
│    - Returns summary to main agent                              │
│                                                                 │
│ 5. Main agent combines results into final report                │
└─────────────────────────────────────────────────────────────────┘

CONTEXT ISOLATION:
┌─────────────────────────────────────────────────────────────────┐
│ Main agent context:                                             │
│ - User request                                                  │
│ - Summary from quality_checker (small)                          │
│ - Summary from security_checker (small)                         │
│ - Summary from test_suggester (small)                           │
│                                                                 │
│ NOT in main context:                                            │
│ - All the tool calls subagents made                             │
│ - Full tool outputs                                             │
│ - Subagent reasoning traces                                     │
│                                                                 │
│ RESULT: Main agent stays lean even with 3 subagents!           │
└─────────────────────────────────────────────────────────────────┘

STATELESS SUBAGENTS:
┌─────────────────────────────────────────────────────────────────┐
│ quality_checker does NOT know what security_checker found       │
│ security_checker does NOT know what test_suggester suggested    │
│                                                                 │
│ Only the MAIN AGENT sees all results and combines them!        │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# ADVANCED: Show config options
# ============================================================

print("\n" + "=" * 70)
print("ADVANCED CONFIGURATION OPTIONS")
print("=" * 70)
print("""
FULL SUBAGENT CONFIG:
┌─────────────────────────────────────────────────────────────────┐
│ {                                                               │
│     "name": "security_checker",        # Required               │
│     "description": "Scans for vulns",  # Required               │
│     "system_prompt": "You are...",     # Required               │
│     "tools": [check_vuln_tool],        # Optional               │
│     "model": "openai:gpt-4o-mini",     # Optional (cheaper!)    │
│     "middleware": [LoggingMiddleware], # Optional               │
│     "interrupt_on": {"delete": True},  # Optional (HITL)        │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘

COST OPTIMIZATION PATTERN:
┌─────────────────────────────────────────────────────────────────┐
│ Main agent: claude-sonnet (smart, coordinates)                  │
│ Subagents:  gpt-4o-mini (cheaper, specialized tasks)            │
│                                                                 │
│ Result: Smart orchestration + cheap execution = $$$ saved       │
└─────────────────────────────────────────────────────────────────┘

COMPILED SUBAGENT (Full LangGraph):
┌─────────────────────────────────────────────────────────────────┐
│ from deepagents import CompiledSubAgent                         │
│                                                                 │
│ # Your custom multi-step workflow                               │
│ custom_graph = create_agent(...)                                │
│                                                                 │
│ complex_subagent = CompiledSubAgent(                            │
│     name="complex-workflow",                                    │
│     description="Runs multi-step analysis",                     │
│     runnable=custom_graph                                       │
│ )                                                               │
│                                                                 │
│ # Use it like any other subagent                                │
│ subagents = [complex_subagent, ...]                             │
└─────────────────────────────────────────────────────────────────┘
""")
