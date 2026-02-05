# hello_agent.py - Your first Deep Agent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

# Load API keys from .env
load_dotenv()

# Create model (OpenAI GPT-4o-mini - fast and cheap)
model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# Create the agent
agent = create_deep_agent(model=model)

# Run it
result = agent.invoke({
    "messages": [{"role": "user", "content": "Createa file called test.txt with the content \"Hello from my first agent!\" and then read it back to me."}]
})

# Print response
print(result["messages"][-1].content)
