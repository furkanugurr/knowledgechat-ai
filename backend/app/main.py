"""FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.embedding.ollama_embedding import OllamaEmbeddingProvider
from app.prompt.prompt_builder import PromptBuilder
from app.providers.ollama_provider import OllamaProvider
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.vectorstore.chroma_provider import ChromaVectorStoreProvider

logger = logging.getLogger(__name__)


def create_lifespan(
    settings: Settings,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """Create the application lifespan for managed service resources."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        prompt_builder = PromptBuilder.from_defaults()
        provider = OllamaProvider(
            host=settings.ollama_host,
            model=settings.chat_model,
            timeout=settings.request_timeout,
        )
        embedding_provider = OllamaEmbeddingProvider(
            host=settings.ollama_host,
            model=settings.embedding_model,
            timeout=settings.request_timeout,
        )
        await provider.start()
        await embedding_provider.start()
        application.state.llm_provider = provider
        application.state.prompt_builder = prompt_builder
        application.state.embedding_service = EmbeddingService(
            embedding_provider
        )
        application.state.vector_store_service = VectorStoreService(
            ChromaVectorStoreProvider(
                persistence_path=settings.vector_db_path,
                collection_name=settings.vector_collection_name,
            )
        )
        try:
            yield
        finally:
            await embedding_provider.close()
            await provider.close()

    return lifespan


def create_application(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    application_settings = settings or get_settings()
    configure_logging(application_settings.log_level)

    application = FastAPI(
        title=application_settings.app_name,
        version=application_settings.app_version,
        lifespan=create_lifespan(application_settings),
    )
    application.state.settings = application_settings
    application.include_router(api_router)

    logger.info(
        "Application configured",
        extra={"app_env": application_settings.app_env},
    )
    return application


app = create_application()
