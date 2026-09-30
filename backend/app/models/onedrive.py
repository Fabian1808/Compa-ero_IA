from sqlalchemy import String, DateTime, Text, ForeignKey, Index, func, Boolean, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.database import Base


class OneDriveFile(Base):
    __tablename__ = "onedrive_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), default="file", nullable=False)  # file, folder
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("onedrive_files.id"), nullable=True, index=True)
    path: Mapped[str | None] = mapped_column(Text, nullable=True)
    web_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    download_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified_by_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    last_modified_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    is_processed: Mapped[bool] = mapped_column(default=False, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at_local: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    account: Mapped["Account"] = relationship()
    parent: Mapped["OneDriveFile | None"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["OneDriveFile"]] = relationship(back_populates="parent", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_onedrive_files_account_parent", "account_id", "parent_id"),
        Index("ix_onedrive_files_graph_id", "graph_id", unique=True),
        Index("ix_onedrive_files_last_modified", "last_modified_at"),
    )


class OneDriveDeltaLink(Base):
    __tablename__ = "onedrive_delta_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    drive_id: Mapped[str] = mapped_column(String(255), nullable=False)
    delta_link: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_onedrive_delta_account_drive", "account_id", "drive_id", unique=True),
    )