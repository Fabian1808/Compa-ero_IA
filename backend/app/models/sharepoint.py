from sqlalchemy import String, DateTime, Text, ForeignKey, Index, func, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class SharePointSite(Base):
    __tablename__ = "sharepoint_sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(500), nullable=False)
    web_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    site_type: Mapped[str] = mapped_column(String(50), default="teamSite", nullable=False)  # teamSite, communicationSite, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    account: Mapped["Account"] = relationship()
    lists: Mapped[list["SharePointList"]] = relationship(back_populates="site", cascade="all, delete-orphan")
    drives: Mapped[list["SharePointDrive"]] = relationship(back_populates="site", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sharepoint_sites_graph_id", "graph_id", unique=True),
    )


class SharePointDrive(Base):
    __tablename__ = "sharepoint_drives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sharepoint_sites.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    drive_type: Mapped[str] = mapped_column(String(50), default="documentLibrary", nullable=False)
    web_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    account: Mapped["Account"] = relationship()
    site: Mapped["SharePointSite"] = relationship(back_populates="drives")
    items: Mapped[list["SharePointItem"]] = relationship(back_populates="drive", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sharepoint_drives_graph_id", "graph_id", unique=True),
    )


class SharePointList(Base):
    __tablename__ = "sharepoint_lists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sharepoint_sites.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    list_template: Mapped[str | None] = mapped_column(String(50), nullable=True)  # genericList, documentLibrary, etc.
    web_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    account: Mapped["Account"] = relationship()
    site: Mapped["SharePointSite"] = relationship(back_populates="lists")
    items: Mapped[list["SharePointListItem"]] = relationship(back_populates="list", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sharepoint_lists_graph_id", "graph_id", unique=True),
    )


class SharePointListItem(Base):
    __tablename__ = "sharepoint_list_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    list_id: Mapped[str] = mapped_column(String(36), ForeignKey("sharepoint_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    fields_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)  # Dynamic columns
    web_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_modified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    is_processed: Mapped[bool] = mapped_column(default=False, nullable=False)

    account: Mapped["Account"] = relationship()
    list: Mapped["SharePointList"] = relationship(back_populates="items")

    __table_args__ = (
        Index("ix_sharepoint_list_items_list_modified", "list_id", "last_modified_at"),
        Index("ix_sharepoint_list_items_graph_id", "graph_id", unique=True),
    )


class SharePointItem(Base):
    __tablename__ = "sharepoint_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    drive_id: Mapped[str] = mapped_column(String(36), ForeignKey("sharepoint_drives.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), default="file", nullable=False)  # file, folder
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sharepoint_items.id"), nullable=True, index=True)
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
    drive: Mapped["SharePointDrive"] = relationship(back_populates="items")
    parent: Mapped["SharePointItem | None"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["SharePointItem"]] = relationship(back_populates="parent", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sharepoint_items_drive_parent", "drive_id", "parent_id"),
        Index("ix_sharepoint_items_graph_id", "graph_id", unique=True),
        Index("ix_sharepoint_items_last_modified", "last_modified_at"),
    )


class SharePointDeltaLink(Base):
    __tablename__ = "sharepoint_delta_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # site, drive, list
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    delta_link: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_sp_delta_account_resource", "account_id", "resource_type", "resource_id", unique=True),
    )