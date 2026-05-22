from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class VersionItem(BaseModel):
    id: int
    version: int
    source: str
    summary: Optional[str] = None
    job_id: Optional[int] = None
    created_at: datetime


class VersionDetail(BaseModel):
    id: int
    version: int
    source: str
    content: str
    summary: Optional[str] = None
    job_id: Optional[int] = None
    created_at: datetime


class VersionListResponse(BaseModel):
    versions: List[VersionItem]


class SaveVersionRequest(BaseModel):
    content: str
    source: str = "manual"
    summary: Optional[str] = None
    job_id: Optional[int] = None


class CompareItem(BaseModel):
    section: str
    before: str
    after: str


class CompareResponse(BaseModel):
    v1_id: int
    v2_id: int
    v1_version: int
    v2_version: int
    changes: List[CompareItem]
