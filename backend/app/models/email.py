from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey, Index, func, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False)
    thread_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("email_threads.id"), nullable=True, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipients_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    importance: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    categories_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    account: Mapped["Account"] = relationship(back_populates="emails")
    thread: Mapped["EmailThread"] = relationship(back_populates="emails")
    tasks: Mapped[list["Task"]] = relationship(back_populates="source_email")

    __table_args__ = (
        Index("ix_emails_account_received", "account_id", "received_at"),
        Index("ix_emails_graph_id", "graph_id", unique=True),
    )


class EmailThread(Base):
    __tablename__ = "email_threads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_thread_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    participants_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    account: Mapped["Account"] = relationship(back_populates="email_threads")
    emails: Mapped[list["Email"]] = relationship(back_populates="thread")

    __table_args__ = (
        Index("ix_email_threads_graph_id", "graph_thread_id", unique=True),
    )