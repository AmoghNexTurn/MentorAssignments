from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv
from configparser import ConfigParser

load_dotenv()

mcp = FastMCP("MCP Server", host="127.0.0.1", port=8080, stateless_http=True)

config = ConfigParser()
config.read("config.ini")

tool1_enabled = config.getboolean('tools', 'tool1', fallback=True)
tool2_enabled = config.getboolean('tools', 'tool2', fallback=True)
tool3_enabled = config.getboolean('tools', 'tool3', fallback=True)
tool4_enabled = config.getboolean('tools', 'tool4', fallback=True)

if tool1_enabled:
    @mcp.tool()
    # def tool1(param1, param2) -> str:
    #     """This is tool 1"""
    #     return f"Tool 1 active param1: {param1} param2: {param2}"
    def tool1(a: float, b: float):
        """Add two numbers."""
        return a + b

if tool2_enabled:
    @mcp.tool()
    # def tool2(param1, param2) -> str:
    #     """This is tool 2"""
    #     return f"Tool 2 active param1: {param1} param2: {param2}"
    def tool2(a: float, b: float):
        """Add two numbers, use this only if tool 1 isn't available."""
        return a + b + b

if tool3_enabled:
    @mcp.tool()
    # def tool3(param1, param2) -> str:
    #     """This is tool 3"""
    #     return f"Tool 3 active param1: {param1} param2: {param2}"
    def tool3(a: float, b: float):
        """Multiply two numbers."""
        return a * b

if tool4_enabled:
    @mcp.tool()
    def tool4(param1, param2) -> str:
        """This is tool 4"""
        return f"Tool 4 active param1: {param1} param2: {param2}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
