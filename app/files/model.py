from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class FileEntry(Base):
    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint("type IN ('file', 'folder')", name="ck_files_type"),
        UniqueConstraint("project_id", "id", name="uq_files_project_id_id"),
        UniqueConstraint(
            "project_id",
            "parent_id",
            "name",
            name="uq_files_sibling_name",
            postgresql_nulls_not_distinct=True,
        ),
        ForeignKeyConstraint(
            ["project_id", "parent_id"],
            ["files.project_id", "files.id"],
            name="fk_files_parent_in_project",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[UUID | None] = mapped_column(Uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[Literal["file", "folder"]] = mapped_column(Text, nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
