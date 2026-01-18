import json
from typing import Any


class LLMManager:
    def __init__(
        self,
        api_key: str,
        model: str,
        api_base: str | None = None,
        temperature: float = 0.2,
        timeout: float | None = None,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The openai package is required to use the internal LLM. "
                "Install it with: python -m pip install openai"
            ) from exc

        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if api_base:
            client_kwargs["base_url"] = api_base
        if timeout is not None:
            client_kwargs["timeout"] = timeout

        self._client = OpenAI(**client_kwargs)
        self._model = model
        self._temperature = temperature

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> Any:
        request: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
        }
        if tools is not None:
            request["tools"] = tools
        return self._client.chat.completions.create(**request)

    def extract_message(self, response: Any) -> Any:
        return response.choices[0].message

    @staticmethod
    def parse_json(text: str) -> dict[str, Any]:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or start >= end:
                raise ValueError("LLM response did not contain valid JSON.")
            return json.loads(text[start : end + 1])
