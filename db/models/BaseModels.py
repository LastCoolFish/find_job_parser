from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey


class Base(DeclarativeBase):
    """Base model for all tables used to fetch metadata."""
    __abstract__ = True


class IdMixin:
    """A model for uniformly adding an `id` field to models."""
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)

class BaseModel(Base, IdMixin):
    __abstract__ = True

class SkillAssociationModel(Base):
    """Base for pure association tables linking some entity to SkillModel."""

    __abstract__ = True

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT", onupdate="CASCADE"),
        primary_key=True,
    )
