"""End-to-end chat turn: retrieve, generate, validate, persist."""

import uuid

from sqlalchemy.orm import Session

from app.assistant.agent import build_openai_client, run_document_agent
from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer
from app.database.chats import add_citations, add_message, ensure_profile, get_thread, update_thread_title
from app.grounding.validator import GroundingValidator
from app.retrieval.retriever import DocumentRetriever


class ChatOrchestrator:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._retriever = DocumentRetriever(session, build_openai_client())
        self._validator = GroundingValidator()

    async def run_turn(
        self,
        user_id: str,
        email: str | None,
        thread_id: str,
        user_text: str,
    ) -> GroundedAnswer:
        ensure_profile(self._session, user_id, email)
        thread = get_thread(self._session, thread_id, user_id)
        if thread is None:
            raise LookupError("thread_not_found")

        retrieval = await self._retriever.retrieve(user_text)
        deps = DocumentAgentDeps(
            user_id=user_id,
            thread_id=thread_id,
            retriever=self._retriever,
            grounding_validator=self._validator,
        )
        answer = await run_document_agent(deps, user_text, retrieval.passages)

        add_message(self._session, thread_id, "user", user_text)
        assistant_message = add_message(self._session, thread_id, "assistant", answer.answer)
        add_citations(
            self._session,
            str(assistant_message.id),
            [
                {
                    "chunk_id": citation.chunk_id,
                    "excerpt": citation.excerpt,
                    "metadata": citation.metadata,
                }
                for citation in answer.citations
            ],
        )

        if thread.title == "New chat" and user_text:
            update_thread_title(self._session, thread, user_text[:80])

        return answer

    async def run_turn_streaming(
        self,
        user_id: str,
        email: str | None,
        thread_id: str,
        user_text: str,
    ) -> GroundedAnswer:
        # Streaming endpoint still completes the full turn before emitting deltas.
        return await self.run_turn(user_id, email, thread_id, user_text)
