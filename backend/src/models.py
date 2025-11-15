"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Optional


class Source(BaseModel):
    """Citation source with breadcrumb and snippet."""
    breadcrumb: str = Field(..., description="Breadcrumb path like 'Modules > Week_02 > Policy Memo Rubric'")
    url: Optional[str] = Field(None, description="Optional Canvas URL")
    snippet: str = Field(..., description="Relevant excerpt from the document")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str = Field(..., description="User's question about course materials", min_length=1)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str = Field(..., description="Generated answer from RAG")
    sources: List[Source] = Field(..., description="List of 2-3 citation sources", min_items=0, max_items=3)
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")


class Document(BaseModel):
    """Internal document model for ingestion."""
    text: str
    breadcrumb: str
    source_file: str
    file_type: str
    metadata: Optional[dict] = None


class Chunk(BaseModel):
    """Chunk model for indexing."""
    text: str
    breadcrumb: str
    source_file: str
    chunk_id: int
    start_char: int
    end_char: int

