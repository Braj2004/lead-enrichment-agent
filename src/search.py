"""
External Search Integration Module (Bonus Feature).
Uses search engine queries (DuckDuckGo search) to look up external LinkedIn URLs for founders,
leadership, or company profiles if not discoverable directly on the website.
"""
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import unquote

try:
    from duckduckgo_search import DDGS
    DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False

logger = logging.getLogger(__name__)


def extract_linkedin_from_text(text: str) -> Optional[str]:
    """Extract first valid personal LinkedIn URL from text."""
    match = re.search(r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9%_-]+/?', text, re.IGNORECASE)
    if match:
        return match.group(0).rstrip("/")
    return None


def search_external_leadership(domain: str, company_name: str) -> List[Dict[str, str]]:
    """
    Search external engine for company founder/executive leadership & LinkedIn URLs.
    """
    results: List[Dict[str, str]] = []
    queries = [
        f'"{company_name}" founder CEO CTO site:linkedin.com/in',
        f'"{company_name}" leadership team site:linkedin.com/in'
    ]

    if not DDG_AVAILABLE:
        logger.warning("duckduckgo_search package not available. Skipping external search fallback.")
        return results

    try:
        with DDGS() as ddgs:
            for query in queries:
                logger.info(f"Executing search fallback query: {query}")
                search_results = list(ddgs.text(query, max_results=3))
                
                for item in search_results:
                    title = item.get("title", "")
                    snippet = item.get("body", "")
                    href = item.get("href", "")

                    linkedin_url = extract_linkedin_from_text(href) or extract_linkedin_from_text(snippet)
                    
                    if linkedin_url:
                        # Parse name and title from search result
                        name_title = title.split("-")[0].split("|")[0].strip()
                        results.append({
                            "name_or_title": name_title,
                            "snippet": snippet,
                            "linkedin_url": linkedin_url
                        })

    except Exception as e:
        logger.warning(f"External search query failed for {company_name}: {e}")

    return results


def search_specific_person_linkedin(company_name: str, person_name: str) -> Optional[str]:
    """Search specifically for a named person's LinkedIn profile at a target company."""
    if not DDG_AVAILABLE:
        return None

    query = f'"{person_name}" "{company_name}" site:linkedin.com/in'
    try:
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=2))
            for item in search_results:
                href = item.get("href", "")
                snippet = item.get("body", "")
                linkedin_url = extract_linkedin_from_text(href) or extract_linkedin_from_text(snippet)
                if linkedin_url:
                    return linkedin_url
    except Exception as e:
        logger.warning(f"Search for {person_name} at {company_name} failed: {e}")
        
    return None
