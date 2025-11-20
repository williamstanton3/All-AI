from __future__ import annotations
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from hashing_examples import UpdatedHasher
from modules import dbms
from modules.llm_client import *

#from llms import gpt


db = dbms.db
gpt_client: GPTClient|None = None
gemini_client: GeminiClient|None = None
grok_client: GrokClient|None = None
claude_client: ClaudeClient|None = None
deepseek_client: DeepseekClient|None = None
pwd_hasher: UpdatedHasher|None = None

def init_extensions(
    claude_model: str,
    claude_key: str,
    claude_max_tokens: int,
    claude_temperature: float,

    deepseek_model: str,
    deepseek_key: str,
    deepseek_max_tokens: int,
    deepseek_temperature: float,

    gemini_model: str,
    gemini_key: str,
    gemini_max_tokens: int,
    gemini_temperature: float,

    openai_model: str,
    openai_key: str,
    openai_max_tokens: int,
    openai_temperature: float,

    grok_model: str,
    grok_key: str,
    grok_max_tokens: int,
    grok_temperature: float,

    pepper: bytes, 
    flask_app: Flask
    ) -> None:
    
    global gpt_client, gemini_client, grok_client, claude_client, deepseek_client, pwd_hasher
    
    gpt_client = GPTClient(openai_model, openai_max_tokens, openai_temperature, openai_key)
    gemini_client = GeminiClient(gemini_model, gemini_max_tokens, gemini_temperature, gemini_key)
    grok_client = GrokClient(grok_model, grok_max_tokens, grok_temperature, grok_key)
    claude_client = ClaudeClient(claude_model, claude_max_tokens, claude_temperature, claude_key)
    deepseek_client = DeepseekClient(deepseek_model, deepseek_max_tokens, deepseek_temperature, deepseek_key)
    pwd_hasher = UpdatedHasher(pepper)
    db.init_app(flask_app)