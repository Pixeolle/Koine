import json

from uuid import uuid4

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from backend.infrastructure.api.dependencies import get_agent_provider
from backend.domain.agents.agent_provider import AgentProvider
from backend.domain.agents.assisant import Assistant
from backend.domain.enums.output_language import OutputLanguage

chat_router = APIRouter()

_chat_sessions: dict[str, Assistant] = {}

@chat_router.websocket("")
async def chat(
        websocket: WebSocket,
        documentation_id: str,
        agent_provider: AgentProvider = Depends(get_agent_provider)
) -> None:
    await websocket.accept()
    session_id = str(uuid4())
    agent = agent_provider.get_assistant(documentation_id)
    _chat_sessions[session_id] = agent

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            async for chunk in agent.respond(payload["message"], OutputLanguage(payload["output_language"])):
                await websocket.send_json({"type": "chunk", "content": chunk})
            await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        pass
    finally:
        _chat_sessions.pop(session_id)