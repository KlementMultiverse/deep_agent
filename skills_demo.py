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
print("SKILLS DEMO - Progressive Disclosure")
print("=" * 70)

print("""
THE CONCEPT:

STARTUP (what agent sees):
┌─────────────────────────────────────────────────────────────────┐
│ Available skills:                                               │
│ - python-best-practices: Use for Python best practices...      │
│                                                                 │
│ (Only name + description loaded - ~50 tokens)                   │
└─────────────────────────────────────────────────────────────────┘

WHEN SKILL NEEDED:
┌─────────────────────────────────────────────────────────────────┐
│ User: "What are Python best practices for error handling?"      │
│                                                                 │
│ Agent: "This matches 'python-best-practices' skill..."          │
│        [Loads FULL skill content - ~500 tokens]                 │
│        "According to best practices, use specific exceptions..."│
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# CREATE AGENT WITH SKILLS
# ============================================================

agent = create_deep_agent(
    model=model,
    backend=FilesystemBackend(root_dir=workspace_dir, virtual_mode=True),
    memory=["./AGENTS.md"],      # Always loaded
    skills=["./skills/"]         # Loaded on-demand!
)

# ============================================================
# TEST 1: Question that TRIGGERS skill
# ============================================================

print("=" * 70)
print("[TEST 1] Question that TRIGGERS skill loading")
print("=" * 70)
print("User: 'What are Python best practices for error handling?'\n")

response_1 = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "What are Python best practices for error handling? Give me a code example."
    }]
},
config={"configurable": {"thread_id": "skills-demo-1", "assistant_id": "test"}}
)

print("[RESPONSE] (agent loaded python-best-practices skill):")
print("-" * 70)
print(response_1["messages"][-1].content)

# ============================================================
# TEST 2: Question that does NOT trigger skill
# ============================================================

print("\n" + "=" * 70)
print("[TEST 2] Question that does NOT trigger skill")
print("=" * 70)
print("User: 'What is 2 + 2?'\n")

response_2 = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "What is 2 + 2?"
    }]
},
config={"configurable": {"thread_id": "skills-demo-2", "assistant_id": "test"}}
)

print("[RESPONSE] (no skill loaded - simple question):")
print("-" * 70)
print(response_2["messages"][-1].content)

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("KEY INSIGHT: Progressive Disclosure")
print("=" * 70)
print("""
TEST 1: "Python best practices for error handling?"
        → Agent recognized this matches skill description
        → Loaded FULL skill content
        → Used detailed guidelines from skill

TEST 2: "What is 2 + 2?"
        → No skill match needed
        → Agent answered directly
        → Skill content NOT loaded (saved tokens!)

┌─────────────────────────────────────────────────────────────────┐
│ STARTUP COST:                                                   │
│ - memory=["./AGENTS.md"]  → Always loaded (~100 tokens)         │
│ - skills=["./skills/"]    → Only frontmatter (~50 tokens)       │
│                                                                 │
│ TOTAL STARTUP: ~150 tokens (not thousands!)                     │
│                                                                 │
│ RUNTIME:                                                        │
│ - Skill loaded ONLY when question matches description           │
│ - Scales to 100+ skills without startup cost                    │
└─────────────────────────────────────────────────────────────────┘

PATTERN: memory=[] for ALWAYS needed, skills=[] for ON-DEMAND
""")
