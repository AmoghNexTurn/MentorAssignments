from flask import Flask, jsonify, request
from flask_cors import CORS
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
import asyncio
import os
from dotenv import load_dotenv
from flask_apscheduler import APScheduler

scheduler = APScheduler()

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

model = llm = ChatGroq(
  model="openai/gpt-oss-120b",
  groq_api_key=GROQ_API_KEY,
  temperature=0

)

server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
)

async def run_agent(prompt):
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model, tools)
            agent_response = await agent.ainvoke({"messages": prompt+"\nGive all table like responses in table-like output."})
            print(agent_response)
            return agent_response["messages"][-1].content
        
app = Flask(__name__)
CORS(app)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    print(data)
    if not data:
        return jsonify({"error": "No JSON data received"}), 400
    response = asyncio.run(run_agent(str(data)))
    print(response)
    return jsonify(response)

def bid_accept():
    with app.app_context():
        asyncio.run(run_agent("Run the hourly bid accept function"))

if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()

    # scheduler.add_job(
    #     id='hourly_bid_job',
    #     func=bid_accept,
    #     trigger='cron',
    #     second=0  # Runs at the 0th minute of every hour
    # )
    app.run(debug=True)
