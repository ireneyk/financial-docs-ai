"""PydanticAI agent for grounded answers."""

from pathlib import Path

from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer
from app.config import settings
from app.retrieval.queries import SourcePassage

_INSTRUCTIONS = Path(__file__).with_name("instructions.md").read_text(encoding="utf-8")

_provider = OpenAIProvider(api_key=settings.openai_api_key)
_model = OpenAIChatModel(settings.openai_chat_model, provider=_provider)
document_agent = Agent(_model, deps_type=DocumentAgentDeps, output_type=GroundedAnswer, system_prompt=_INSTRUCTIONS)


def format_passages(passages: list[SourcePassage]) -> str:
    blocks: list[str] = []
    for index, passage in enumerate(passages, start=1):
        header = (
            f"[{index}] {passage.ticker} {passage.form_type} "
            f"({passage.filing_date}) chunk {passage.chunk_index}"
        )
        blocks.append(f"{header}\n{passage.text}")
    return "\n\n".join(blocks)


async def run_document_agent(
    deps: DocumentAgentDeps,
    user_message: str,
    passages: list[SourcePassage],
) -> GroundedAnswer:
    context = format_passages(passages)
    prompt = (
        f"User question:\n{user_message}\n\n"
        f"Retrieved passages:\n{context}\n\n"
        "Respond with a grounded answer and citations."
    )

    result = await document_agent.run(prompt, deps=deps)
    answer = result.output

    # Inline [n] markers become structured citations when the model skips the list.
    if not answer.citations:
        answer.citations = deps.grounding_validator.extract_inline_citations(answer.answer, passages)

    return deps.grounding_validator.validate(answer, passages)


def build_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.openai_api_key)
