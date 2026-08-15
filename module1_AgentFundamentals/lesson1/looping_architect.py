# while True:

#     response = llm(messages, tools)

#     if response.has_tool_call():

#         tool_name = response.tool_name
#         arguments = response.arguments

#         result = tools[tool_name](**arguments)

#         messages.append(response)
#         messages.append(result)

#     else:
#         return response

