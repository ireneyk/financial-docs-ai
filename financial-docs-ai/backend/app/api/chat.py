"""Chat thread routes and streaming endpoint."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.chat.messages import (
    CreateThreadRequest,
    StreamChatRequest,
    UpdateThreadRequest,
    extract_user_text,
    to_ui_message,
)
from app.chat.orchestrator import ChatOrchestrator
from app.chat.streaming import encode_data, stream_plain_text
from app.database.chats import create_thread, get_thread, list_messages, list_threads, update_thread_title
from app.database.session import get_db

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/threads")
async def get_threads(
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[dict]:
    threads = list_threads(session, user.id)
    return [
        {
            "id": str(thread.id),
            "title": thread.title,
            "createdAt": thread.created_at.isoformat(),
            "updatedAt": thread.updated_at.isoformat(),
        }
        for thread in threads
    ]


@router.post("/threads", status_code=status.HTTP_201_CREATED)
async def post_thread(
    body: CreateThreadRequest,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> dict:
    thread = create_thread(session, user.id, body.title)
    return {
        "id": str(thread.id),
        "title": thread.title,
        "createdAt": thread.created_at.isoformat(),
        "updatedAt": thread.updated_at.isoformat(),
    }


@router.patch("/threads/{thread_id}")
async def patch_thread(
    thread_id: str,
    body: UpdateThreadRequest,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> dict:
    thread = get_thread(session, thread_id, user.id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    update_thread_title(session, thread, body.title)
    return {
        "id": str(thread.id),
        "title": thread.title,
        "updatedAt": thread.updated_at.isoformat(),
    }


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: str,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[dict]:
    thread = get_thread(session, thread_id, user.id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    messages = list_messages(session, thread_id)
    payload: list[dict] = []
    for message in messages:
        ui = to_ui_message(message.role, message.content, str(message.id))
        if message.role == "assistant" and message.citations:
            ui["citations"] = [
                {
                    "chunkId": str(citation.chunk_id),
                    "excerpt": citation.excerpt,
                    "metadata": citation.metadata_json,
                }
                for citation in message.citations
            ]
        payload.append(ui)
    return payload


@router.post("/stream")
async def stream_chat(
    body: StreamChatRequest,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> StreamingResponse:
    user_text = extract_user_text(body.messages)
    if not user_text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Missing user message")

    orchestrator = ChatOrchestrator(session)

    try:
        answer = await orchestrator.run_turn_streaming(user.id, user.email, body.thread_id, user_text)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    async def event_stream():
        yield encode_data(
            {
                "type": "message-start",
                "messageId": str(uuid.uuid4()),
                "role": "assistant",
            }
        )
        async for chunk in stream_plain_text(answer.answer):
            yield chunk
        yield encode_data(
            {
                "type": "citations",
                "items": [
                    {
                        "chunkId": citation.chunk_id,
                        "label": citation.label,
                        "excerpt": citation.excerpt,
                        "metadata": citation.metadata,
                    }
                    for citation in answer.citations
                ],
            }
        )

    return StreamingResponse(event_stream(), media_type="text/plain; charset=utf-8")
