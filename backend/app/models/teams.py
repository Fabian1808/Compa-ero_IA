from sqlalchemy import String, DateTime, Text, ForeignKey, Index, func, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class TeamsChat(Base):
    __tablename__ = "teams_chats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(500), nullable=True)
    chat_type: Mapped[str] = mapped_column(String(50), default="oneOnOne", nullable=False)
    members_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    account: Mapped["Account"] = relationship()
    messages: Mapped[list["TeamsMessage"]] = relationship(back_populates="chat", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_teams_chats_graph_id", "graph_id", unique=True),
    )


class TeamsMessage(Base):
    __tablename__ = "teams_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    chat_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams_chats.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    message_type: Mapped[str] = mapped_column(String(50), default="message", nullable=False)
    attachments_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    mentions_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_processed: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    account: Mapped["Account"] = relationship()
    chat: Mapped["TeamsChat"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_teams_messages_chat_sent", "chat_id", "sent_at"),
        Index("ix_teams_messages_graph_id", "graph_id", unique=True),
    )


class TeamsChannel(Base):
    __tablename__ = "teams_channels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    account: Mapped["Account"] = relationship()

    __table_args__ = (
        Index("ix_teams_channels_team_graph", "team_id", "graph_id", unique=True),
    )