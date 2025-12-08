from abc import ABC, abstractmethod

import openai
from google import genai
import anthropic
import xai_sdk
from xai_sdk import chat as xai_chat


class LLMClient(ABC):
    def __init__(self, model: str, max_tokens: int, temperature: float):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.name = "LLM"

    def system_prompt(self) -> str:
        return (
            f"You are a highly intelligent, helpful assistant. "
            f"Provide a concise answer under {int(float(self.max_tokens) * 0.75)} words."
        )

    @abstractmethod
    def get_reply(self, system_prompt: str, user_prompt: str, history: list[tuple[str, str]]):
        ...


class GeminiClient(LLMClient):
    def __init__(self, model: str, max_tokens: int, temperature: float, key: str | None):
        super().__init__(model, max_tokens, temperature)
        self.name = "Gemini"
        self.api = genai.Client(api_key=key) if key else None

    def get_reply(self, system_prompt: str, user_prompt: str, history: list[tuple[str, str]]):
        parts: list[str] = []

        if system_prompt:
            parts.append(f"[SYSTEM]\n{system_prompt}\n")

        for user_msg, assistant_msg in history:
            parts.append(f"User: {user_msg}\n")
            parts.append(f"Assistant: {assistant_msg}\n")
        parts.append(f"User: {user_prompt}\nAssistant:")

        full_prompt = "\n".join(parts)

        # use the sync API, *not* the aio version
        resp = self.api.models.generate_content(  # type: ignore[union-attr]
            model=self.model,
            contents=full_prompt,
        )
        return resp.text


class GPTClient(LLMClient):
    def __init__(self, model: str, max_tokens: int, temperature: float, key: str | None):
        super().__init__(model, max_tokens, temperature)
        self.name = "ChatGPT"
        self.api = openai.OpenAI(api_key=key) if key else None

    def get_reply(self, system_prompt: str, user_prompt: str, history: list[tuple[str, str]]):
        messages = [{"role": "system", "content": system_prompt}]
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        messages.append({"role": "user", "content": user_prompt})

        completion = self.api.chat.completions.create(  # type: ignore[union-attr]
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return completion.choices[0].message.content


class ClaudeClient(LLMClient):
    def __init__(self, model: str, max_tokens: int, temperature: float, key: str | None):
        super().__init__(model, max_tokens, temperature)
        self.name = "Claude"
        self.api = anthropic.Anthropic(api_key=key) if key else None

    def get_reply(self, system_prompt: str, user_prompt: str, history: list[tuple[str, str]]):
        messages: list[dict] = []
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        messages.append({"role": "user", "content": user_prompt})

        resp = self.api.messages.create(  # type: ignore[union-attr]
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
            system=system_prompt,
            temperature=self.temperature,
        )
        return resp.content[0].text


class GrokClient(LLMClient):
    def __init__(self, model: str, max_tokens: int, temperature: float, key: str | None):
        super().__init__(model, max_tokens, temperature)
        self.name = "Grok"
        self.api = xai_sdk.Client(api_key=key) if key else None

    def get_reply(self, system_prompt: str, user_prompt: str, history: list[tuple[str, str]]):
        chat = self.api.chat.create(  # type: ignore[union-attr]
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        chat.append(xai_chat.system(system_prompt))
        for user_msg, assistant_msg in history:
            chat.append(xai_chat.user(user_msg))
            chat.append(xai_chat.assistant(assistant_msg))
        chat.append(xai_chat.user(user_prompt))

        response = chat.sample()
        return response.content if hasattr(response, "content") else str(response)


class DeepseekClient(LLMClient):
    def __init__(self, model: str, max_tokens: int, temperature: float, key: str | None):
        super().__init__(model, max_tokens, temperature)
        self.name = "Deepseek"
        self.api = openai.OpenAI(
            api_key=key,
            base_url="https://api.deepseek.com",
        ) if key else None

    def get_reply(self, system_prompt: str, user_prompt: str, history: list[tuple[str, str]]):
        messages = [{"role": "system", "content": system_prompt}]
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        messages.append({"role": "user", "content": user_prompt})

        resp = self.api.chat.completions.create(  # type: ignore[union-attr]
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False,
        )
        return resp.choices[0].message.content
