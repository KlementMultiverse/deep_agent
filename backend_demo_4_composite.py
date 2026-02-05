# backend_demo_4_composite.py
# Day 4 Hands-On: Backend Systems
#
# Shows: CompositeBackend - ROUTES paths to different backends
#
# KEY INSIGHT: CompositeBackend is a router. Different paths go to different storage.
# This gives you BOTH ephemeral scratch space AND persistent long-term memory.
#
# Path Routing:
#   /memories/*  → StoreBackend (persistent across threads)
#   everything else → StateBackend (ephemeral, this thread only)

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Store for persistent data
store = InMemoryStore()

# CompositeBackend: Routes by path prefix
# - /memories/* → StoreBackend (persistent)
# - default (everything else) → StateBackend (ephemeral)
agent = create_deep_agent(
    model=model,
    store=store,
    backend=lambda rt: CompositeBackend(
        default=StateBackend(rt),  # Default: ephemeral
        routes={
            "/memories/": StoreBackend(rt)  # /memories/*: persistent
        }
    )
)

print("=== EXAMPLE 4: CompositeBackend (Routing) ===")
print("Path routing: /memories/* → persistent, everything else → ephemeral")
print()

# Write to BOTH locations
print("--- Writing to both backends ---")
response1 = agent.invoke(
    {"messages": [{"role": "user", "content": """
        Do these two things:
        1. Write a file /scratch/temp_notes.txt with 'This is temporary'
        2. Write a file /memories/user_prefs.txt with 'User likes dark mode'
        Confirm when done.
    """}]},
    config={"configurable": {"thread_id": "thread-A"}}
)
print(response1["messages"][-1].content)
print()

# New thread: Try to read both
print("--- NEW THREAD: Reading both files ---")
response2 = agent.invoke(
    {"messages": [{"role": "user", "content": """
        Try to read these files and tell me what you find:
        1. /scratch/temp_notes.txt
        2. /memories/user_prefs.txt
    """}]},
    config={"configurable": {"thread_id": "thread-B"}}  # Different thread!
)
print(response2["messages"][-1].content)
print()

print("=== KEY INSIGHT ===")
print("/scratch/temp_notes.txt → NOT FOUND (ephemeral, lost between threads)")
print("/memories/user_prefs.txt → FOUND (persistent, survives across threads)")
print()
print("This is how agents have scratch space for current task + long-term memory!")
