"""
Pydantic data models for Lead Intelligence extraction, cost tracking, and pipeline output schemas.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class KeyLeadership(BaseModel):
    """Information on key leadership or team members."""
    name: str = Field(description="Full name of the leader or team member")
    role: str = Field(description="Title or role (e.g. Founder, CEO, CTO, VP of Engineering)")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL if discoverable")


class CostMetrics(BaseModel):
    """Token usage and estimated cost metrics for LLM API calls."""
    input_tokens: int = Field(default=0, description="Total input tokens consumed")
    output_tokens: int = Field(default=0, description="Total output tokens generated")
    total_tokens: int = Field(default=0, description="Total tokens combined")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated API cost in USD")


class LeadIntelligence(BaseModel):
    """Structured Lead Intelligence extracted for a single target company domain."""
    domain: str = Field(description="Target company domain (e.g. postman.com)")
    company_name: str = Field(description="Official company name")
    company_overview: str = Field(
        description="A concise 2-sentence summary of what the company does."
    )
    target_audience: str = Field(
        description="Target Audience / ICP: Who their product is built for (e.g., 'Developers building API workflows')."
    )
    contact_points: List[str] = Field(
        default_factory=list,
        description="Generic or public emails found on the site (e.g. contact@, sales@, support@)."
    )
    key_leadership: List[KeyLeadership] = Field(
        default_factory=list,
        description="Key leadership / team members with name, role, and optional LinkedIn URL."
    )
    data_confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="An estimated score between 0.0 and 1.0 indicating data quality/completeness."
    )
    pages_crawled: List[str] = Field(
        default_factory=list,
        description="List of subpage URLs successfully fetched and analyzed."
    )
    search_queries_used: List[str] = Field(
        default_factory=list,
        description="External search queries executed during lead enrichment fallback."
    )
    cost_metrics: CostMetrics = Field(
        default_factory=CostMetrics,
        description="Token usage and cost breakdown for this domain."
    )


class PipelineResult(BaseModel):
    """Aggregated output containing results for all target domains and total cost metrics."""
    results: List[LeadIntelligence] = Field(default_factory=list)
    total_domains: int = 0
    successful_domains: int = 0
    failed_domains: int = 0
    total_cost_metrics: CostMetrics = Field(default_factory=CostMetrics)
