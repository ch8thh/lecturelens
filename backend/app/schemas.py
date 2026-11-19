"""All shared Pydantic models. Person B imports these too - do not change field names."""
from typing import Literal

from pydantic import BaseModel, Field


class Concept(BaseModel):
    name: str
    definition: str
    importance: Literal["high", "medium", "low"]


class ImageAnalysisResult(BaseModel):
    title: str
    summary: str
    key_concepts: list[Concept]
    visible_text: str
    diagram_description: str


class AudioAnalysisResult(BaseModel):  # built by Person B's /api/... audio route
    title: str
    summary: str
    key_concepts: list[Concept]
    transcript: str


class NotesSection(BaseModel):
    heading: str
    content: str


class SynthesisRequest(BaseModel):
    image_results: list[ImageAnalysisResult] = Field(default_factory=list)
    audio_result: AudioAnalysisResult | None = None
    extra_notes: str = ""


class SynthesisResult(BaseModel):
    title: str
    summary: str
    key_takeaways: list[str]
    key_concepts: list[Concept]
    notes_sections: list[NotesSection]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatContext(BaseModel):
    summary: str
    transcript: str = ""
    notes: str = ""


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)
    context: ChatContext


class ChatResponse(BaseModel):
    reply: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
