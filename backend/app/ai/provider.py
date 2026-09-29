from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from pydantic import BaseModel
from dataclasses import dataclass


class ChatMessage(BaseModel):
    role: str
    content: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


class ChatCompletion(BaseModel):
    message: ChatMessage
    finish_reason: str
    usage: dict | None = None


class EmbeddingResponse(BaseModel):
    embeddings: list[list[float]]
    usage: dict | None = None


class AIProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def supports_tools(self) -> bool:
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[ChatMessage],
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> ChatCompletion:
        pass

    @abstractmethod
    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AsyncIterator[ChatCompletion]:
        pass

    @abstractmethod
    async def create_embeddings(self, texts: list[str]) -> EmbeddingResponse:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass


@dataclass
class AIProviderConfig:
    provider: str
    base_url: str
    chat_model: str
    embed_model: str