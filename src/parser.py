"""
DOM Pre-processing and Context Optimization Module.
Strips boilerplate, extracts clean Markdown, emails, LinkedIn URLs, and relevant subpage links.
"""
import re
from typing import List, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import html2text

# Excluded email domains / false positives
FALSE_POSITIVE_EMAILS = {
    "example.com", "domain.com", "sentry.io", "wixpress.com", "schema.org",
    "png", "jpg", "jpeg", "svg", "webp", "gif"
}

# Subpage keywords to target for deep intelligence gathering
TARGET_SUBPAGE_KEYWORDS = [
    "about", "about-us", "company", "team", "leadership", "contact", "contact-us",
    "pricing", "careers", "founders", "management"
]


def clean_html_soup(html_content: str) -> BeautifulSoup:
    """Parse HTML and strip scripts, styles, SVGs, headers, footers, and boilerplate tags."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Tags to remove completely
    unwanted_tags = [
        "script", "style", "svg", "noscript", "iframe", "form",
        "nav", "footer", "header", "button", "input", "select",
        "textarea", "picture", "path", "symbol"
    ]
    for tag in unwanted_tags:
        for element in soup.find_all(tag):
            element.decompose()

    # Remove hidden elements or elements with display:none style
    for element in soup.find_all(style=re.compile(r"display\s*:\s*none", re.I)):
        element.decompose()

    return soup


def html_to_clean_markdown(html_content: str) -> str:
    """Convert raw HTML into token-optimized Markdown text."""
    if not html_content or not html_content.strip():
        return ""

    soup = clean_html_soup(html_content)
    
    # Configure html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = True
    h.ignore_tables = False
    h.body_width = 0

    raw_markdown = h.handle(str(soup))

    # Post-process markdown to trim excessive whitespace and linebreaks
    lines = [line.strip() for line in raw_markdown.splitlines()]
    non_empty_lines = []
    prev_empty = False

    for line in lines:
        if not line:
            if not prev_empty:
                non_empty_lines.append("")
                prev_empty = True
        else:
            non_empty_lines.append(line)
            prev_empty = False

    cleaned_text = "\n".join(non_empty_lines).strip()
    return cleaned_text


def extract_emails(text: str) -> List[str]:
    """Extract valid public email addresses using regex."""
    if not text:
        return []
    
    # Standard email regex pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    matches = re.findall(email_pattern, text)
    
    valid_emails: Set[str] = set()
    for email in matches:
        email_lower = email.lower()
        domain_part = email_lower.split("@")[-1]
        
        # Filter out common false positives and image extensions
        if any(domain_part.endswith(fp) for fp in FALSE_POSITIVE_EMAILS):
            continue
        if any(email_lower.endswith(ext) for ext in [".png", ".jpg", ".svg", ".webp", ".css", ".js"]):
            continue
        
        valid_emails.add(email_lower)
        
    return sorted(list(valid_emails))


def extract_linkedin_urls(text_or_html: str) -> List[str]:
    """Extract LinkedIn personal profile and company URLs from page text or HTML."""
    if not text_or_html:
        return []
    
    linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/(?:in|company)/[a-zA-Z0-9%_-]+/?'
    matches = re.findall(linkedin_pattern, text_or_html, re.IGNORECASE)
    
    # Standardize URLs
    urls: Set[str] = set()
    for url in matches:
        clean_url = url.rstrip("/")
        if "/in/" in clean_url or "/company/" in clean_url:
            urls.add(clean_url)
            
    return sorted(list(urls))


def discover_subpage_links(base_url: str, html_content: str, max_links: int = 5) -> List[str]:
    """
    Discover relevant subpages (e.g. /about, /team, /company, /contact, /pricing)
    belonging to the same domain.
    """
    if not html_content or not base_url:
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    base_domain = urlparse(base_url).netloc.lower()

    discovered_links: List[str] = []
    seen_urls: Set[str] = {base_url.rstrip("/")}

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
            continue

        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        url_domain = parsed_url.netloc.lower()

        # Must match exact domain or subdomains of base_domain
        if url_domain != base_domain and not url_domain.endswith("." + base_domain):
            continue

        clean_path = parsed_url.path.lower().rstrip("/")
        normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}".rstrip("/")

        if normalized_url in seen_urls:
            continue

        # Check if path contains any key subpage target keywords
        path_segments = [seg for seg in clean_path.split("/") if seg]
        is_target = any(
            kw in clean_path or any(kw == seg for seg in path_segments)
            for kw in TARGET_SUBPAGE_KEYWORDS
        )

        if is_target:
            seen_urls.add(normalized_url)
            discovered_links.append(normalized_url)
            if len(discovered_links) >= max_links:
                break

    return discovered_links


def truncate_context_for_llm(context: str, max_chars: int = 15000) -> str:
    """Limit character count to keep LLM context crisp and token-efficient."""
    if len(context) <= max_chars:
        return context
    return context[:max_chars] + "\n... [Content truncated for token optimization] ..."
