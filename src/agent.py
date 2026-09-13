"""
Autonomous Lead Enrichment Agent Module.
Implements a multi-step agentic decision loop to crawl, parse, evaluate data confidence,
and trigger external search fallback for missing leadership/LinkedIn information.
"""
import logging
from typing import List, Optional

# pyrefly: ignore [missing-import]
from src.cost_tracker import CostTracker
# pyrefly: ignore [missing-import]
from src.crawler import CrawledPageResult, WebCrawler
# pyrefly: ignore [missing-import]
from src.extractor import IntelligenceExtractor
# pyrefly: ignore [missing-import]
from src.models import KeyLeadership, LeadIntelligence
# pyrefly: ignore [missing-import]
from src.parser import truncate_context_for_llm
# pyrefly: ignore [missing-import]
from src.search import search_external_leadership, search_specific_person_linkedin

logger = logging.getLogger(__name__)


class AutonomousLeadAgent:
    """
    Autonomous Lead Enrichment Agent featuring multi-step tool execution,
    dynamic context optimization, confidence evaluation, and search fallback.
    """

    def __init__(self, headless: bool = True, cost_tracker: Optional[CostTracker] = None):
        self.crawler = WebCrawler(headless=headless)
        self.cost_tracker = cost_tracker or CostTracker()
        self.extractor = IntelligenceExtractor(cost_tracker=self.cost_tracker)

    async def run(self, domain: str) -> LeadIntelligence:
        """
        Execute full autonomous lead enrichment loop for a target domain.
        """
        logger.info(f"=== Starting Autonomous Lead Enrichment for domain: {domain} ===")
        pages_crawled_urls: List[str] = []
        search_queries_used: List[str] = []

        # Step 1: Automated Browsing & Content Retrieval
        crawled_results: List[CrawledPageResult] = await self.crawler.crawl_domain(domain, max_subpages=4)
        
        combined_markdown_pieces: List[str] = []
        all_emails: List[str] = []
        all_linkedin_urls: List[str] = []

        for page_res in crawled_results:
            pages_crawled_urls.append(page_res.url)
            if page_res.markdown:
                combined_markdown_pieces.append(f"--- PAGE: {page_res.url} ---\n{page_res.markdown}")
            all_emails.extend(page_res.emails)
            all_linkedin_urls.extend(page_res.linkedin_urls)

        # Deduplicate emails and LinkedIn URLs
        unique_emails = sorted(list(set(all_emails)))
        unique_linkedin_urls = sorted(list(set(all_linkedin_urls)))

        # Step 2: Context Pre-Processing & Token Optimization
        raw_combined_markdown = "\n\n".join(combined_markdown_pieces)
        optimized_context = truncate_context_for_llm(raw_combined_markdown, max_chars=12000)

        # Step 3: Initial LLM Extraction
        lead_info: LeadIntelligence = self.extractor.extract(
            domain=domain,
            combined_markdown=optimized_context,
            found_emails=unique_emails,
            found_linkedin_urls=unique_linkedin_urls
        )
        lead_info.pages_crawled = pages_crawled_urls

        # Step 4: Evaluate Data Completeness & Trigger External Search Fallback
        # If leadership list is empty or any key leader is missing a LinkedIn URL, trigger search engine fallback
        needs_search_fallback = (
            len(lead_info.key_leadership) == 0 or
            any(leader.linkedin_url is None for leader in lead_info.key_leadership)
        )

        if needs_search_fallback:
            company_name = lead_info.company_name or domain.split(".")[0].capitalize()
            logger.info(f"Triggering Search Fallback for {company_name} leadership/LinkedIn discovery...")

            # 4a. If leadership members exist without LinkedIn, search per leader
            if lead_info.key_leadership:
                for leader in lead_info.key_leadership:
                    if not leader.linkedin_url:
                        q_str = f'"{leader.name}" "{company_name}" site:linkedin.com/in'
                        search_queries_used.append(q_str)
                        found_url = search_specific_person_linkedin(company_name, leader.name)
                        if found_url:
                            leader.linkedin_url = found_url
                            logger.info(f"Discovered LinkedIn URL for {leader.name}: {found_url}")
            
            # 4b. If no leadership members were extracted at all, run broad search fallback
            else:
                q_str = f'"{company_name}" founder CEO CTO site:linkedin.com/in'
                search_queries_used.append(q_str)
                external_leaders = search_external_leadership(domain, company_name)
                for item in external_leaders:
                    lead_info.key_leadership.append(
                        KeyLeadership(
                            name=item["name_or_title"],
                            role="Leadership Team",
                            linkedin_url=item["linkedin_url"]
                        )
                    )

        lead_info.search_queries_used = search_queries_used

        # Step 5: Recalculate Final Data Confidence Score
        confidence = 0.50
        if lead_info.company_overview and len(lead_info.company_overview) > 30:
            confidence += 0.20
        if lead_info.target_audience and len(lead_info.target_audience) > 15:
            confidence += 0.15
        if lead_info.key_leadership:
            confidence += 0.10
        if lead_info.contact_points:
            confidence += 0.05

        lead_info.data_confidence_score = round(min(1.0, confidence), 2)
        logger.info(f"Completed enrichment for {domain} with Confidence Score: {lead_info.data_confidence_score}")

        return lead_info
