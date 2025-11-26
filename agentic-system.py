from fastapi import FastAPI, HTTPException, Query
from typing import Literal
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
import requests
from langchain.agents import create_agent
from langchain_core.messages import convert_to_messages
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from configparser import ConfigParser
from langgraph_supervisor import create_supervisor
from langchain.chat_models import init_chat_model
import os

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

config = ConfigParser()
config.read("config.ini")

base_url = "http://localhost:8000"


def call_tool_api(tool_name, a, b):
    url = f"{base_url}/tool/{tool_name}"
    payload = {"a": a, "b": b}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(
            f"API call failed with status {response.status_code}: {response.text}")


def tool1(a, b):
    """Add two numbers."""
    return call_tool_api("tool1", a, b)


def tool2(a, b):
    """Add two numbers, use this only if tool 1 isn't available."""
    return call_tool_api("tool2", a, b)


def tool3(a, b):
    """Multiply two numbers."""
    return call_tool_api("tool3", a, b)


def tool4(a, b):
    """Multiply two, use this only if tool 1 isn't available."""
    return call_tool_api("tool4", a, b)


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


def get_tools(tools):
    agent1_tools = config.get(
        'agents', 'agent1_tools', fallback='').split(', ')
    agent2_tools = config.get(
        'agents', 'agent2_tools', fallback='').split(', ')
    agent3_tools = config.get(
        'agents', 'agent3_tools', fallback='').split(', ')

    tools1 = [t for t in tools if t.__name__ in agent1_tools]
    tools2 = [t for t in tools if t.__name__ in agent2_tools]
    tools3 = [t for t in tools if t.__name__ in agent3_tools]
    return [tools1, tools2, tools3]


tools = get_tools([tool1, tool2, tool3, tool4])
agent1_enabled = config.getboolean('agents', 'agent1_enabled', fallback=False)
agent2_enabled = config.getboolean('agents', 'agent2_enabled', fallback=False)
agent3_enabled = config.getboolean('agents', 'agent3_enabled', fallback=False)
agent1_tools = tools[0]
agent2_tools = tools[1]
agent3_tools = tools[2]
# print(tools)
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
            "You are a math agent that can add using the tools provided. Use the tools provided and just provide the output without checking if tools aren't there.\n\n"
            "INSTRUCTIONS:\n"
            # "- After you're done with your tasks, respond to the supervisor directly\n"
            # "- Do not do any work yourself, JUST USE THE TOOLS. IF THE ANSWER IS WRONG, RETURN THE WRONG ANSWER.\n"
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


class AgentMessage(BaseModel):
    role: str
    content: str


class AgentRequest(BaseModel):
    messages: list[AgentMessage]


class Message(BaseModel):
    message: str


app = FastAPI()


@app.put("/tool/{name}", responses={404: {"model": Message}})
def call_tool(
    name: Literal["add_agent", "multiply_agent", "combined_agent"],
    input: AgentRequest
):
    tool_map = {
        "add_agent": globals().get("add_agent"),
        "multiply_agent": globals().get("mulyiply_agent"),
        "combined_agent": globals().get("combined_agent"),
    }
    fn = tool_map.get(name)
    expr = input.messages[0].content
    if fn is None:
        return JSONResponse(status_code=404, content={"message": f"{name} is not enabled"})
    return {
        "tool": name,
        "result": fn.invoke({"messages": [{"role": "user", "content": expr}]})
    }
