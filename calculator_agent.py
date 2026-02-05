from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from langchain.tools import tool

load_dotenv()

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

@tool
def add(a: float, b: float) -> float:
    """
    Add two numbers
    
    :param a: first number
    :type a: float
    :param b: Second number
    :type b: float
    :return: a + b 
    :rtype: float
    """
    return a + b

@tool
def subtract(a: float, b: float) -> float:
    """
    Subtract two given numbers
    USe this function when the user needs to ffind the difference of two numbers or subtract or minus
    
    :param a: first number
    :type a: float
    :param b: second number
    :type b: float
    :return: a - b
    :rtype: float
    """
    return a - b

@tool
def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers
    use this when the user needs product or times or multiplication of 2 numbers
    
    :param a: first number 
    :type a: float
    :param b: secong number
    :type b: float
    :return: a * b
    :rtype: float
    """
    return a* b

@tool
def divide(a: float, b: float) -> float:
    """
    divide 2 numbers
    USe this to divide 2 numbers or one number by another
    
    :param a: first number
    :type a: float
    :param b: seconf number 
    :type b: float
    :return: a / b
    :rtype: float
    """
    return a/b

agent = create_deep_agent(
    model=model,
    tools=[add, subtract, multiply, divide]
    )

response = agent.invoke({
    "messages":[{"role": "user", "content":"What is 2.345 * 1.415 / 2.6 * (2*5)"}]
})

print(response["messages"][-1].content)
