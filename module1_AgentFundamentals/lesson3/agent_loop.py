

# while True:

#     response = llm(messages, tools)

#     if response.has_tool_calls():

#         for tool_call in response.tool_calls:

#             result = execute_tool(tool_call)

#             messages.append(response)

#             messages.append(
#                 create_tool_message(
#                     tool_call,
#                     result
#                 )
#             )

#     else:

#         return response