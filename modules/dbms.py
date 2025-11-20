from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from flask_login import UserMixin
import modules.extensions as extensions
from datetime import datetime
import base64
import lzma
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def db_encode_text(input: str) -> bytes:
    """
    Encodes text to store as binary in the database. Text over 25 bytes in size will be compressed using LZMA.
    """
    input_bytes = input.encode("utf-8")
    if len(input_bytes) > 25:
        return lzma.compress(input_bytes)
    else:
        return input_bytes

def db_decode_text(input: bytes) -> str:
    """
    Decodes text stored in the database
    """
    if len(input) > 25:
        return lzma.decompress(input).decode("utf-8")
    else:
        return input.decode("utf-8")


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False)
    pwd_hash: Mapped[bytes] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default='Free')

    threads: Mapped[list['ChatThread']] = db.relationship(back_populates='user')  # type: ignore

    @property
    def password(self):
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, pwd: str) -> None:
        if extensions.pwd_hasher is None:
            raise RuntimeError("Password hasher not initialized. Call init_extensions(...) before using models.")
        self.pwd_hash = extensions.pwd_hasher.hash(pwd)

    def verify_password(self, pwd: str) -> bool:
        if extensions.pwd_hasher is None:
            raise RuntimeError("Password hasher not initialized. Call init_extensions(...) before using models.")
        return extensions.pwd_hasher.check(pwd, self.pwd_hash)


class ChatThread(db.Model):
    __tablename__ = 'chat_threads'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), nullable=False)
    thread_name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    date_created: Mapped[datetime] = mapped_column(default=datetime.now(), nullable=False)

    user: Mapped[User] = db.relationship(back_populates='threads')  # type: ignore
    messages: Mapped[list['ChatHistory']] = db.relationship(
        back_populates='thread',
        cascade="all, delete-orphan",
        order_by='ChatHistory.id'
    )  # type: ignore


class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(db.ForeignKey('chat_threads.id'), nullable=False)
    
    # User prompt
    _user_input: Mapped[bytes] = mapped_column("user_input", db.BLOB, nullable=False)
    @property
    def user_input(self): return db_decode_text(self._user_input)
    @user_input.setter
    def user_input(self, value: str): self._user_input = db_encode_text(value)

    # Model name
    model_name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    
    # Model response 
    _model_response: Mapped[bytes] = mapped_column("model_response", db.BLOB, nullable=False)
    @property 
    def model_response(self): return db_decode_text(self._model_response)
    @model_response.setter
    def model_response(self, value: str): self._model_response = db_encode_text(value)
    
    # Date of response
    date_saved: Mapped[datetime] = mapped_column(default=datetime.now(), nullable=False)

    # Associated thread
    thread: Mapped[ChatThread] = db.relationship(back_populates='messages')  # type: ignore


def get_history_entries(thread_id):
    history_entries = ChatHistory.query.filter_by(thread_id=thread_id).order_by(ChatHistory.id.desc()).limit(2).all()
    history_entries.reverse()
    return history_entries