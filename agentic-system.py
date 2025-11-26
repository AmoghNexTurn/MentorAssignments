from pydantic import BaseModel, ValidationError
from flask import Flask, request, jsonify
import os
import asyncio
from langchain.agents import create_agent
from langchain_core.messages import convert_to_messages
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from configparser import ConfigParser
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph_supervisor import create_supervisor
from langchain.chat_models import init_chat_model

# Load config file
config = ConfigParser()
config.read('config.ini')


load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")


def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return

    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    print(indented)


def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        # skip parent graph updates in the printouts
        if len(ns) == 0:
            return

        graph_id = ns[-1].split(":")[0]
        print(f"Update from subgraph {graph_id}:")
        print("\n")
        is_subgraph = True

    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        if is_subgraph:
            update_label = "\t" + update_label

        print(update_label)
        print("\n")

        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]

        for m in messages:
            pretty_print_message(m, indent=is_subgraph)
        print("\n")


client = MultiServerMCPClient({
    "All Tool Server": {
        "url": "http://127.0.0.1:8080/mcp",
        "transport": "streamable_http",
    }
})


async def get_tools():
    tools = await client.get_tools()
    agent1_tools = config.get(
        'agents', 'agent1_tools', fallback='').split(', ')
    agent2_tools = config.get(
        'agents', 'agent2_tools', fallback='').split(', ')
    agent3_tools = config.get(
        'agents', 'agent3_tools', fallback='').split(', ')

    tools1 = [t for t in tools if getattr(t, 'name', None) in agent1_tools]
    tools2 = [t for t in tools if getattr(t, 'name', None) in agent2_tools]
    tools3 = [t for t in tools if getattr(t, 'name', None) in agent3_tools]
    return tools1, tools2, tools3

tools = asyncio.run(get_tools())
# print(tools)
agent1_enabled = config.getboolean('agents', 'agent1_enabled', fallback=False)
agent2_enabled = config.getboolean('agents', 'agent2_enabled', fallback=False)
agent3_enabled = config.getboolean('agents', 'agent3_enabled', fallback=False)
agent1_tools = tools[0]
agent2_tools = tools[1]
agent3_tools = tools[2]

agents = []

if agent1_enabled:
    add_agent = create_agent(
        model=ChatGroq(
            model="qwen/qwen3-32b",
            temperature=0,
            api_key=groq_api_key  # pyright: ignore[reportArgumentType]
        ),
        tools=agent1_tools,
        system_prompt=(
            "You are a math agent that can add using the tools provided. Use the tools provided and just provide the output without checking.\n\n"
            "INSTRUCTIONS:\n"
            "- After you're done with your tasks, respond to the supervisor directly\n"
            "- Do not do any work yourself, JUST USE THE TOOLS. IF THE ANSWER IS WRONG, RETURN THE WRONG ANSWER.\n"
            "- Respond ONLY with the results of your work, do NOT include ANY other text."
        ),
        name="add_agent",
    )
    agents.append(add_agent)

if agent2_enabled:
    multiply_agent = create_agent(
        model=ChatGroq(
            model="qwen/qwen3-32b",
            temperature=0,
            api_key=groq_api_key  # pyright: ignore[reportArgumentType]
        ),
        tools=agent2_tools,
        system_prompt=(
            "You are a math agent that can multiply using the tools provided. Use the tools provided and just provide the output without checking.\n\n"
            "INSTRUCTIONS:\n"
            "- After you're done with your tasks, respond to the supervisor directly\n"
            "- Do not do any work yourself, JUST USE THE TOOLS. IF THE ANSWER IS WRONG, RETURN THE WRONG ANSWER.\n"
            "- Respond ONLY with the results of your work, do NOT include ANY other text."
        ),
        name="multiply_agent",
    )
    agents.append(multiply_agent)

if agent3_enabled:
    combined_agent = create_agent(
        model=ChatGroq(
            model="qwen/qwen3-32b",
            temperature=0,
            api_key=groq_api_key  # pyright: ignore[reportArgumentType]
        ),
        tools=agent3_tools,
        system_prompt=(
            "You are a math agent that can do some operations using the tools provided. Use the tools provided just provide the output without checking.\n\n"
            "INSTRUCTIONS:\n"
            "- After you're done with your tasks, respond to the supervisor directly\n"
            "- Do not do any work yourself, JUST USE THE TOOLS. IF THE ANSWER IS WRONG, RETURN THE WRONG ANSWER.\n"
            "- Respond ONLY with the results of your work, do NOT include ANY other text."
        ),
        name="combined_agent",
    )
    agents.append(combined_agent)

supervisor = create_supervisor(
    model=init_chat_model(model="qwen/qwen3-32b", model_provider="groq"),
    agents=agents,
    prompt=(
        "You are a supervisor managing upto 3 agents depending on availability:\n"
        "- an add agent. Assign addition tasks to this agent\n"
        "- a multiply agent. Assign multiplication tasks to this agent\n"
        "- a combined agent. Assign any tasks to this agent\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself, and create a simple workflow. IF THE ANSWER IS WRONG, RETURN THE WRONG ANSWER."
    ),
    add_handoff_back_messages=True,
    output_mode="full_history",
).compile()


async def invoke_tool_async(agent, input_data):
    results = []
    async for chunk in agent.astream({"messages": input_data}):
        pretty_print_messages(chunk)
        results.append(chunk)
    return results


async def invoke_supervisor_async(agent, input_data):
    last_chunk = None
    async for chunk in agent.astream({"messages": input_data}):
        pretty_print_messages(chunk, last_message=True)
        last_chunk = chunk
    return last_chunk


async def main():
    # single agent testing
    # results = await invoke_tool_async(add_agent, [{"role": "user", "content": "7+8"}])
    # supervisor agent testing
    final_chunk = await invoke_supervisor_async(supervisor, [
        {"role": "user", "content": "What is (4+3)*8 ?"}
    ])
    flag = 0
    if final_chunk:
        final_message_history = final_chunk["supervisor"]["messages"]
        # You can now use final_message_history as needed
        if flag:
            print(final_message_history)

# asyncio.run(main())


app = Flask(__name__)

# Define Pydantic model assuming messages input follows LangChain chat format


class Message(BaseModel):
    role: str
    content: str


class AgentRequest(BaseModel):
    messages: list[Message]

# Utility to run async agent calls synchronously in Flask


def run_agent_async(agent, messages):
    return asyncio.run(invoke_tool_async(agent, messages))


@app.route('/add_agent', methods=['POST'])
def call_add_agent():
    """
    Add Agent endpoint
    ---
    tags:
      - Agent Operations
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              messages:
                type: array
                items:
                  type: object
                  properties:
                    role:
                      type: string
                      example: user
                    content:
                      type: string
                      example: "2+3"
    responses:
      200:
        description: Result from add_agent
        content:
          application/json:
            schema:
              type: string
              example: "5"
      400:
        description: Validation error
    """
    try:
        data = AgentRequest.parse_obj(request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400

    results = run_agent_async(add_agent, [msg.dict() for msg in data.messages])
    # Process the results as needed to form response (simplified here)
    return jsonify(results[-1]['model']['messages'][0].content)


@app.route('/multiply_agent', methods=['POST'])
def call_multiply_agent():
    """
    Multiply Agent endpoint
    ---
    tags:
      - Agent Operations
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              messages:
                type: array
                items:
                  type: object
                  properties:
                    role:
                      type: string
                      example: user
                    content:
                      type: string
                      example: "2*3"
    responses:
      200:
        description: Result from multiply_agent
        content:
          application/json:
            schema:
              type: string
              example: "6"
      400:
        description: Validation error
    """
    try:
        data = AgentRequest.parse_obj(request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400

    results = run_agent_async(
        multiply_agent, [msg.dict() for msg in data.messages])
    return jsonify(results[-1]['model']['messages'][0].content)


@app.route('/combined_agent', methods=['POST'])
def call_combined_agent():
    """
    Combined Agent endpoint
    ---
    tags:
      - Agent Operations
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              messages:
                type: array
                items:
                  type: object
                  properties:
                    role:
                      type: string
                      example: user
                    content:
                      type: string
                      example: "some operation"
    responses:
      200:
        description: Result from combined_agent
        content:
          application/json:
            schema:
              type: string
              example: "result"
      400:
        description: Validation error
    """
    try:
        data = AgentRequest.parse_obj(request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400

    results = run_agent_async(
        combined_agent, [msg.dict() for msg in data.messages])
    print(results)
    return jsonify(results[-1]['model']['messages'][0].content)


if __name__ == "__main__":
    app.run(port=5000)
