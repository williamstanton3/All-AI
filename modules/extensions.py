from __future__ import annotations
from typing import Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
from hashing_examples import UpdatedHasher

db = SQLAlchemy()
client: Optional[OpenAI] = None
pwd_hasher: Optional[UpdatedHasher] = None

def init_extensions(openai_key: Optional[str], pepper: bytes, flask_app: Flask) -> None:
    """
    Initialize extension instances that require the Flask app or runtime secrets.
    Call this from `app.py` after creating `app` and setting config.
    """
    global client, pwd_hasher
    if openai_key:
        client = OpenAI(api_key=openai_key)
    pwd_hasher = UpdatedHasher(pepper)
    db.init_app(flask_app)
