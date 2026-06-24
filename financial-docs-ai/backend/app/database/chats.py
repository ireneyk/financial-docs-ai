"""Chat thread and message persistence."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.models import ChatMessage, ChatThread, MessageCitation, Profile


def ensure_profile(session: Session, user_id: str, email: str | None) -> Profile:
    profile = session.get(Profile, uuid.UUID(user_id))
    if profile is None:
        profile = Profile(id=uuid.UUID(user_id), email=email)
        session.add(profile)
        session.flush()
    return profile


def list_threads(session: Session, user_id: str) -> list[ChatThread]:
    stmt = (
        select(ChatThread)
        .where(ChatThread.user_id == uuid.UUID(user_id))
        .order_by(ChatThread.updated_at.desc())
    )
    return list(session.scalars(stmt))


def get_thread(session: Session, thread_id: str, user_id: str) -> ChatThread | None:
    thread = session.get(ChatThread, uuid.UUID(thread_id))
    if thread is None or thread.user_id != uuid.UUID(user_id):
        return None
    return thread


def create_thread(session: Session, user_id: str, title: str = "New chat") -> ChatThread:
    thread = ChatThread(user_id=uuid.UUID(user_id), title=title)
    session.add(thread)
    session.flush()
    return thread


def update_thread_title(session: Session, thread: ChatThread, title: str) -> None:
    thread.title = title
    thread.updated_at = datetime.now(UTC)


def list_messages(session: Session, thread_id: str) -> list[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .options(joinedload(ChatMessage.citations))
        .where(ChatMessage.thread_id == uuid.UUID(thread_id))
        .order_by(ChatMessage.created_at.asc())
    )
    return list(session.scalars(stmt).unique())


def add_message(
    session: Session,
    thread_id: str,
    role: str,
    content: str,
    message_json: dict | None = None,
) -> ChatMessage:
    message = ChatMessage(
        thread_id=uuid.UUID(thread_id),
        role=role,
        content=content,
        message_json=message_json,
    )
    session.add(message)
    session.flush()
    return message


def add_citations(
    session: Session,
    message_id: str,
    citations: list[dict],
) -> list[MessageCitation]:
    rows: list[MessageCitation] = []
    for item in citations:
        row = MessageCitation(
            message_id=uuid.UUID(message_id),
            chunk_id=uuid.UUID(item["chunk_id"]),
            excerpt=item["excerpt"],
            metadata_json=item.get("metadata", {}),
        )
        session.add(row)
        rows.append(row)
    session.flush()
    return rows
