from flask import Flask, request, jsonify
import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langchain.agents import create_agent
import langchain_mcp_tools as lmt

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
github_pat = os.getenv("GITHUB_PAT")
notion_key = os.getenv("NOTION_KEY")
slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
slack_team_id = os.getenv("SLACK_TEAM_ID")

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2,
    groq_api_key=groq_api_key,
    streaming=True
)

# Set up servers
SERVER_CONFIGS = {
    "slack": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env": {
            "SLACK_BOT_TOKEN": slack_bot_token,
            "SLACK_TEAM_ID": slack_team_id
        },
        "transport": "stdio"
    },
    "github": {
        "url": "https://api.githubcopilot.com/mcp/",
        "headers": {
            "Authorization": f"Bearer {github_pat}"
        },
        "transport": "streamable_http"
    },
    "mcp-server-time": {
        "command": "python",
        "args": ["-m", "mcp_server_time"],
        "transport": "stdio"
    },
}

client = MultiServerMCPClient(SERVER_CONFIGS)

# Create Flask app
app = Flask(__name__)

# Initialize tools and agent asynchronously once
async def initialize_agent():
    tools = await client.get_tools()
    agent = create_agent(model, tools)
    return agent

agent_instance = asyncio.run(initialize_agent())

# Utility for async Flask route execution
def run_async(coro):
    return asyncio.run(coro)

# GITHUB ROUTE
@app.route("/github", methods=["POST"])
def github_tools():
    data = request.json
    action = data.get("action")
    repo = data.get("repo")
    prompt = None

    if action == "create_repo":
        prompt = f"Create repository {repo} if it doesn't exist."
    elif action == "issues":
        prompt = f"Show open issues for repository {repo}."
    else:
        return jsonify({"error": "Invalid action"}), 400

    async def process():
        response = await agent_instance.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        return response["messages"][-1].content

    content = run_async(process())
    return jsonify({"response": content})


# SLACK ROUTE
@app.route("/slack", methods=["POST"])
def slack_tools():
    data = request.json
    action = data.get("action")

    if action == "send_message":
        message = data.get("message")
        prompt = f"Send the following message to Slack: {message}"
    elif action == "read_users":
        prompt = "List all Slack users in the current workspace."
    else:
        return jsonify({"error": "Unsupported Slack action"}), 400

    async def process():
        response = await agent_instance.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        return response["messages"][-1].content

    content = run_async(process())
    return jsonify({"response": content})


# TIME ROUTE
@app.route("/time", methods=["POST"])
def time_tools():
    data = request.json
    action = data.get("action")
    location = data.get("location")

    if not location:
        return jsonify({"error": "Missing location"}), 400

    if action == "current_time":
        prompt = f"What is the current time in {location}?"
    elif action == "sunrise_or_sunset":
        prompt = f"How long until the next sunrise or sunset in {location}?"
    else:
        return jsonify({"error": "Invalid action"}), 400

    async def process():
        response = await agent_instance.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        return response["messages"][-1].content

    content = run_async(process())
    return jsonify({"response": content})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
