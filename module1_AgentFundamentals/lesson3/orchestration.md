1. First, forget LangChain

Imagine we have this normal Python function:

def get_weather(city: str, days: int):
    return {
        "city": city,
        "temperature": 30,
        "raining": True
    }

Python knows this function exists.

But the LLM doesn't automatically know it exists.

We need to expose it.

2. Create the tool schema ourselves

Let's manually describe it:

weather_tool = {
    "name": "get_weather",
    "description": "Get the weather forecast for a city.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "Name of the city"
            },
            "days": {
                "type": "integer",
                "description": "Number of forecast days"
            }
        },
        "required": ["city", "days"]
    }
}

Now we have two separate things:

Python implementation
        │
        │
        ▼
get_weather()

and:

Tool schema
        │
        │
        ▼
"name": get_weather
"description": ...
"parameters": ...

This distinction is very important.

3. Why do we need both?

Because:

LLM needs
Schema

It needs to know:

"What tools are available and how can I request them?"

Runtime needs
Implementation

It needs to know:

"When the model requests get_weather, what actual Python code should I execute?"

So:

              Tool
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
    Schema          Implementation
       │                │
       ▼                ▼
      LLM             Runtime
4. Now imagine sending tools to the LLM

Conceptually we send:

tools = [
    weather_tool
]

along with the user message:

"What is the weather in Chennai tomorrow?"

The model sees something conceptually like:

Available tools:


get_weather
Description:
Get the weather forecast for a city.


Parameters:
city: string
days: integer


User:
What is the weather in Chennai tomorrow?
5. The LLM generates a tool call

Instead of generating:

"The weather in Chennai is..."

it can produce:

{
    "tool_calls": [
        {
            "id": "call_001",
            "name": "get_weather",
            "arguments": {
                "city": "Chennai",
                "days": 1
            }
        }
    ]
}

Notice something important.

This is not the tool result.

It is a request to execute the tool.

6. Think of the LLM as a planner

At this stage:

LLM
 │
 │ "I need this capability"
 ▼
Tool Call

The LLM hasn't executed anything.

The runtime now takes over.

7. Build the tool registry

Our runtime needs to know:

Which tool name maps to which Python function?

We can create:

tool_registry = {
    "get_weather": get_weather
}

Now:

tool_registry["get_weather"]

returns:

get_weather

So when we receive:

{
    "name": "get_weather",
    "arguments": {
        "city": "Chennai",
        "days": 1
    }
}

we can do:

tool_name = "get_weather"


tool = tool_registry[tool_name]


result = tool(
    city="Chennai",
    days=1
)

And get:

{
    "city": "Chennai",
    "temperature": 30,
    "raining": True
}
8. This is the first major piece of runtime logic

Conceptually:

def execute_tool(tool_call):


    name = tool_call["name"]
    arguments = tool_call["arguments"]


    tool = tool_registry[name]


    result = tool(**arguments)


    return result

This tiny function is incredibly important.

It performs:

Tool call
   ↓
Find implementation
   ↓
Extract arguments
   ↓
Execute function
   ↓
Return result
9. Now we need to send the result back

The LLM originally said:

{
    "name": "get_weather",
    "arguments": {
        "city": "Chennai",
        "days": 1
    }
}

Runtime executes it:

get_weather("Chennai", 1)

Result:

{
    "city": "Chennai",
    "temperature": 30,
    "raining": true
}

Now we create a tool result message.

Conceptually:

{
    "role": "tool",
    "tool_call_id": "call_001",
    "content": {
        "city": "Chennai",
        "temperature": 30,
        "raining": true
    }
}

And send it back to the LLM.

10. Now the LLM sees the complete conversation

The model effectively sees:

Human:
What is the weather in Chennai tomorrow?


AI:
I want to call get_weather(city="Chennai", days=1)


Tool:
{
    "city": "Chennai",
    "temperature": 30,
    "raining": true
}

Now the LLM can answer:

"The forecast for Chennai tomorrow is 30°C with rain.
Carry an umbrella."
11. We have built an agent!

Our flow is now:

                 USER
                   │
                   ▼
                 LLM
                   │
             tool call
                   │
                   ▼
             TOOL RUNTIME
                   │
                   ▼
                Python
                Tool
                   │
                 result
                   │
                   ▼
                  LLM
                   │
             final answer
                   │
                   ▼
                  END

That's the basic architecture.

12. But we haven't handled multiple steps

Let's make it more interesting.

Tools:

def get_weather(city: str, days: int):
    ...


def recommend_clothing(temperature: float, raining: bool):
    ...

User:

"What's the weather tomorrow and what should I wear?"

Now the LLM might do:

LLM
 ↓
get_weather()
 ↓
Tool result
 ↓
LLM
 ↓
recommend_clothing()
 ↓
Tool result
 ↓
LLM
 ↓
Final answer

So we need a loop.

13. The agent loop from scratch

Conceptually:

while True:


    response = llm(messages, tools)


    if response.has_tool_calls():


        for tool_call in response.tool_calls:


            result = execute_tool(tool_call)


            messages.append(response)


            messages.append(
                create_tool_message(
                    tool_call,
                    result
                )
            )


    else:


        return response

This is the heart of the system.

Let's understand every line conceptually.

14. llm(messages, tools)

We send the model:

Conversation
+
Available tools

For example:

messages:
    Human
    AI
    Tool
    AI
    Tool


tools:
    get_weather
    recommend_clothing

The LLM then determines the next action.

15. response.has_tool_calls()

We need to determine:

Did the model ask for a tool?

If yes:

continue agent loop

If no:

the model produced a final response

So:

                 LLM
                  │
             tool calls?
              /       \
            YES        NO
             │          │
             ▼          ▼
          execute      END
           tools

This is our first conditional edge.

And guess what?

This exact concept will become important in LangGraph.

16. Execute tool

Suppose:

{
    "name": "get_weather",
    "arguments": {
        "city": "Chennai",
        "days": 1
    }
}

Runtime:

result = execute_tool(tool_call)

returns:

{
    "temperature": 30,
    "raining": True
}
17. Update messages

We then add:

AI tool call

and:

Tool result

to our conversation state.

So:

messages = [


    Human:
    "What's the weather?",


    AI:
    tool_call(get_weather),


    Tool:
    temperature=30, raining=True
]

Now when we call the LLM again, it has the history.

18. Second LLM invocation

The LLM now sees:

Human:
What's the weather tomorrow and what should I wear?


AI:
Call get_weather()


Tool:
temperature=30
raining=true

Available:

recommend_clothing()

The model decides:

{
    "name": "recommend_clothing",
    "arguments": {
        "temperature": 30,
        "raining": true
    }
}

Runtime executes it.

19. Final invocation

Tool returns:

"Light clothes and an umbrella."

Now messages contain:

Human
AI → get_weather
Tool → weather
AI → recommend_clothing
Tool → recommendation

The LLM receives this.

This time it doesn't need a tool.

It responds:

"Tomorrow in Chennai will be around 30°C with rain.
I'd recommend light clothing and carrying an umbrella."

has_tool_calls() is false.

Therefore:

END
20. This is the complete loop

Memorize this:

                ┌─────────────┐
                │    USER     │
                └──────┬──────┘
                       ↓
                ┌─────────────┐
                │     LLM     │
                └──────┬──────┘
                       ↓
                 Tool calls?
                  /       \
                YES        NO
                 │          │
                 ↓          ↓
            Execute tool   END
                 │
                 ↓
            Tool result
                 │
                 ↓
          Update messages
                 │
                 ↓
                LLM
                 │
                 └──────→ repeat

That is an agent loop.

21. Now let's connect this to LangChain

What we manually built:

Tool schema
Tool registry
Tool execution
Messages
Tool calls
Loop

LangChain provides abstractions for these.

For example:

from langchain.tools import tool


@tool
def get_weather(city: str, days: int):
    """Get the weather forecast for a city."""
    ...

LangChain handles much of the schema construction.

Then:

model_with_tools = model.bind_tools([
    get_weather
])

Now the model knows:

get_weather exists

But remember:

bind_tools() doesn't by itself create the full agent loop.

It mainly makes the tool definitions available to the model.

22. LangGraph enters here

Our manual loop:

while True:


    response = llm(...)


    if response.has_tool_calls():
        execute_tool()
    else:
        break

can be represented as a graph:

              ┌─────────┐
              │  START  │
              └────┬────┘
                   ↓
              ┌─────────┐
              │   LLM   │
              └────┬────┘
                   ↓
             Tool calls?
              /       \
            YES        NO
             │          │
             ↓          ↓
         ┌───────┐     END
         │ Tools │
         └───┬───┘
             │
             ↓
            LLM
             │
             └──────────→ ...

This is exactly the kind of graph LangGraph allows us to construct.

23. Why LangGraph instead of just a while loop?

Because real agents become much more complicated.

For example:

                    START
                      │
                      ▼
                     LLM
                  /   |   \
                 /    |    \
                ▼     ▼     ▼
            Search   SQL   API
                │     │     │
                └──┬──┴─────┘
                   ▼
                  LLM
                 /   \
                ▼     ▼
             Human   Tool
              │        │
              ▼        ▼
             END      LLM

You may need:

branching
loops
retries
parallel execution
human approval
checkpoints
persistence
failure handling
conditional routing

A simple while loop becomes difficult to maintain.

That's where LangGraph's state + nodes + edges become powerful.

24. The mapping you should remember

This is probably the most important table of this lesson:

Our manual system	LangGraph concept
Python state dictionary	State
LLM function	Node
Tool execution	ToolNode
if tool_call	Conditional edge
while loop	Graph cycle
End condition	END
Messages	State/messages
Tool registry	Tools
Tool result	ToolMessage

So LangGraph isn't inventing agentic AI.

It gives us a formal execution graph around the agent loop.

25. And now MCP

This is where everything starts connecting.

Our local tool:

Python
 └── get_weather()

can eventually become an MCP tool:

MCP Server
 └── get_weather()

Then:

                  LLM
                   │
              tool call
                   ↓
              LangGraph
                   │
              MCP Client
                   │
                   ↓
              MCP Server
                   │
                   ↓
            get_weather()
                   │
                   ↓
                result
                   │
                   ↓
                  LLM

The agent loop remains fundamentally the same.

Only the tool transport/execution layer changes.

26. One important architectural distinction

Don't think:

MCP = Agent

They are different things.

Think:

Agent
│
├── LLM
├── State
├── Decision loop
└── Tools
      │
      ├── Local Python tool
      ├── REST API
      ├── Database
      ├── MCP tool
      └── Other capability

MCP is primarily a standardized protocol for exposing and consuming capabilities/tools.

We'll go much deeper into this later.

27. Your architecture after Lesson 3

You should now be able to explain:

User
 ↓
LLM
 ↓
LLM selects tool based on context + available tool schemas
 ↓
Structured tool call
 ↓
Agent runtime
 ↓
Tool implementation
 ↓
Tool result
 ↓
State/messages updated
 ↓
LLM
 ↓
Another tool OR final answer
 ↓
END

And the framework mapping:

Manual implementation
        ↓
      LangChain
        ↓
      LangGraph
        ↓
        MCP

But these are not replacements for each other.

They solve different layers.

28. Your challenge before we move on

Let's test whether you've really internalized Lesson 3.

We have three tools:

def get_user(user_id: int):
    """Get basic information about a user."""


def get_orders(user_id: int):
    """Get the user's recent orders."""


def get_order_status(order_id: int):
    """Get the current shipping status of an order."""

User asks:

"Find my latest order and tell me whether it has been delivered."

Don't write code.

Trace the actual messages and execution:

1. HumanMessage
2. AIMessage → ?
3. ToolMessage → ?
4. AIMessage → ?
5. ToolMessage → ?
6. AIMessage → final
7. END

And answer these:

A. What tool should the LLM call first?

B. What arguments should it generate?

C. What does the runtime do with the tool call?

D. What information does the tool return?

E. What does the LLM need to know before it can call get_order_status()?

F. What causes the agent to terminate?

Once you get this right, Lesson 4 will be our first actual LangChain implementation, where we'll create @tool, bind it to a model, inspect the tool-call object, and then build the loop ourselves before using LangGraph.