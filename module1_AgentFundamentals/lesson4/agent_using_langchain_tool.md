. The most important part
This is the part you should focus on:
tool_calls=[    {        'name': 'add',        'args': {            'a': 25,            'b': 17        },        'id': 'call_3689347',        'type': 'tool_call'    }]


This means:
The LLM decided that it wants the runtime to execute add(25, 17).

It has not executed add() yet.
Your Python function hasn't necessarily run at this point.
2. Let's separate the response into layers
Your response contains:
AIMessage
│
├── content=[]
│
├── additional_kwargs
│
├── response_metadata
│
├── id
│
├── tool_calls
│
├── invalid_tool_calls
│
└── usage_metadata

For agent development, the most important ones initially are:
content
tool_calls
response_metadata
usage_metadata

The huge thought_signatures field is provider-specific metadata. Don't try to build your agent around it.
3. content=[]
You got:
content=[]


At first this might look strange.
You might expect:
"What is 25 + 17?"

or something like:
"25 + 17 = 42"

But the model hasn't produced a normal textual answer yet.
Instead, it produced an action:
I want to call add()

So conceptually:
AIMessage
   │
   ├── text → none
   │
   └── tool call → add(25,17)

This is perfectly normal.
4. tool_calls
This is your gold mine:
response.tool_calls


will give:
[    {        'name': 'add',        'args': {            'a': 25,            'b': 17        },        'id': 'call_3689347',        'type': 'tool_call'    }]


So your runtime can do:
for tool_call in response.tool_calls:    print(tool_call["name"])    print(tool_call["args"])    print(tool_call["id"])


Output:
add
{'a': 25, 'b': 17}
call_3689347

5. Compare this with what we learned
Remember our manual conceptual tool call:
{
    "name": "add",
    "arguments": {
        "a": 25,
        "b": 17
    }
}

LangChain has essentially normalized that into:
{    "name": "add",    "args": {        "a": 25,        "b": 17    },    "id": "call_3689347",    "type": "tool_call"}


So:
LLM
 ↓
AIMessage
 ↓
tool_calls
 ↓
{name, args, id}

That's exactly the mechanism we were discussing.
6. Now something very interesting happened
Your user asked two things:
1. What is 25 + 17?
2. Who is the current president of India?

But you only gave the model:
add

as a tool.
Therefore the model has:
Capability available:
    add()

Capability NOT available:
    current_president_of_india()

So the model can execute the first part through your tool, but it doesn't have a tool for retrieving current information.
This is a very important agentic-AI principle:
The LLM can only use capabilities that are actually available to it.

7. Why didn't it simply answer the president question?
Because you specifically asked it to use tools, and the available tool set was:
model_with_tools = model.bind_tools([    add])


The model knows:
I have an add tool.

It does not have:
get_current_president()

or:
web_search()

So it cannot perform a reliable live lookup through your tool set.
Depending on the model/provider and prompt, it might still answer from its internal knowledge, but that would not be a live/current lookup.
This distinction will become extremely important when we build MCP systems.
8. additional_kwargs
You have this:
additional_kwargs={    'function_call': {        'name': 'add',        'arguments': '{"a": 25, "b": 17}'    },    ...}


This is provider/integration-level information.
Notice that it contains essentially the same information:
name = "add"arguments = '{"a": 25, "b": 17}'


But don't use additional_kwargs["function_call"] as your primary application interface.
Prefer:
response.tool_calls


because LangChain gives you a standardized representation.
Think:
Provider-specific representation
        ↓
additional_kwargs

LangChain normalized representation
        ↓
response.tool_calls

That's one of the reasons frameworks like LangChain are useful.
9. The huge thought_signatures
You saw:
__gemini_function_call_thought_signatures__

with a massive encoded string.
Don't panic. 😂
This is Gemini-specific provider metadata associated with its tool/function-calling behavior.
You generally shouldn't:
parse this


or:
modify this


or:
build your state around this


For our agent implementation, focus on:
response.tool_calls


The framework/provider handles the underlying details.
10. response_metadata
You have:
response_metadata={    'finish_reason': 'STOP',    'model_name': 'gemini-3.5-flash',    'safety_ratings': [],    'model_provider': 'google_genai'}


This tells you things about the model invocation.
For example:
response.response_metadata["model_name"]


gives:
gemini-3.5-flash

and:
response.response_metadata["model_provider"]


gives:
google_genai

This is useful for logging/debugging, but it isn't the agent's main decision mechanism.
11. usage_metadata
You have:
usage_metadata={    'input_tokens': 74,    'output_tokens': 153,    'total_tokens': 227,    ...}


This is useful for:
- token usage
- cost estimation
- performance monitoring
- debugging
- production observability
And notice:
output_tokens = 153
reasoning = 135

The provider is reporting token accounting details.
Again, not part of the tool loop itself.
12. Now let's execute the tool ourselves
This is the next step.
You already have:
tool_call = response.tool_calls[0]


So:
tool_call["name"]


→
add

and:
tool_call["args"]


→
{'a': 25, 'b': 17}


Now:
result = add.invoke(tool_call["args"])


should give:
42

At this point:
LLM said:
"Call add(25,17)"

Runtime:
"Okay."

Runtime executes:
add(25,17)

Result:
42

13. Now we need the ToolMessage
Import:
from langchain.messages import ToolMessage


Then:
tool_message = ToolMessage(    content=str(result),    tool_call_id=tool_call["id"])


Notice:
tool_call_id=tool_call["id"]


which is:
call_3689347

This ID is important.
We're effectively saying:
"This result belongs to the specific tool call the model made earlier."

So:
AIMessage
   │
   └── call_3689347
            │
            ▼
       ToolMessage
            │
            └── call_3689347

14. Now comes the critical part
You need to send both the AI's tool-call message and the ToolMessage back to the model.
For example:
from langchain.messages import HumanMessagemessages = [    HumanMessage(        content="What is 25 + 17? and tell me who is the current president of India?"    ),    response,    tool_message]


Then:
final_response = model_with_tools.invoke(messages)


Now the model gets:
Human:
What is 25 + 17? and tell me who is the current president of India?

AI:
Call add(a=25,b=17)

Tool:
42

15. Here's the key agent-loop decision
Now inspect:
final_response.tool_calls


If:
[]


then:
No more tools required
        ↓
Final answer
        ↓
END

If instead:
[    {        ...    }]


then:
Another tool is required
        ↓
Execute it
        ↓
ToolMessage
        ↓
LLM again

This is the agent loop.
16. Your next experiment should be even better
Let's add a second tool:
@tooldef multiply(a: int, b: int) -> int:    """Multiply two integers together."""    return a * b


Then:
tools = [add, multiply]model_with_tools = model.bind_tools(tools)


Ask:
"Calculate 25 + 17 and then multiply the result by 2."

Now you should observe:
Human
  ↓
AIMessage
  └── add(25,17)
  ↓
ToolMessage
  └── 42
  ↓
AIMessage
  └── multiply(42,2)
  ↓
ToolMessage
  └── 84
  ↓
AIMessage
  └── final answer

This is exactly the multi-step agent loop we learned conceptually.
17. One subtle point: tool execution is NOT automatic yet
This is probably the most important thing to understand from today's experiment.
You did:
response = model_with_tools.invoke(...)


and got:
tool_calls=[...]

But LangChain did not automatically execute your Python function just because you used:
bind_tools()


You still need:
result = add.invoke(...)


unless you use a higher-level agent/runtime abstraction such as LangGraph's ToolNode or an agent executor.
So:
bind_tools()

means:
Give the LLM knowledge of the tools and allow it to request them.

It does not mean:
Run the tools automatically.

That distinction is fundamental.
18. Your current architecture
You've now actually implemented:
                    User
                     │
                     ▼
              ┌─────────────┐
              │    LLM      │
              │ + tool      │
              │   schemas   │
              └──────┬──────┘
                     │
                     ▼
                 AIMessage
                     │
                tool_calls
                     │
                     ▼
              ┌─────────────┐
              │   Runtime   │
              └──────┬──────┘
                     │
                     ▼
              add.invoke(...)
                     │
                     ▼
                    42
                     │
                     ▼
               ToolMessage
                     │
                     ▼
                    LLM
                     │
              ┌──────┴──────┐
              │             │
        tool_calls=[]    tool_calls
              │             │
              ▼             ▼
             END       execute again

And this is exactly the point where LangGraph becomes useful.
Your next task
Before moving to LangGraph, run this exact experiment:
@tooldef add(a: int, b: int) -> int:    """Add two integers together."""    return a + b@tooldef multiply(a: int, b: int) -> int:    """Multiply two integers together."""    return a * b


Bind both tools and ask:
Calculate 25 + 17 and then multiply the result by 2.

Then show me the output of:
print(response)print(response.tool_calls)


especially after the first tool result is returned.
We'll trace the actual AIMessage → ToolMessage → AIMessage → ToolMessage → final AIMessage sequence from your Gemini model, and then we'll turn that exact loop into a LangGraph StateGraph + ToolNode