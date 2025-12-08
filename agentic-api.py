from fastapi import FastAPI, HTTPException, Query
from typing import Literal
from pydantic import BaseModel, Field, Json
from fastapi.responses import JSONResponse
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

# Create FastAPI app
app = FastAPI(title="Agent API", description="Agent API")


class ToolInput(BaseModel):
    a: float
    b: float


class DBQuery(BaseModel):
    parameter: str
    value: str


class DBQueryMultiple(BaseModel):
    parameter1: str
    value1: str
    parameter2: str
    value2: str


class AgentMessage(BaseModel):
    role: str
    content: str


class AgentRequest(BaseModel):
    messages: list[AgentMessage]


class Message(BaseModel):
    message: str


def call_tool_api(name, parameter, value):
    url = f"{base_url}/api/single/{name}"
    payload = {"parameter": parameter, "value": value}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(
            f"API call failed with status {response.status_code}: {response.text}")


def call_tool_api_multiple(name, parameter1, value1, parameter2, value2):
    url = f"{base_url}/api/multiple/{name}"
    payload = {
        "parameter1": parameter1,
        "value1": value1,
        "parameter2": parameter2,
        "value2": value2
    }
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(
            f"API call failed with status {response.status_code}: {response.text}")


def indexed(parameter: str, value: str):
    """Get info from indexed table"""
    return call_tool_api("indexed", parameter, value)


def non_indexed(parameter: str, value: str):
    """Get info from the non-indexed table"""
    return call_tool_api("non_indexed", parameter, value)


def indexed_multiple(parameter1: str, value1: str, parameter2: str, value2: str):
    """Get info from indexed table with multiple parameters"""
    return call_tool_api_multiple("indexed", parameter1, value1, parameter2, value2)


def non_indexed_multiple(parameter1: str, value1: str, parameter2: str, value2: str):
    """Get info from the non-indexed table with multiple parameters"""
    return call_tool_api_multiple("non_indexed", parameter1, value1, parameter2, value2)


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


indexed_agent = create_agent(
    model=ChatGroq(
        model="qwen/qwen3-32b",
        temperature=0,
        api_key=groq_api_key  # pyright: ignore[reportArgumentType]
    ),
    tools=[indexed, indexed_multiple],
    system_prompt=(
        "You are a database assistant agent that can query an indexed table using the tools provided."
        "INSTRUCTIONS:\n"
        "- Use the indexed_multiple tool for queries with multiple conditions.\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
        '''
        Response format if data is found:
        The data for [parameter] [value] from the table is (There can be multiple of these if there are multiple outputs):

        ID: 
        User ID: 
        Value: 
        Hash: 
        Query Time: 

        Response format if no data is found:
        No data in table
        '''
    ),
    name="indexed_agent",
)

non_indexed_agent = create_agent(
    model=ChatGroq(
        model="qwen/qwen3-32b",
        temperature=0,
        api_key=groq_api_key  # pyright: ignore[reportArgumentType]
    ),
    tools=[non_indexed, non_indexed_multiple],
    system_prompt=(
        "You are a database assistant agent that can query a non-indexed table using the tools provided."
        "INSTRUCTIONS:\n"
        "- Use the non_indexed_multiple tool for queries with multiple conditions.\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
        '''
        Response format if data is found:
        The data for [parameter] [value] from the table is (There can be multiple of these if there are multiple outputs):

        ID: 
        User ID: 
        Value: 
        Hash: 
        Query Time: 

        Response format if no data is found:
        No data in table
        '''
    ),
    name="non_indexed_agent",
)

agent_list = []
agent_list.append(indexed_agent)
agent_list.append(non_indexed_agent)

supervisor = create_supervisor(
    model=init_chat_model(model="qwen/qwen3-32b", model_provider="groq"),
    agents=agent_list,
    prompt=(
        "You are a supervisor agent that manages multiple database assistant agents."
        "Based on the user's query, you will decide which agent to delegate the task to."
        "INSTRUCTIONS:\n"
        "- Analyze the user's query to determine whether it can be answered using the indexed database or requires querying the non-indexed database.\n"
        "- Delegate the task to the appropriate agent by invoking it with the user's query.\n"
        "- Once the agent provides a response, relay that response back to the user without any additional commentary."
    ),
    add_handoff_back_messages=True,
    output_mode="full_history",
).compile()


@app.post("/agent/{name}", responses={404: {"model": Message}}, tags=["Agent API"])
def call_agent(
    name: Literal["indexed_agent", "non_indexed_agent"],
    input: AgentRequest
):
    agent_map = {
        "indexed_agent": indexed_agent,
        "non_indexed_agent": non_indexed_agent,
    }
    fn = agent_map.get(name)
    expr = input.messages[0].content
    if fn is None:
        return JSONResponse(status_code=404, content={"message": f"{name} is not enabled"})
    return fn.invoke({"messages": [{"role": "user", "content": expr}]})["messages"][-1].content
