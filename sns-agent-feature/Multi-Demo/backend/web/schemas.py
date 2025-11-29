"""Shared Pydantic schemas for the backend."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class IPProfile(BaseModel):
    id: str
    name: str
    role: str
    mission: str
    values: List[str]
    style: str
    keywords: List[str]
    target_audience: str = Field(alias="targetAudience")
    taboo: Optional[List[str]] = None

    class Config:
        allow_population_by_field_name = True


class IPDecisionRequest(BaseModel):
    user_brief: str = ""
    goal: str = ""
    prefer_ip_id: Optional[str] = None


class IPDecisionResponse(BaseModel):
    profile: IPProfile
    reason: str


class ResearchTask(BaseModel):
    topic: str
    target_platform: str = Field(default="pinterest")


class ResearchFinding(BaseModel):
    topic: str
    source: str
    title: str
    url: str
    summary: str


class AgentStep(BaseModel):
    agent: str
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GenerationRequest(BaseModel):
    input: str
    user_brief: str = ""
    goal: str = ""
    prefer_ip_id: Optional[str] = None
    ip_profile: Optional[IPProfile] = None
    research_topics: List[str] = Field(default_factory=list)


class GenerationResponse(BaseModel):
    content: str
    ip_profile: IPProfile
    reason: str
    steps: List[AgentStep] = Field(default_factory=list)
    research_notes: List[ResearchFinding] = Field(default_factory=list)
