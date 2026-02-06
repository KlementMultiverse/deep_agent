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

agent = create_deep_agent(
    model=model,
    backend=FilesystemBackend(root_dir=workspace_dir, virtual_mode=True),
    memory=["./AGENTS.md"]
)

print("=== Context Memory Demo ===")
print("Agent loads AGENTS.md and formats code according to project rules")
print("NEW: Testing Response Style rule - should return ONLY code, no explanations\n")

# Bad code: camelCase, no type hints, no docstring
bad_code = """
def calculateTotal(itemList, taxRate):
    subTotal = 0
    for item in itemList:
        subTotal = subTotal + item
    finalTotal = subTotal + (subTotal * taxRate)
    return finalTotal
"""

print("INPUT (bad code):")
print(bad_code)
print("-" * 40)

response = agent.invoke({
    "messages": [{
        "role": "user",
        "content": f"Reformat this code according to project coding standards:\n{bad_code}"
    }]
},
config={"configurable": {"thread_id": "memory-demo", "assistant_id": "test"}}
)

print("OUTPUT (formatted by agent):")
print(response["messages"][-1].content)
