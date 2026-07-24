"""Pydantic request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from backend.models.entities import AssetType, ContentStatus, JobStatus, Platform


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AssetResponse(BaseModel):
    id: UUID
    filename: str
    content_type: str
    asset_type: AssetType
    storage_key: str
    extracted_text: str | None = None
    metadata_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentJobCreate(BaseModel):
    prompt: str = Field(min_length=10)
    platform: Platform
    asset_ids: list[UUID] = Field(default_factory=list)


class ContentPackageResponse(BaseModel):
    id: UUID
    job_id: UUID
    title: str
    body: str
    platform: Platform
    status: ContentStatus
    originality_score: float | None = None
    relevance_score: float | None = None
    expertise_score: float | None = None
    banner_storage_key: str | None = None
    metadata_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentJobResponse(BaseModel):
    id: UUID
    prompt: str
    platform: Platform
    status: JobStatus
    asset_ids: list | None = None
    plan_json: dict | None = None
    evaluation_json: dict | None = None
    error_message: str | None = None
    regeneration_count: int
    created_at: datetime
    updated_at: datetime
    packages: list[ContentPackageResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ImproveContentRequest(BaseModel):
    instructions: str | None = None


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str


class PlatformInfo(BaseModel):
    id: Platform
    label: str
    max_length: int | None
    style_notes: str


class EvaluationScores(BaseModel):
    originality: float
    relevance: float
    expertise: float
    passed: bool
    feedback: list[str] = Field(default_factory=list)
