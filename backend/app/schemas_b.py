"""Pydantic models for Person B's endpoints (the shared JSON contract).

Concept and AudioAnalysisResult are intentional copies of Person A's
schemas.py versions; we will dedupe later. Keep field names identical.
"""
from typing import Literal

from pydantic import BaseModel

Difficulty = Literal["easy", "medium", "hard"]


# ---- audio ----------------------------------------------------------------
class Concept(BaseModel):
    name: str
    definition: str
    importance: Literal["high", "medium", "low"]


class AudioAnalysisResult(BaseModel):
    title: str
    summary: str
    key_concepts: list[Concept]
    transcript: str


# ---- flashcards -------------------------------------------------------------
class Flashcard(BaseModel):
    front: str
    back: str
    type: Literal["definition", "question", "application", "formula", "comparison"]


class FlashcardsRequest(BaseModel):
    source_text: str
    count: int = 10
    difficulty: Difficulty = "medium"
    concepts: list[str] = []  # Pydantic copies mutable defaults, so this is safe


class FlashcardsResult(BaseModel):
    cards: list[Flashcard]


# ---- quiz -------------------------------------------------------------------
class QuizQuestion(BaseModel):
    type: Literal["multiple_choice", "true_false", "short_answer"]
    question: str
    options: list[str] = []
    correct_answer: str
    explanation: str
    concept: str


class QuizRequest(BaseModel):
    source_text: str
    count: int = 5
    difficulty: Difficulty = "medium"
    types: list[str] = ["multiple_choice"]


class QuizResult(BaseModel):
    questions: list[QuizQuestion]


# ---- concept explainer --------------------------------------------------------
class ConceptExplainRequest(BaseModel):
    concept: str
    context: str
    style: Literal["simple", "in_depth", "analogy", "example"]


class ConceptExplainResult(BaseModel):
    concept: str
    explanation: str
    example: str
    related_concepts: list[str]
