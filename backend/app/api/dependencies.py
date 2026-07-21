"""FastAPI dependency providers."""

from typing import Annotated, cast

from fastapi import Depends, Request

from app.core.config import Settings
from app.prompt.prompt_builder import PromptBuilder
from app.providers.base import LLMProvider
from app.services.chat_service import ChatService
from app.services.retrieval_service import RetrievalService


def get_llm_provider(request: Request) -> LLMProvider:
    """Return the application-managed language model provider."""
    return cast(LLMProvider, request.app.state.llm_provider)


def get_prompt_builder(request: Request) -> PromptBuilder:
    """Return the application-managed prompt builder."""
    return cast(PromptBuilder, request.app.state.prompt_builder)


def get_retrieval_service(request: Request) -> RetrievalService:
    """Return the application-managed retrieval service."""
    return cast(RetrievalService, request.app.state.retrieval_service)


def get_application_settings(request: Request) -> Settings:
    """Return the application settings."""
    return cast(Settings, request.app.state.settings)


def get_chat_service(
    provider: Annotated[LLMProvider, Depends(get_llm_provider)],
    prompt_builder: Annotated[PromptBuilder, Depends(get_prompt_builder)],
    retrieval_service: Annotated[
        RetrievalService,
        Depends(get_retrieval_service),
    ],
    settings: Annotated[Settings, Depends(get_application_settings)],
) -> ChatService:
    """Create a chat service with its abstract provider dependencies."""
    return ChatService(
        provider=provider,
        prompt_builder=prompt_builder,
        retrieval_service=retrieval_service,
        retrieval_min_similarity=settings.retrieval_min_similarity,
        out_of_domain_min_similarity=settings.out_of_domain_min_similarity,
        out_of_domain_min_lexical_overlap=(
            settings.out_of_domain_min_lexical_overlap
        ),
        out_of_domain_min_guide_confidence=(
            settings.out_of_domain_min_guide_confidence
        ),
        domain_gate_enabled=True,
    )
