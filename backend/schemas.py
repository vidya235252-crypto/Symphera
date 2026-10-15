"""The contract. Person B's UI and Person C's llm.py both depend on this exact shape."""
from typing import Literal
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)
    language_hint: str = "auto"  # "en" | "hi" | "kn" | "auto"


class Pattern(BaseModel):
    pattern: str
    note: str


class Source(BaseModel):
    id: str
    title: str
    url: str


class AnalyzeResponse(BaseModel):
    detected_language: str
    summary: str
    possible_patterns: list[Pattern] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    urgency: Literal["routine", "soon", "urgent"] = "routine"
    suggested_specialist: str = "general physician"
    questions_for_doctor: list[str] = Field(default_factory=list)
    what_to_track: list[str] = Field(default_factory=list)
    disclaimer: str = ""
    sources: list[Source] = []  # filled in code from model-returned IDs
    fallback: bool = False
