"""Wire-format message conversion for the AI SDK client."""

from pydantic import BaseModel, Field


class ChatUIMessage(BaseModel):
    id: str
    role: str
    parts: list[dict] = Field(default_factory=list)


class StreamChatRequest(BaseModel):
    thread_id: str = Field(alias="threadId")
    messages: list[ChatUIMessage] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class CreateThreadRequest(BaseModel):
    title: str = "New chat"


class UpdateThreadRequest(BaseModel):
    title: str


def extract_user_text(messages: list[ChatUIMessage]) -> str:
    for message in reversed(messages):
        if message.role != "user":
            continue
        text_parts = [part.get("text", "") for part in message.parts if part.get("type") == "text"]
        joined = "\n".join(part for part in text_parts if part).strip()
        if joined:
            return joined
    return ""


def to_ui_message(role: str, content: str, message_id: str) -> dict:
    return {
        "id": message_id,
        "role": role,
        "parts": [{"type": "text", "text": content}],
    }
