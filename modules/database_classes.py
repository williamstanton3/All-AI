from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from flask_login import UserMixin
import modules.extensions as extensions
from datetime import datetime

db = extensions.db

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
    user_input: Mapped[str] = mapped_column(db.Text, nullable=False)
    model_name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    model_response: Mapped[str] = mapped_column(db.Text, nullable=False)
    date_saved: Mapped[datetime] = mapped_column(default=datetime.now(), nullable=False)

    thread: Mapped[ChatThread] = db.relationship(back_populates='messages')  # type: ignore