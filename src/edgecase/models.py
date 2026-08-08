from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Scope(StrEnum):
    WHOLE_PROJECT = "whole_project"
    API = "api"
    DATABASE = "database"
    AUTH = "auth"
    BACKGROUND_JOBS = "background_jobs"
    MODULE = "module"


class Depth(StrEnum):
    HIGH_VALUE = "high_value"
    EXHAUSTIVE = "exhaustive"


class Priority(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RepoAnalysis(BaseModel):
    repo_path: Path
    language: str = "python"
    project_type: str | None = None
    frameworks: list[str] = []
    testing_framework: str | None = "pytest"
    dependencies: list[str] = []
    integrations: list[str] = []
    behaviors: list[str] = []
    test_files: list[str] = []
    entry_points: list[str] = []
    databases: list[str] = []
    external_services: list[str] = []
    background_jobs: list[str] = []
    security_boundaries: list[str] = []
    existing_tests_summary: str = ""
    source_file_count: int = 0
    test_function_count: int = 0


class ProjectFingerprint(BaseModel):
    language: str = "python"
    project_type: str | None = None
    frameworks: list[str] = []
    testing_framework: str | None = None
    dependencies: list[str] = []
    integrations: list[str] = []
    behaviors: list[str] = []
    domain: str = ""
    architecture: str = ""
    maturity: str = "unknown"
    is_monorepo: bool = False


class CandidateScenario(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    category: str
    area: str
    scenario: str
    priority: Priority
    why_it_matters: str
    repo_evidence: list[str] = []
    official_evidence: list[str] = []
    similar_project_evidence: list[str] = []
    bug_regression_evidence: list[str] = []
    suggested_test_cases: list[str] = []
    affected_files: list[str] = []


class ValidatedScenario(CandidateScenario):
    devin_relevant: bool = True
    devin_priority: Priority = Priority.MEDIUM
    priority_score: int = 0
    devin_reason: str = ""
    existing_coverage: str = ""


class ContextResearch(BaseModel):
    official_guidance: list[dict] = []
    similar_projects: list[dict] = []
    test_patterns: list[dict] = []
    bugs_regressions: list[dict] = []


class ImplementationResult(BaseModel):
    scenario_id: UUID
    tests_added: int = 0
    passed: int = 0
    failed: int = 0
    potential_implementation_issue: bool = False
    summary: str = ""


class Session(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    repository: str | None = None
    repository_url: str | None = None
    repository_confirmed: bool = False
    scope: Scope = Scope.WHOLE_PROJECT
    depth: Depth = Depth.HIGH_VALUE
    allow_devin_implementation: bool = True
    repo_analysis: RepoAnalysis | None = None
    project_fingerprint: ProjectFingerprint | None = None
    context_research: ContextResearch | None = None
    candidate_scenarios: list[CandidateScenario] = []
    validated_scenarios: list[ValidatedScenario] = []
    selected_scenario: ValidatedScenario | None = None
    implementation_result: ImplementationResult | None = None
    analysis_status: Literal["pending", "running", "completed", "failed"] = "pending"
    analysis_error: str | None = None
    status_detail: str = ""
    expires_at: datetime | None = None
