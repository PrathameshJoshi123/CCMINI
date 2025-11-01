from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ProcessingStatusEnum(str, Enum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ContentTypeEnum(str, Enum):
    SUMMARY = "SUMMARY"
    MINDMAP = "MINDMAP"
    FLASHCARDS = "FLASHCARDS"


class TextChunk(BaseModel):
    text: str
    page_number: int
    source: str  # one of TextSourceEnum values: 'TEXT', 'OCR', 'TABLE'


class TextSourceEnum(str, Enum):
    TEXT = "TEXT"
    OCR = "OCR"
    TABLE = "TABLE"


class DocumentInDB(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    original_filename: str
    # New primary storage key for S3. Optional for backward compatibility.
    s3_key: Optional[str] = None
    # Keep local_path optional to support older records that haven't been migrated yet.
    local_path: Optional[str] = None
    processing_status: ProcessingStatusEnum
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        validate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class GeneratedContentInDB(BaseModel):
    id: str = Field(..., alias="_id")
    document_id: str
    user_id: str
    content_type: ContentTypeEnum
    content_data: dict
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        validate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# Structured output models for LLM-generated content
class Summary(BaseModel):
    summary: str


class MindMapNode(BaseModel):
    topic: str
    children: list["MindMapNode"] = []


class Flashcard(BaseModel):
    term: str
    definition: str


class FlashcardList(BaseModel):
    flashcards: list[Flashcard]

