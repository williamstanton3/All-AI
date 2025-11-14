from __future__ import annotations
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
from google import genai
from xai_sdk import Client
from anthropic import Anthropic
from hashing_examples import UpdatedHasher

db = SQLAlchemy()
gpt_client = None
gemini_client = None
grok_client = None
claude_client = None
deepseek_client = None
pwd_hasher = None

def init_extensions(openai_key: str, gemini_key: str, grok_key: str, claude_key: str, deepseek_key: str, pepper: bytes, flask_app: Flask) -> None:
    global gpt_client, gemini_client, grok_client, claude_client, deepseek_client, pwd_hasher
    if openai_key:
        gpt_client = OpenAI(api_key=openai_key)

    # gemini_key argument takes precedence, fall back to env var
    if gemini_key:
        gemini_client = genai.Client(api_key=gemini_key)

    if grok_key:
        grok_client = Client(api_key=grok_key)

    if claude_key:
        claude_client = Anthropic(api_key=claude_key)

    if deepseek_key:
        deepseek_client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")

    pwd_hasher = UpdatedHasher(pepper)
    db.init_app(flask_app)