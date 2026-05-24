"""RAG 相关 Pydantic schema"""

from pydantic import BaseModel
from typing import Optional


class ResumeQueryRequest(BaseModel):
    question: str


class ReferenceItem(BaseModel):
    content: str
    section: str


class ResumeQueryResponse(BaseModel):
    answer: str
    references: list[ReferenceItem] = []


class JobMatchRequest(BaseModel):
    job_id: int


class MatchScore(BaseModel):
    dimension: str
    score: float  # 0-1
    reason: str


class JobMatchResponse(BaseModel):
    overall_score: float
    scores: list[MatchScore]
    analysis: str
    suggestions: list[str] = []


class ResumeDiagnoseResponse(BaseModel):
    overall_score: str
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[dict] = []


class OptimizeRequest(BaseModel):
    job_id: int


class OptimizedSection(BaseModel):
    section: str
    original: str
    optimized: str
    change_reason: str


class OptimizeResponse(BaseModel):
    optimized_sections: list[OptimizedSection] = []
    full_resume: str
    summary: dict = {}