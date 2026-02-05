from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from deepagents.backends import StoreBackend
from langgraph.store.memory import InMemoryStore

load_dotenv()

store = InMemoryStore()

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

agent = create_deep_agent(
    model=model,
    backend= lambda rt: StoreBackend(rt),
    store=store
)

response = agent.invoke({
    "messages":[{"role": "user", "content": " create a file typed.txt, info \' my name is klement\'"}]
    },
    config={"configurable":{"thread_id":"User_klement",
                            "assistant_id":"mom"}}
)

response1 = agent.invoke({
    "messages":[{"role": "user", "content": "read the file typed.txt and show me ALL its contents"}]
    },
    config={"configurable":{"thread_id":"User_X",
                            "assistant_id":"klement"}}
)

print(response["messages"][-1].content)
print(response1["messages"][-1].content)