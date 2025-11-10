import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langchain.agents import create_agent
import asyncio
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

async def main():
    tools = await client.get_tools()
    print("Done")
    agent = create_agent(model, tools)
    print(tools)
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "How long till sunrise in Delhi?"}]}
    )
    print(response["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())
