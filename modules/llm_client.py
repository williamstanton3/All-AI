from abc import ABC, abstractmethod

import xai_sdk
from xai_sdk import chat as xai_sdk_chat
import openai
from google import genai
import anthropic



class LLMClient(ABC):
    system_prompt = lambda self: f"""
You are a highly intelligent, helpful assistant. Provide a concise answer under {int(float(self.max_tokens) * 0.75)} words.
"""
    @abstractmethod
    async def get_reply(self, system_prompt: str, user_prompt: str, history: list[(str, str)]):
        pass
    


class GPTClient(LLMClient):
    def __init__(self, model, max_tokens, temperature, key):
        self.name = "ChatGPT"
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api = openai.AsyncOpenAI(api_key=key) if key else None

    async def get_reply(self, system_prompt: str, user_prompt: str, history: list[(str, str)]):
        messages = [{"role": "system", "content": system_prompt}]
        for e in history:
            messages.append({"role": "user", "content": e[0]})
            messages.append({"role": "assistant", "content": e[1]})
        messages.append({"role": "user", "content": user_prompt})

        completion = await self.api.chat.completions.create(
            model=self.model,messages = messages,temperature=self.temperature,max_tokens=self.max_tokens)
        return completion.choices[0].message.content




class GrokClient(LLMClient):
    def __init__(self, model, max_tokens, temperature, key):
        self.name = "Grok"
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api = xai_sdk.Client(api_key=key) if key else None # not using AsyncClient because it has some bugs

    async def get_reply(self, system_prompt: str, user_prompt: str, history: list[(str, str)]):
        chat = self.api.chat.create(model=self.model,max_tokens=self.max_tokens,temperature=self.temperature)
        chat.append(xai_sdk_chat.system(system_prompt))
        for h in history:
            chat.append(xai_sdk_chat.user(h[0]))
            chat.append(xai_sdk_chat.assistant(h[1]))
        chat.append(xai_sdk_chat.user(user_prompt))

        response = chat.sample()
        reply = getattr(response, "content", None) or getattr(response, "text", None) or getattr(response, "output", None) or str(response)
        return reply
    


class GeminiClient(LLMClient):
    def __init__(self, model, max_tokens, temperature, key):
        self.name = "Gemini"
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api = genai.Client(api_key=key) if key else None

    async def get_reply(self, system_prompt: str, user_prompt: str, history: list[(str, str)]): 
        resp = await self.api.aio.models.generate_content(model=self.model, contents=user_prompt)
        reply = getattr(resp, "text", None) or getattr(resp, "output", None)
        if reply is None:
            try:
                body = resp if isinstance(resp, dict) else resp.__dict__
                candidates = body.get("candidates") if isinstance(body, dict) else None
            except Exception:
                candidates = None
            if candidates:
                reply = candidates[0].get("content") or candidates[0].get("text") or candidates[0].get("output")
            else:
                reply = str(resp)
        return reply
    

class ClaudeClient(LLMClient):
    def __init__(self, model, max_tokens, temperature, key):
        self.name = "Claude"
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api = anthropic.AsyncAnthropic(api_key=key) if key else None

    async def get_reply(self, system_prompt: str, user_prompt: str, history: list[(str, str)]):
        messages = [{"role": "system", "content": system_prompt}]
        for e in history:
            messages.append({"role": "user", "content": e[0]})
            messages.append({"role": "assistant", "content": e[1]})
        messages.append({"role": "user", "content": user_prompt})
        resp = await self.api.messages.create(model=self.model, max_tokens=self.max_tokens, messages=messages)

        def _text_of(item):
            if item is None:
                return ""
            if isinstance(item, str):
                return item
            text = getattr(item, "text", None) or getattr(item, "content", None)
            if text is None and isinstance(item, dict):
                text = item.get("text") or item.get("content")
            return str(text) if text is not None else str(item)

        reply_candidate = getattr(resp, "content", None) or getattr(resp, "text", None)
        if reply_candidate is None and isinstance(resp, dict):
            reply_candidate = resp.get("content") or resp.get("text")
        if reply_candidate is None:
            reply_candidate = resp

        if isinstance(reply_candidate, list):
            parts = [_text_of(it) for it in reply_candidate]
            reply = "\n".join([p for p in parts if p]).strip()
        else:
            reply = _text_of(reply_candidate).strip()

        if not reply:
            reply = str(resp)


class DeepseekClient(LLMClient):
    def __init__(self, model, max_tokens, temperature, key):
        self.name = "Deepseek"
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api = openai.AsyncOpenAI(api_key=key, base_url="https://api.deepseek.com") if key else None


    async def get_reply(self, system_prompt: str, user_prompt: str, history: list[(str, str)]):
        messages = [{"role": "system", "content": system_prompt}]
        for e in history:
            messages.append({"role": "user", "content": e[0]})
            messages.append({"role": "assistant", "content": e[1]})
        messages.append({"role": "user", "content": user_prompt})

        resp = await self.api.chat.completions.create(
            model = self.model,
            messages = messages,
            stream=False
        )
        reply = None
        try:
            choices = getattr(resp, "choices", None)
            if choices and len(choices) > 0:
                msg = getattr(choices[0], "message", None)
                reply = getattr(msg, "content", None) if msg is not None else None
        except Exception:
            reply = None

        if reply is None:
            reply = getattr(resp, "content", None) or getattr(resp, "text", None)
        if reply is None:
            try:
                # attempt dict access if SDK returned a dict-like response
                if isinstance(resp, dict):
                    if "choices" in resp and resp["choices"]:
                        c = resp["choices"][0]
                        reply = (c.get("message") or {}).get("content") or c.get("text")
            except Exception:
                pass
        if reply is None:
            reply = str(resp)
        return reply
