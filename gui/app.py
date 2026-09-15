import json
import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field


MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOOL_ROUNDS = 8
SYSTEM_PROMPT = (
    "You are a PowerPoint production assistant. Use the available tools to create and edit presentations. "
    "When a user asks for a presentation, execute the required tools instead of only describing steps. "
    "Keep the user informed about what you did and mention presentation IDs or saved file paths when available."
)

app = FastAPI(title="PowerPoint Studio")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)


async def mcp_request(method: str, path: str, **kwargs: Any) -> Any:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.request(method, f"{MCP_SERVER_URL}{path}", **kwargs)
        response.raise_for_status()
        return response.json()


async def get_openai_tools() -> list[dict[str, Any]]:
    payload = await mcp_request("GET", "/mcp/tools")
    tools = []
    for tool in payload.get("tools", []):
        schema = tool.get("inputSchema") or {"type": "object", "properties": {}}
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description") or "PowerPoint operation",
                    "parameters": schema,
                },
            }
        )
    return tools


def serialize_tool_result(result: Any) -> str:
    try:
        return json.dumps(result, ensure_ascii=True, default=str)
    except TypeError:
        return json.dumps({"result": str(result)}, ensure_ascii=True)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    mcp_status = "unavailable"
    try:
        await mcp_request("GET", "/health")
        mcp_status = "healthy"
    except Exception:
        pass
    return {
        "status": "healthy" if mcp_status == "healthy" else "degraded",
        "mcp": mcp_status,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "model": OPENAI_MODEL,
    }


@app.get("/api/presentations")
async def presentations() -> dict[str, Any]:
    try:
        return await mcp_request("GET", "/mcp/presentations")
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail=f"MCP server unavailable: {error}") from error


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")
    if not request.messages:
        raise HTTPException(status_code=400, detail="At least one message is required")

    try:
        tools = await get_openai_tools()
        client = AsyncOpenAI(api_key=api_key)
        conversation: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        conversation.extend(message.model_dump() for message in request.messages)
        trace: list[dict[str, Any]] = []

        for _ in range(MAX_TOOL_ROUNDS):
            completion = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=conversation,
                tools=tools,
                tool_choice="auto",
            )
            message = completion.choices[0].message
            assistant_message: dict[str, Any] = {"role": "assistant", "content": message.content or ""}
            if message.tool_calls:
                assistant_message["tool_calls"] = [tool_call.model_dump() for tool_call in message.tool_calls]
            conversation.append(assistant_message)

            if not message.tool_calls:
                return {"reply": message.content or "Done.", "trace": trace}

            for tool_call in message.tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                    result = await mcp_request(
                        "POST",
                        "/mcp/call",
                        json={"tool_name": tool_call.function.name, "arguments": arguments},
                    )
                    trace.append({"tool": tool_call.function.name, "status": result.get("status", "success")})
                    tool_content = serialize_tool_result(result)
                except (json.JSONDecodeError, httpx.HTTPError, KeyError) as error:
                    trace.append({"tool": tool_call.function.name, "status": "error"})
                    tool_content = serialize_tool_result({"status": "error", "error": str(error)})
                conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_content,
                    }
                )

        return {"reply": "The request required too many tool steps. Please try a smaller request.", "trace": trace}
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"OpenAI request failed: {error}") from error
