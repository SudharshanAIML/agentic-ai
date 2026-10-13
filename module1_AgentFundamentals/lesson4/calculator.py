from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import ToolMessage, HumanMessage
from dotenv import load_dotenv
load_dotenv()



@tool
def add(a: int, b: int) -> int:
    """Add two integers together."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers together."""
    return a * b


model = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0
)

tools = [add, multiply]
tool_registry = {
    "add": add,
    "multiply": multiply
}

model_with_tools = model.bind_tools(tools)



response = model_with_tools.invoke(
    "Calculate 25 + 17 and then multiply the result by 2."
)

tool_call = response.tool_calls[0]
tool = tool_registry[tool_call["name"]]
result = tool.invoke(tool_call["args"])
print(result)
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import ToolMessage, HumanMessage
from dotenv import load_dotenv
load_dotenv()



@tool
def add(a: int, b: int) -> int:
    """Add two integers together."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers together."""
    return a * b


model = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0
)

tools = [add, multiply]
tool_registry = {
    "add": add,
    "multiply": multiply
}

model_with_tools = model.bind_tools(tools)



response = model_with_tools.invoke(
    "Calculate 25 + 17 and then multiply the result by 2."
)

tool_call = response.tool_calls[0]
tool = tool_registry[tool_call["name"]]
result = tool.invoke(tool_call["args"])
print(result)

tool_message = ToolMessage(
    content=str(result),
    tool_call_id=tool_call["id"]
)


messages = [
    HumanMessage(
        content="Calculate 25 + 17 and then multiply the result by 2."
    ),
    response,
    tool_message
]

# Ask the model what to do next
response2 = model_with_tools.invoke(messages)

print("Next tool call:", response2.tool_calls)




# print(add.name)
# print(add.description)
# print(add.args)
# print(response)
# print(add.name)
# print(add.description)
# print(add.args)

# result = add.invoke({
#     "a": 5,
#     "b": 2,
# })

# print(result)

# print(add.name)
# print(add.description)
# print(add.args)
# print(response)
# print(add.name)
# print(add.description)
# print(add.args)

# result = add.invoke({
#     "a": 5,
#     "b": 2,
# })

# print(result)