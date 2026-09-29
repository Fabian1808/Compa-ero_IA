import ollama
import json
from typing import AsyncIterator
from app.ai.provider import AIProvider, ChatMessage, ChatCompletion, EmbeddingResponse, AIProviderConfig
from app.config import settings


class OllamaProvider(AIProvider):
    def __init__(self, config: AIProviderConfig | None = None):
        if config:
            self._config = config
        else:
            self._config = AIProviderConfig(
                provider="ollama",
                base_url=settings.ollama_base_url,
                chat_model=settings.ollama_chat_model,
                embed_model=settings.ollama_embed_model,
            )
        self._client = ollama.AsyncClient(host=self._config.base_url)

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def supports_tools(self) -> bool:
        return True

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> ChatCompletion:
        # Convert to Ollama format
        ollama_messages = [
            {"role": m.role, "content": m.content or ""}
            for m in messages
        ]

        ollama_tools = None
        if tools:
            ollama_tools = [{"type": "function", "function": t["function"]} for t in tools]

        response = await self._client.chat(
            model=self._config.chat_model,
            messages=ollama_messages,
            tools=ollama_tools,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        )

        message = response["message"]
        tool_calls = None
        if message.get("tool_calls"):
            tool_calls = [
                {
                    "id": tc["function"]["name"],
                    "type": "function",
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": json.dumps(tc["function"]["arguments"])
                    }
                }
                for tc in message["tool_calls"]
            ]

        return ChatCompletion(
            message=ChatMessage(
                role=message["role"],
                content=message.get("content"),
                tool_calls=tool_calls,
            ),
            finish_reason="tool_calls" if tool_calls else "stop",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        )

    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AsyncIterator[ChatCompletion]:
        ollama_messages = [
            {"role": m.role, "content": m.content or ""}
            for m in messages
        ]

        ollama_tools = None
        if tools:
            ollama_tools = [{"type": "function", "function": t["function"]} for t in tools]

        stream = await self._client.chat(
            model=self._config.chat_model,
            messages=ollama_messages,
            tools=ollama_tools,
            options={"temperature": kwargs.get("temperature", 0.1), "num_predict": kwargs.get("max_tokens", 2048)},
            stream=True
        )

        accumulated_content = ""
        async for chunk in stream:
            message = chunk["message"]
            content = message.get("content", "")
            accumulated_content += content

            tool_calls = None
            if message.get("tool_calls"):
                tool_calls = [
                    {
                        "id": tc["function"]["name"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": json.dumps(tc["function"]["arguments"])
                        }
                    }
                    for tc in message["tool_calls"]
                ]

            yield ChatCompletion(
                message=ChatMessage(
                    role=message["role"],
                    content=accumulated_content if content else None,
                    tool_calls=tool_calls,
                ),
                finish_reason="tool_calls" if tool_calls else ("stop" if chunk.get("done") else "streaming"),
                usage=None
            )

    async def create_embeddings(self, texts: list[str]) -> EmbeddingResponse:
        response = await self._client.embed(
            model=self._config.embed_model,
            input=texts
        )

        return EmbeddingResponse(
            embeddings=response["embeddings"],
            usage={"prompt_tokens": 0, "total_tokens": 0}
        )

    async def health_check(self) -> bool:
        try:
            models = await self._client.list()
            model_names = [m["name"] for m in models.get("models", [])]
            return self._config.chat_model in model_names
        except Exception:
            return False