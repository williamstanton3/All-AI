from __future__ import annotations
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from hashing_examples import UpdatedHasher
from modules import dbms
from modules.llm_client import (
    GPTClient,
    GeminiClient,
    GrokClient,
    ClaudeClient,
    DeepseekClient,
    MistralClient,
    TogetherLlamaClient,
    TogetherQwenClient,
)

db = dbms.db

gpt_client: GPTClient | None = None
gemini_client: GeminiClient | None = None
grok_client: GrokClient | None = None
claude_client: ClaudeClient | None = None
deepseek_client: DeepseekClient | None = None
mistral_client: MistralClient | None = None
pwd_hasher: UpdatedHasher | None = None
llama_client: TogetherLlamaClient | None = None
qwen_client: TogetherQwenClient | None = None

def init_extensions(
    claude_model: str | None,
    claude_key: str | None,
    claude_max_tokens: int,
    claude_temperature: float,

    deepseek_model: str | None,
    deepseek_key: str | None,
    deepseek_max_tokens: int,
    deepseek_temperature: float,

    gemini_model: str | None,
    gemini_key: str | None,
    gemini_max_tokens: int,
    gemini_temperature: float,

    openai_model: str | None,
    openai_key: str | None,
    openai_max_tokens: int,
    openai_temperature: float,

    grok_model: str | None,
    grok_key: str | None,
    grok_max_tokens: int,
    grok_temperature: float,

    mistral_model: str | None,
    mistral_key: str | None,
    mistral_max_tokens: int,
    mistral_temperature: float,

    llama_model: str | None,
    llama_key: str | None,
    llama_max_tokens: int,
    llama_temperature: float,

    qwen_model: str | None,
    qwen_key: str | None,
    qwen_max_tokens: int,
    qwen_temperature: float,

    pepper: bytes,
    flask_app: Flask,
) -> None:
    global gpt_client, gemini_client, grok_client, claude_client
    global deepseek_client, mistral_client, pwd_hasher, llama_client, qwen_client

    gpt_client = GPTClient(openai_model or "", openai_max_tokens, openai_temperature, openai_key)
    gemini_client = GeminiClient(gemini_model or "", gemini_max_tokens, gemini_temperature, gemini_key)
    grok_client = GrokClient(grok_model or "", grok_max_tokens, grok_temperature, grok_key)
    claude_client = ClaudeClient(claude_model or "", claude_max_tokens, claude_temperature, claude_key)
    deepseek_client = DeepseekClient(deepseek_model or "", deepseek_max_tokens, deepseek_temperature, deepseek_key)
    mistral_client = MistralClient(mistral_model, mistral_max_tokens, mistral_temperature, mistral_key)
    llama_client = TogetherLlamaClient(llama_model, llama_max_tokens, llama_temperature, llama_key)
    qwen_client = TogetherQwenClient(qwen_model, qwen_max_tokens, qwen_temperature, qwen_key)

    pwd_hasher = UpdatedHasher(pepper)
    db.init_app(flask_app)