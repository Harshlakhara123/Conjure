from datetime import datetime
from uuid import UUID

from sqlalchemy import TIMESTAMP, ForeignKey, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(
            Uuid,
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        )
    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    owner_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )