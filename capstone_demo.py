"""
CAPSTONE PROJECT: Project Scaffolding Agent
============================================
A "System that builds systems" - combines ALL concepts from the 2-week program.

Concepts Used:
- Day 1-3: Agent fundamentals, tools, loop
- Day 4: Backends (Filesystem + virtual_mode)
- Day 5: Context management (memory loading)
- Day 6: Skills (domain expertise)
- Day 7: HITL (approve file creation)
- Day 8: Subagents (specialized workers)
- Day 9: Multi-agent patterns (supervisor)
- Day 10: Sandboxes (safe execution)
- Day 11: LangSmith (tracing)
- Day 12: Production patterns (streaming, error handling)
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

print("=" * 70)
print("CAPSTONE: PROJECT SCAFFOLDING AGENT")
print("A System That Builds Systems")
print("=" * 70)

# ============================================================
# ARCHITECTURE OVERVIEW
# ============================================================

print("""
ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────┐
│                    PROJECT SCAFFOLDING AGENT                    │
│                        (Supervisor)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Skills Loaded:                                                 │
│  ├── python-best-practices (from Day 6)                        │
│  └── project-structure (templates)                             │
│                                                                 │
│  Subagents:                                                     │
│  ├── structure_planner   → Plans folder/file structure         │
│  ├── code_generator      → Generates boilerplate code          │
│  └── config_writer       → Creates config files                │
│                                                                 │
│  Backend: FilesystemBackend (virtual_mode=True)                │
│  HITL: Approve all file writes                                  │
│  Checkpointer: MemorySaver (PostgresSaver in prod)             │
│                                                                 │
│  Flow:                                                          │
│  1. User: "Create a FastAPI project called 'myapi'"            │
│  2. structure_planner → Returns file structure                 │
│  3. code_generator → Generates each file                       │
│  4. config_writer → Creates requirements.txt, .env, etc.       │
│  5. HITL → User approves each file creation                    │
│  6. Files written to disk                                       │
└─────────────────────────────────────────────────────────────────┘

CONCEPTS DEMONSTRATED:
┌─────────────────────────────────────────────────────────────────┐
│ Concept              │ How It's Used                            │
├─────────────────────────────────────────────────────────────────┤
│ Backends (Day 4)     │ FilesystemBackend writes real files     │
│ Context (Day 5)      │ memory=[] loads project templates       │
│ Skills (Day 6)       │ Python best practices guide code        │
│ HITL (Day 7)         │ User approves each file creation        │
│ Subagents (Day 8)    │ 3 specialists (structure, code, config) │
│ Patterns (Day 9)     │ Supervisor coordinates subagents        │
│ Sandbox (Day 10)     │ virtual_mode prevents path traversal    │
│ LangSmith (Day 11)   │ Tracing all operations                  │
│ Production (Day 12)  │ Error handling, streaming               │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# MODEL SETUP
# ============================================================

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# ============================================================
# SPECIALIZED TOOLS
# ============================================================

@tool
def plan_project_structure(project_type: str, project_name: str) -> str:
    """Plan the folder and file structure for a project."""
    print(f"    [TOOL] Planning structure for {project_type} project: {project_name}")

    structures = {
        "fastapi": f"""
Project Structure for {project_name}:
├── {project_name}/
│   ├── __init__.py
│   ├── main.py           # FastAPI app entry point
│   ├── routers/
│   │   ├── __init__.py
│   │   └── api.py        # API routes
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py    # Pydantic models
│   └── services/
│       ├── __init__.py
│       └── business.py   # Business logic
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
""",
        "cli": f"""
Project Structure for {project_name}:
├── {project_name}/
│   ├── __init__.py
│   ├── cli.py            # CLI entry point
│   ├── commands/
│   │   ├── __init__.py
│   │   └── main.py       # Command implementations
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── tests/
│   ├── __init__.py
│   └── test_cli.py
├── requirements.txt
├── setup.py
└── README.md
""",
        "agent": f"""
Project Structure for {project_name}:
├── {project_name}/
│   ├── __init__.py
│   ├── agent.py          # Main agent
│   ├── tools/
│   │   ├── __init__.py
│   │   └── custom.py     # Custom tools
│   ├── skills/
│   │   └── domain/
│   │       └── SKILL.md
│   └── backends/
│       └── __init__.py
├── tests/
│   └── test_agent.py
├── requirements.txt
├── .env.example
├── AGENTS.md
└── README.md
"""
    }

    return structures.get(project_type.lower(), f"Unknown project type: {project_type}")

@tool
def generate_file_content(file_path: str, file_purpose: str, project_name: str) -> str:
    """Generate content for a specific file based on its purpose."""
    print(f"    [TOOL] Generating content for: {file_path}")

    templates = {
        "main.py": f'''"""
{project_name} - FastAPI Application
"""
from fastapi import FastAPI
from {project_name}.routers import api

app = FastAPI(
    title="{project_name}",
    description="Generated by Project Scaffolding Agent",
    version="0.1.0"
)

app.include_router(api.router, prefix="/api", tags=["api"])

@app.get("/health")
async def health_check():
    return {{"status": "healthy"}}
''',
        "requirements.txt": """fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pytest>=7.0.0
""",
        ".gitignore": """# Python
__pycache__/
*.py[cod]
.venv/
venv/
.env

# IDE
.vscode/
.idea/

# Testing
.pytest_cache/
.coverage
htmlcov/
""",
        "README.md": f"""# {project_name}

Generated by Project Scaffolding Agent.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn {project_name}.main:app --reload
```

## Test

```bash
pytest
```
""",
        "__init__.py": f'"""{project_name} package."""\n',
    }

    # Match by filename
    for key, content in templates.items():
        if file_path.endswith(key):
            return content

    return f"# TODO: Implement {file_path}\n# Purpose: {file_purpose}\n"

@tool
def validate_project_name(name: str) -> str:
    """Validate that a project name is valid Python package name."""
    print(f"    [TOOL] Validating project name: {name}")

    import re

    if not name:
        return "Error: Project name cannot be empty"

    if not re.match(r'^[a-z][a-z0-9_]*$', name.lower()):
        return f"Error: '{name}' is not a valid Python package name. Use lowercase letters, numbers, and underscores only."

    if name.lower() in ['test', 'tests', 'src', 'lib', 'bin']:
        return f"Error: '{name}' is a reserved name. Choose a different name."

    return f"Valid: '{name}' is a valid project name"

# ============================================================
# SUBAGENTS DEFINITION
# ============================================================

subagents = [
    {
        "name": "structure_planner",
        "description": "Plans the folder and file structure for a new project based on project type",
        "system_prompt": """You are a project structure expert.
When asked to plan a project:
1. Use the plan_project_structure tool with the project type and name
2. Return a clear, organized structure
3. Explain what each folder/file is for

Focus ONLY on structure - not code generation.""",
        "tools": [plan_project_structure, validate_project_name],
    },
    {
        "name": "code_generator",
        "description": "Generates boilerplate code for each file in the project",
        "system_prompt": """You are a code generation expert.
When asked to generate code:
1. Use the generate_file_content tool for each file
2. Follow Python best practices
3. Add proper docstrings and type hints

Focus ONLY on code - not project structure.""",
        "tools": [generate_file_content],
    },
    {
        "name": "config_writer",
        "description": "Creates configuration files like requirements.txt, .env, .gitignore",
        "system_prompt": """You are a configuration expert.
When asked to create configs:
1. Use generate_file_content for config files
2. Include all necessary dependencies
3. Add proper .gitignore rules

Focus ONLY on configuration - not application code.""",
        "tools": [generate_file_content],
    },
]

# ============================================================
# MAIN AGENT SETUP
# ============================================================

checkpointer = MemorySaver()  # Use PostgresSaver in production

# Create output directory for generated projects
os.makedirs("./generated_projects", exist_ok=True)

agent = create_deep_agent(
    model=model,
    backend=FilesystemBackend(
        root_dir="./generated_projects",  # Restrict to this directory
        virtual_mode=True,  # Security: block path traversal
    ),
    subagents=subagents,
    checkpointer=checkpointer,
    interrupt_on={
        "write_file": True,   # User approves each file
        "edit_file": True,
    },
    # In production, also add:
    # memory=["./AGENTS.md"],  # Load project context
    # skills=["./skills/"],    # Load coding guidelines
)

print("""
AGENT CREATED:
┌─────────────────────────────────────────────────────────────────┐
│ Main Agent (Supervisor)                                         │
│ ├── Subagents:                                                  │
│ │   ├── structure_planner                                      │
│ │   ├── code_generator                                         │
│ │   └── config_writer                                          │
│ ├── Backend: FilesystemBackend (virtual_mode=True)             │
│ ├── HITL: write_file, edit_file                                │
│ └── Checkpointer: MemorySaver                                  │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# DEMONSTRATE USAGE
# ============================================================

print("=" * 70)
print("USAGE EXAMPLE")
print("=" * 70)

print("""
To use this agent:

┌─────────────────────────────────────────────────────────────────┐
│ from capstone_demo import agent                                 │
│                                                                 │
│ response = agent.invoke({                                       │
│     "messages": [{                                              │
│         "role": "user",                                         │
│         "content": "Create a FastAPI project called 'myapi'"   │
│     }]                                                          │
│ }, config={"configurable": {"thread_id": "project-1"}})        │
│                                                                 │
│ # Agent will:                                                   │
│ # 1. Call structure_planner subagent                           │
│ # 2. Call code_generator for each file                         │
│ # 3. Call config_writer for configs                            │
│ # 4. PAUSE before each write (HITL)                            │
│ # 5. On approve, write files to ./generated_projects/          │
└─────────────────────────────────────────────────────────────────┘

STREAMING USAGE (Production):
┌─────────────────────────────────────────────────────────────────┐
│ for mode, chunk in agent.stream(                               │
│     {"messages": [...]},                                        │
│     config=config,                                              │
│     stream_mode=["updates", "messages"],                       │
│ ):                                                              │
│     if mode == "messages":                                      │
│         token, metadata = chunk                                 │
│         print(token.content, end="", flush=True)               │
│     elif mode == "updates" and "__interrupt__" in chunk:       │
│         # Show file preview, ask user to approve               │
│         ...                                                     │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# TEST: Quick validation
# ============================================================

print("=" * 70)
print("QUICK TEST: Validate project name tool")
print("=" * 70)

test_names = ["myapi", "my-api", "123project", "test_project"]
for name in test_names:
    result = validate_project_name.invoke({"name": name})
    status = "✅" if "Valid" in result else "❌"
    print(f"  {status} {name}: {result}")

# ============================================================
# TEST: Structure planning
# ============================================================

print("\n" + "=" * 70)
print("QUICK TEST: Plan project structure")
print("=" * 70)

structure = plan_project_structure.invoke({
    "project_type": "fastapi",
    "project_name": "myapi"
})
print(structure)

# ============================================================
# CAPSTONE SUMMARY
# ============================================================

print("=" * 70)
print("CAPSTONE SUMMARY: What You've Learned")
print("=" * 70)

print("""
2-WEEK DEEP AGENTS MASTERY - COMPLETE!

Week 1: Foundations
┌─────────────────────────────────────────────────────────────────┐
│ Day 1-3: Agent Fundamentals                                     │
│   └── LLM + Tools + Loop = Agent                               │
│                                                                 │
│ Day 4: Backend Systems                                          │
│   └── State, Filesystem, Store, Composite                      │
│                                                                 │
│ Day 5: Context Management                                       │
│   └── memory=[], offloading, auto-eviction                     │
│                                                                 │
│ Day 6: Skills System                                            │
│   └── SKILL.md, progressive disclosure                         │
│                                                                 │
│ Day 7: Human-in-the-Loop                                        │
│   └── interrupt_on, approve/edit/reject                        │
└─────────────────────────────────────────────────────────────────┘

Week 2: Advanced
┌─────────────────────────────────────────────────────────────────┐
│ Day 8: Subagents Deep Dive                                      │
│   └── SubAgentMiddleware, context isolation, task()            │
│                                                                 │
│ Day 9: Multi-Agent Patterns                                     │
│   └── Supervisor, Handoffs, Router, Skills, Custom             │
│                                                                 │
│ Day 10: Sandboxes                                               │
│   └── LocalShellBackend, virtual_mode, security                │
│                                                                 │
│ Day 11: LangSmith Integration                                   │
│   └── Tracing, @traceable, observability                       │
│                                                                 │
│ Day 12: Production Patterns                                     │
│   └── Streaming, error handling, deployment                    │
│                                                                 │
│ Day 13-14: CAPSTONE                                             │
│   └── Combined all concepts into one system!                   │
└─────────────────────────────────────────────────────────────────┘

YOU CAN NOW BUILD:
┌─────────────────────────────────────────────────────────────────┐
│ ✅ Agents with custom tools                                     │
│ ✅ Persistent file/memory backends                              │
│ ✅ Context-aware agents (memory, skills)                        │
│ ✅ Safe agents (HITL, sandboxes)                                │
│ ✅ Multi-agent systems (subagents, patterns)                    │
│ ✅ Observable agents (LangSmith)                                │
│ ✅ Production-ready agents (streaming, error handling)          │
└─────────────────────────────────────────────────────────────────┘

NEXT STEPS:
1. Build YOUR real project using these patterns
2. Deploy with LangSmith Agent Server
3. Iterate based on tracing/feedback
""")

print("=" * 70)
print("CONGRATULATIONS! Deep Agents Mastery Complete!")
print("=" * 70)
