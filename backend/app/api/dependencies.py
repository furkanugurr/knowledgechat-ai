"""FastAPI dependency providers."""

from typing import Annotated, cast

from fastapi import Depends, Request

from app.prompt.prompt_builder import PromptBuilder
from app.providers.base import LLMProvider
from app.services.chat_service import ChatService


def get_llm_provider(request: Request) -> LLMProvider:
    """Return the application-managed language model provider."""
    return cast(LLMProvider, request.app.state.llm_provider)


def get_prompt_builder(request: Request) -> PromptBuilder:
    """Return the application-managed prompt builder."""
    return cast(PromptBuilder, request.app.state.prompt_builder)


def get_chat_service(
    provider: Annotated[LLMProvider, Depends(get_llm_provider)],
    prompt_builder: Annotated[PromptBuilder, Depends(get_prompt_builder)],
) -> ChatService:
    """Create a chat service with its abstract provider dependencies."""
    return ChatService(
        provider=provider,
        prompt_builder=prompt_builder,
    )
