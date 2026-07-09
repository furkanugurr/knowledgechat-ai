"""Single-turn chat endpoint."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_chat_service
from app.providers.base import (
    LLMProviderError,
    LLMProviderTimeoutError,
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import (
    ChatPromptError,
    ChatRetrievalError,
    ChatService,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a single-turn chat response",
)
async def create_chat_response(
    chat_request: ChatRequest,
    chat_service: Annotated[
        ChatService,
        Depends(get_chat_service),
    ],
) -> ChatResponse:
    """Generate one response for one validated user message."""
    logger.info(
        "Incoming chat request message_length=%d",
        len(chat_request.message),
    )

    try:
        response = await chat_service.generate_response(chat_request.message)
    except ChatRetrievalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge retrieval service unavailable.",
        ) from exc
    except ChatPromptError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to build the response prompt.",
        ) from exc
    except LLMProviderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Ollama request timed out.",
        ) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama service unavailable.",
        ) from exc

    return ChatResponse(response=response)
