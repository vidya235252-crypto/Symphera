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
    possible_patterns: list[Pattern] = []
    red_flags: list[str] = []
    urgency: Literal["routine", "soon", "urgent"] = "routine"
    suggested_specialist: str = "gynecologist"
    questions_for_doctor: list[str] = []
    what_to_track: list[str] = []
    disclaimer: str = ""
    sources: list[Source] = []  # filled in code from model-returned IDs
