import os
from typing import Literal

from dotenv import load_dotenv
from configparser import ConfigParser
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Literal


# Load environment variables from .env
load_dotenv()

# Read config.ini
config = ConfigParser()
config.read("config.ini")

tool1_enabled = config.getboolean("tools", "tool1", fallback=True)
tool2_enabled = config.getboolean("tools", "tool2", fallback=True)
tool3_enabled = config.getboolean("tools", "tool3", fallback=True)
tool4_enabled = config.getboolean("tools", "tool4", fallback=True)

# Define tools conditionally, same as in your snippet
if tool1_enabled:
    def tool1(a: float, b: float):
        """Add two numbers."""
        return a + b

if tool2_enabled:
    def tool2(a: float, b: float):
        """Add two numbers, use this only if tool 1 isn't available."""
        return a + b + b

if tool3_enabled:
    def tool3(a: float, b: float):
        """Multiply two numbers."""
        return a * b

if tool4_enabled:
    def tool4(a: float, b: float):
        """Multiply two, use this only if tool 1 isn't available."""
        return a * b * b

# Create FastAPI app
app = FastAPI(title="Math Tools API")


class ToolInput(BaseModel):
    a: float
    b: float


class Message(BaseModel):
    message: str


@app.post("/tool/{name}", responses={404: {"model": Message}})
def call_tool(
    name: Literal["tool1", "tool2", "tool3", "tool4"],
    input: ToolInput  # Pydantic model will parse request JSON body
):
    tool_map = {
        "tool1": globals().get("tool1"),
        "tool2": globals().get("tool2"),
        "tool3": globals().get("tool3"),
        "tool4": globals().get("tool4"),
    }
    fn = tool_map.get(name)
    if fn is None:
        return JSONResponse(status_code=404, content={"message": f"{name} is not enabled"})
    return {
        "tool": name,
        "a": input.a,
        "b": input.b,
        "result": fn(input.a, input.b)
    }
