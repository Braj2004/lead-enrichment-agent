"""
Automated Headless Browser Crawler Module.
Uses Playwright async API to handle dynamic JS rendering, subpage discovery, timeouts, and anti-bot resilience.
Includes standard HTTP fallback if Playwright browser interaction encounters exceptions.
"""
import asyncio
import logging
import urllib.request
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Browser, Page

from src.parser import html_to_clean_markdown, discover_subpage_links, extract_emails, extract_linkedin_urls

logger = logging.getLogger(__name__)

# Default realistic User-Agent to avoid bot blocking
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class CrawledPageResult:
    """Data container for a single crawled page."""
    def __init__(self, url: str, raw_html: str, markdown: str, status_code: int = 200, error: Optional[str] = None):
        self.url = url
        self.raw_html = raw_html
        self.markdown = markdown
        self.status_code = status_code
        self.error = error
        self.emails = extract_emails(raw_html + "\n" + markdown)
        self.linkedin_urls = extract_linkedin_urls(raw_html + "\n" + markdown)


class WebCrawler:
    """Async Web Crawler utilizing Playwright headless browser automation."""

    def __init__(self, headless: bool = True, timeout_ms: int = 12000):
        self.headless = headless
        self.timeout_ms = timeout_ms

    def normalize_url(self, domain_or_url: str) -> str:
        """Ensure domain string is formatted into a valid HTTPS URL."""
        domain_or_url = domain_or_url.strip()
        if not domain_or_url.startswith("http://") and not domain_or_url.startswith("https://"):
            return f"https://{domain_or_url}"
        return domain_or_url

    async def fetch_page_playwright(self, page: Page, url: str) -> CrawledPageResult:
        """Fetch page content using Playwright headless browser."""
        try:
            # Navigate with domcontentloaded for fast response
            response = await page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
            status_code = response.status if response else 200
            
            # Brief pause for client-side JS rendering
            await asyncio.sleep(0.8)

            raw_html = await page.content()
            markdown = html_to_clean_markdown(raw_html)

            return CrawledPageResult(
                url=url,
                raw_html=raw_html,
                markdown=markdown,
                status_code=status_code
            )

        except Exception as e:
            logger.warning(f"Playwright navigation failed for {url}: {e}. Trying HTTP fallback.")
            return await self.fetch_page_http_fallback(url, str(e))

    async def fetch_page_http_fallback(self, url: str, error_msg: str = "") -> CrawledPageResult:
        """Fallback lightweight HTTP fetcher if headless browser encounters an issue."""
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": DEFAULT_USER_AGENT}
            )
            loop = asyncio.get_event_loop()
            
            def _fetch():
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return resp.read().decode('utf-8', errors='ignore'), resp.status

            raw_html, status_code = await loop.run_in_executor(None, _fetch)
            markdown = html_to_clean_markdown(raw_html)

            return CrawledPageResult(
                url=url,
                raw_html=raw_html,
                markdown=markdown,
                status_code=status_code
            )
        except Exception as fallback_err:
            logger.error(f"HTTP fallback also failed for {url}: {fallback_err}")
            return CrawledPageResult(
                url=url,
                raw_html="",
                markdown=f"Failed to crawl page: {error_msg} | Fallback error: {fallback_err}",
                status_code=500,
                error=str(fallback_err)
            )

    async def crawl_domain(self, domain_or_url: str, max_subpages: int = 4) -> List[CrawledPageResult]:
        """
        Crawl target company domain:
        1. Fetch homepage.
        2. Discover relevant subpages (/about, /team, /company, /contact, /pricing).
        3. Crawl target subpages and aggregate structured content.
        """
        start_url = self.normalize_url(domain_or_url)
        results: List[CrawledPageResult] = []

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox"
                    ]
                )
                context = await browser.new_context(
                    user_agent=DEFAULT_USER_AGENT,
                    viewport={"width": 1280, "height": 800}
                )
                page = await context.new_page()

                # Step 1: Crawl homepage
                logger.info(f"Crawling target homepage: {start_url}")
                homepage_res = await self.fetch_page_playwright(page, start_url)
                results.append(homepage_res)

                # Step 2: Subpage Discovery
                discovered_subpages = []
                if homepage_res.raw_html:
                    discovered_subpages = discover_subpage_links(start_url, homepage_res.raw_html, max_links=max_subpages)
                    logger.info(f"Discovered {len(discovered_subpages)} relevant subpages for {domain_or_url}: {discovered_subpages}")

                # Step 3: Crawl discovered subpages
                for sub_url in discovered_subpages:
                    logger.info(f"Crawling discovered subpage: {sub_url}")
                    sub_res = await self.fetch_page_playwright(page, sub_url)
                    results.append(sub_res)

                await context.close()
                await browser.close()

            except Exception as browser_err:
                logger.error(f"Playwright browser failure for {domain_or_url}: {browser_err}. Falling back to HTTP.")
                if not results:
                    homepage_res = await self.fetch_page_http_fallback(start_url, str(browser_err))
                    results.append(homepage_res)

        return results
