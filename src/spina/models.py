"""Domain models for spina. All models are frozen (immutable) Pydantic models."""

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class TocEntry(BaseModel, frozen=True):
    title: str
    level: int = Field(ge=0)
    page: int = Field(ge=0)


class BookMetadata(BaseModel, frozen=True):
    title: str = Field(min_length=1)
    author: str
    source_filename: str
    page_count: int = Field(gt=0)
    toc: tuple[TocEntry, ...] = ()


class DownloadLink(BaseModel, frozen=True):
    label: str
    filename: str


class Chapter(BaseModel, frozen=True):
    title: str
    content: str
    images: tuple[str, ...] = ()
    order: int = Field(ge=0)


class IntermediateBook(BaseModel, frozen=True):
    metadata: BookMetadata
    chapters: tuple[Chapter, ...]

    @field_validator("chapters")
    @classmethod
    def chapters_not_empty(cls, v: tuple[Chapter, ...]) -> tuple[Chapter, ...]:
        if len(v) == 0:
            raise ValueError("At least one chapter is required")
        return v
    image_dir: Path | None = None
