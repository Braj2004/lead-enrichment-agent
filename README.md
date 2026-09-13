# 🚀 Autonomous Lead Enrichment Agent

An autonomous, resilient Python agent that accepts company domains as input, crawls and parses their public web presence using headless browser automation (Playwright), pre-processes DOM trees into token-optimized Markdown, and outputs structured company intelligence using an LLM (with fallback search integration and token/cost tracking).

---

## 📌 Target Domains Tested
- `postman.com`
- `supabase.com`
- `vapi.ai`

---

## 🌟 Key Features & Core Architecture

1. **Automated Browsing & Subpage Discovery (Step 1)**
   - Powered by Playwright headless browser automation.
   - Dynamically renders JavaScript-heavy websites.
   - Automatically discovers key subpages (`/about`, `/team`, `/company`, `/contact`, `/pricing`).
   - Includes automatic network fallback to standard HTTP fetching if browser interaction times out.

2. **Context Pre-Processing & Token Optimization (Step 2)**
   - Strips non-content DOM elements (`<script>`, `<style>`, `<svg>`, `<nav>`, `<footer>`, `<header>`, hidden forms).
   - Converts clean HTML into minimal, high-signal Markdown.
   - Pre-extracts emails and LinkedIn URLs via regex.
   - Limits context window size to optimize LLM tokens and latency.

3. **LLM Extraction & Strict Structured Outputs (Step 3)**
   - Enforces Pydantic schema validation for guaranteed output formatting.
   - Extracts:
     - **Company Overview**: Concise 2-sentence summary.
     - **Target Audience / ICP**: Ideal Customer Profile description.
     - **Contact Points**: Generic/public email addresses.
     - **Key Leadership / Team Members**: Name, role/title, and LinkedIn profile URL.
     - **Data Confidence Score**: Float between `0.0` and `1.0`.
   - Native integration with **OpenAI** (`gpt-4o-mini`, `gpt-4o`) and **Google Gemini** (`gemini-2.5-flash`), plus a rule-based **Heuristic Fallback Extractor** that guarantees resilient execution even without API keys.

4. **Fallback & Error Resilience (Step 4)**
   - Gracefully handles 404s, bot blockers, timeouts, and missing DOM elements.
   - Zero-crash guarantee across multi-domain batch execution.

5. **Bonus Features Included 🎁**
   - **Google / External Search Integration**: Automatically executes external web search fallback queries to discover missing LinkedIn profiles for founders and key leadership.
   - **Agentic Workflow**: Multi-step orchestrator loop that dynamically evaluates data completeness, detects missing leadership/LinkedIn URLs, and triggers targeted sub-crawls or search queries.
   - **Token Usage & API Cost Tracking**: Tracks exact input/output tokens per domain and calculates real-time API cost in USD based on model pricing tables.

---

## 📁 Repository Structure

```
lead-enrichment-agent/
├── README.md                 # Complete documentation, setup guide & ops confirmation
├── requirements.txt           # Python dependency declarations
├── pyproject.toml             # Project metadata & build tool config
├── .env.example               # Template for API keys and model configuration
├── main.py                    # CLI entry point to run pipeline
├── output.json                # Generated structured JSON output
├── output.csv                 # Generated tabular CSV spreadsheet
├── src/
│   ├── __init__.py
│   ├── models.py              # Pydantic schemas (LeadIntelligence, KeyLeadership, CostMetrics)
│   ├── crawler.py             # Playwright async browser automation & subpage discovery
│   ├── parser.py              # DOM cleaning, markdown conversion, regex email/LinkedIn extractors
│   ├── search.py              # External DuckDuckGo search fallback for missing LinkedIn URLs
│   ├── extractor.py           # Structured output LLM extractor (OpenAI, Gemini & Heuristic Fallback)
│   ├── cost_tracker.py        # Real-time token usage counter & USD cost calculator
│   └── agent.py               # Autonomous multi-step agentic orchestrator loop
└── tests/
    └── test_pipeline.py       # Unit & integration test suite (pytest)
```

---

## 🛠️ Setup & Installation

### 1. Clone & Navigate to Project
```bash
git clone <your-repo-link>
cd lead-enrichment-agent
```

### 2. Set Up Virtual Environment & Dependencies
Using `uv` (recommended) or standard `venv`:

```bash
# Using uv (fast)
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Or using standard python venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Install Playwright Chromium Browser
```bash
playwright install chromium
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and set your API keys:
```bash
cp .env.example .env
```
Contents of `.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gpt-4o-mini
```
*Note: If no API key is set, the agent automatically runs in offline **Heuristic Fallback Mode** so execution always succeeds!*

---

## 💻 How to Run

### Run Pipeline on Test Target Domains
```bash
python main.py
```

### Run Pipeline on Custom Domains
```bash
python main.py --domains postman.com supabase.com vapi.ai
```

### Specify Custom Output Paths
```bash
python main.py --output-json output.json --output-csv output.csv
```

### Run Unit Tests
```bash
pytest
```

---

## 📊 Sample Output Preview (`output.json`)

```json
{
  "results": [
    {
      "domain": "postman.com",
      "company_name": "Postman",
      "company_overview": "Postman is an API platform for building, testing, and managing APIs across the entire software development lifecycle. It enables software engineering teams to collaborate seamlessly on API design, documentation, and automated testing.",
      "target_audience": "Software engineers, API developers, DevOps teams, and enterprise product managers building web and mobile APIs.",
      "contact_points": [
        "help@postman.com",
        "sales@postman.com"
      ],
      "key_leadership": [
        {
          "name": "Abhinav Asthana",
          "role": "Co-Founder & CEO",
          "linkedin_url": "https://www.linkedin.com/in/postman-abhinav"
        },
        {
          "name": "Ankit Sobti",
          "role": "Co-Founder & CTO",
          "linkedin_url": "https://www.linkedin.com/in/ankit-sobti"
        }
      ],
      "data_confidence_score": 0.95,
      "pages_crawled": [
        "https://postman.com",
        "https://postman.com/about"
      ],
      "cost_metrics": {
        "input_tokens": 3450,
        "output_tokens": 250,
        "total_tokens": 3700,
        "estimated_cost_usd": 0.000668
      }
    }
  ],
  "total_domains": 3,
  "successful_domains": 3,
  "failed_domains": 0,
  "total_cost_metrics": {
    "input_tokens": 10250,
    "output_tokens": 750,
    "total_tokens": 11000,
    "estimated_cost_usd": 0.001988
  }
}
```

---
## 👤 Author & Project Metadata
> **Brajnandan Prasad**  
> *AI/ML Intern @ Infosys Springboard | Data Scientist | B.Tech CSE ’26*  
> 
> 📌 **Project**: Autonomous Lead Enrichment Agent  
> 🎯 **Focus**: Web Scraping Automation, Token-Optimized DOM Parsing & Structured LLM Extraction  
> 🛠️ **Core Tech Stack**: Python | Playwright | Pydantic | OpenAI / Gemini | DuckDuckGo API | AsyncIO | Pytest  
> 📬 **Contact**: [LinkedIn](www.linkedin.com/in/brajnandan-prasad-2b43b72a6) • [GitHub](https://github.com/Braj2004) • `brajnandanprasad21@gmail.com`
---

