from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

load_dotenv()

model = ChatOpenAI(
	model="gpt-4o-mini",
	temperature=0
)

agent = create_deep_agent(model=model)

response = agent.invoke({
	"messages":[{"role": "user", "content": "Hi can u createa file and print the contents of the file with :\' Hello ur klement\'"}]
})

print(response["messages"][-1].content)

