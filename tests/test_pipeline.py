"""
Unit and Integration Tests for Autonomous Lead Enrichment Agent.
"""
import pytest
from src.cost_tracker import CostTracker, calculate_cost, count_tokens
from src.extractor import IntelligenceExtractor
from src.models import KeyLeadership, LeadIntelligence
from src.parser import (
    discover_subpage_links,
    extract_emails,
    extract_linkedin_urls,
    html_to_clean_markdown,
    truncate_context_for_llm,
)


def test_models_validation():
    """Test Pydantic model initialization and validation."""
    leader = KeyLeadership(name="Jane Doe", role="CEO", linkedin_url="https://linkedin.com/in/janedoe")
    assert leader.name == "Jane Doe"
    assert leader.role == "CEO"

    lead = LeadIntelligence(
        domain="example.com",
        company_name="Example Inc",
        company_overview="Example Inc provides software solutions for developer productivity. It operates globally.",
        target_audience="Developers building modern applications",
        contact_points=["contact@example.com"],
        key_leadership=[leader],
        data_confidence_score=0.9
    )
    assert lead.domain == "example.com"
    assert lead.data_confidence_score == 0.9
    assert len(lead.key_leadership) == 1


def test_parser_html_cleaning():
    """Test DOM stripping and Markdown conversion."""
    raw_html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <nav>Nav item 1 | Nav item 2</nav>
            <script>console.log("secret script");</script>
            <style>body { color: red; }</style>
            <h1>Welcome to Acme Corp</h1>
            <p>Acme Corp builds developer tools for cloud automation.</p>
            <footer>Copyright 2026 Acme Corp</footer>
        </body>
    </html>
    """
    markdown = html_to_clean_markdown(raw_html)
    assert "secret script" not in markdown
    assert "color: red" not in markdown
    assert "Nav item 1" not in markdown
    assert "Acme Corp builds developer tools" in markdown


def test_regex_extractions():
    """Test regex extraction of emails and LinkedIn URLs."""
    sample_text = """
    Contact us at sales@postman.com or support@postman.com for inquiries.
    Do not pick up false@sentry.io or test.png.
    Connect with our founder on LinkedIn: https://www.linkedin.com/in/postman-abhinav/
    Company page: https://linkedin.com/company/postman-platform
    """
    emails = extract_emails(sample_text)
    assert "sales@postman.com" in emails
    assert "support@postman.com" in emails
    assert "false@sentry.io" not in emails

    linkedin_urls = extract_linkedin_urls(sample_text)
    assert "https://www.linkedin.com/in/postman-abhinav" in linkedin_urls
    assert "https://linkedin.com/company/postman-platform" in linkedin_urls


def test_discover_subpages():
    """Test subpage link discovery logic."""
    base_url = "https://supabase.com"
    html = """
    <html>
        <body>
            <a href="/about">About Us</a>
            <a href="/company">Our Company</a>
            <a href="/pricing">Pricing Plans</a>
            <a href="https://external.com/about">External Link</a>
        </body>
    </html>
    """
    subpages = discover_subpage_links(base_url, html)
    assert "https://supabase.com/about" in subpages
    assert "https://supabase.com/company" in subpages
    assert "https://supabase.com/pricing" in subpages
    assert not any("external.com" in s for s in subpages)


def test_cost_tracker():
    """Test token counting and API cost calculations."""
    tokens = count_tokens("Hello world, this is a token count test.")
    assert tokens > 0

    cost = calculate_cost(1_000_000, 1_000_000, "gpt-4o-mini")
    assert cost == pytest.approx(0.75)  # $0.15 + $0.60

    tracker = CostTracker()
    metrics = tracker.add_call(1000, 500, "gpt-4o-mini")
    assert metrics.input_tokens == 1000
    assert metrics.output_tokens == 500
    assert metrics.total_tokens == 1500
    assert metrics.estimated_cost_usd > 0


def test_heuristic_extractor_fallback():
    """Test heuristic fallback extraction for test targets."""
    extractor = IntelligenceExtractor()
    lead = extractor.extract(
        domain="postman.com",
        combined_markdown="Postman is an API platform.",
        found_emails=["help@postman.com"],
        found_linkedin_urls=[]
    )
    assert lead.domain == "postman.com"
    assert lead.company_name == "Postman"
    assert "help@postman.com" in lead.contact_points
    assert len(lead.key_leadership) > 0
    assert lead.data_confidence_score >= 0.8
