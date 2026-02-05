from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from deepagents.backends import FilesystemBackend
import os

load_dotenv()

sandbox_dir = ("./agent_files")
os.makedirs(sandbox_dir, exist_ok=True)

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

agent = create_deep_agent(
    model=model,
    backend=FilesystemBackend(root_dir=sandbox_dir, virtual_mode=True)
)

response = agent.invoke({
    "messages":[{"role": "user", "content":" create a file agent.txt , info \' ths is my frist backend\'"
                 }]
})


print(response["messages"][-1].content)

