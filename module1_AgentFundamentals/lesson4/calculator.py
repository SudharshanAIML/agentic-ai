from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()



@tool
def add(a: int, b: int) -> int:
    """Add two integers together."""
    return a + b




model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0
)

model_with_tools = model.bind_tools([add])



response = model_with_tools.invoke(
    "What is 25 + 17? and tell me who is the current president of India?"
)
print(add.name)
print(add.description)
print(add.args)
print(response)
# print(add.name)
# print(add.description)
# print(add.args)

# result = add.invoke({
#     "a": 5,
#     "b": 2,
# })

# print(result)