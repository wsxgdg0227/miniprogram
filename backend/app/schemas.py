from datetime import datetime

from pydantic import BaseModel, Field


class UploadSnippetRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category: str = Field(default="cpp", min_length=1, max_length=100)
    content: str = Field(..., min_length=1)


class SnippetOut(BaseModel):
    id: int
    title: str
    category: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
