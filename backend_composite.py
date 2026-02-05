from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend, FilesystemBackend
from langgraph.store.memory import InMemoryStore
import os

load_dotenv()

store = InMemoryStore()

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

disk_dir = "./disk_files"
os.makedirs(disk_dir, exist_ok=True)

agent = create_deep_agent(
    model=model,
    store=store,
    backend=lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={
            "/memories/": StoreBackend(rt),
            "/disk/": FilesystemBackend(root_dir=disk_dir, virtual_mode=True)
        }
    )
)

print("=== CompositeBackend Demo ===")
print("Testing 3 different storage routes...\n")

# Test 1: Write to default (StateBackend - ephemeral)
response1 = agent.invoke({
    "messages": [{"role": "user", "content": "Write a file /temp/notes.txt with text 'This is temporary'"}]
},
config={"configurable": {"thread_id": "thread-1", "assistant_id": "test"}}
)
print("1. Temp file:", response1["messages"][-1].content)

# Test 2: Write to /memories/ (StoreBackend - persistent)
response2 = agent.invoke({
    "messages": [{"role": "user", "content": "Write a file /memories/user_pref.txt with text 'User likes dark mode'"}]
},
config={"configurable": {"thread_id": "thread-1", "assistant_id": "test"}}
)
print("2. Memory file:", response2["messages"][-1].content)

# Test 3: Write to /disk/ (FilesystemBackend - real disk)
response3 = agent.invoke({
    "messages": [{"role": "user", "content": "Write a file /disk/output.txt with text 'This is on real disk'"}]
},
config={"configurable": {"thread_id": "thread-1", "assistant_id": "test"}}
)
print("3. Disk file:", response3["messages"][-1].content)

# Step 5: Verify Real Disk File
# Check if /disk/output.txt exists on real filesystem
real_path = os.path.join(disk_dir, "output.txt")
print(f"\n=== Verification ===")
if os.path.exists(real_path):
    with open(real_path) as f:
        print(f"Real file EXISTS: {real_path}")
        print(f"Contents: {f.read()}")
else:
    print(f"File not found: {real_path}")
