#!/usr/bin/env python3
"""
Autonomous Lead Enrichment Agent CLI Entry Point.

Usage:
    python main.py
    python main.py --domains postman.com supabase.com vapi.ai
    python main.py --output-json output.json --output-csv output.csv
"""
import argparse
import asyncio
import csv
import json
import logging
import os
import sys
from typing import List

from dotenv import load_dotenv

# Ensure local packages are importable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agent import AutonomousLeadAgent
from src.cost_tracker import CostTracker
from src.models import LeadIntelligence, PipelineResult

# Load environment variables from .env file
load_dotenv()


def configure_logging(verbose: bool = False):
    """Configure terminal logging formatting."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )


def save_json_output(pipeline_result: PipelineResult, file_path: str):
    """Save structured extraction results to JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_result.model_dump(), f, indent=2)
    print(f"✅ Exported JSON results to: {file_path}")


def save_csv_output(pipeline_result: PipelineResult, file_path: str):
    """Save key lead metrics to CSV spreadsheet file."""
    fieldnames = [
        "domain",
        "company_name",
        "company_overview",
        "target_audience",
        "contact_points",
        "key_leadership",
        "data_confidence_score",
        "input_tokens",
        "output_tokens",
        "estimated_cost_usd"
    ]

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for lead in pipeline_result.results:
            leadership_str = "; ".join(
                [f"{l.name} ({l.role})" + (f" - {l.linkedin_url}" if l.linkedin_url else "") for l in lead.key_leadership]
            )
            writer.writerow({
                "domain": lead.domain,
                "company_name": lead.company_name,
                "company_overview": lead.company_overview,
                "target_audience": lead.target_audience,
                "contact_points": ", ".join(lead.contact_points),
                "key_leadership": leadership_str,
                "data_confidence_score": lead.data_confidence_score,
                "input_tokens": lead.cost_metrics.input_tokens,
                "output_tokens": lead.cost_metrics.output_tokens,
                "estimated_cost_usd": lead.cost_metrics.estimated_cost_usd
            })
    print(f"📊 Exported CSV results to: {file_path}")


async def run_pipeline(domains: List[str], headless: bool, output_json: str, output_csv: str) -> PipelineResult:
    """Run lead enrichment agent against all target domains sequentially."""
    cost_tracker = CostTracker()
    agent = AutonomousLeadAgent(headless=headless, cost_tracker=cost_tracker)
    
    results: List[LeadIntelligence] = []
    successful = 0
    failed = 0

    print("\n" + "=" * 70)
    print("🚀 AUTONOMOUS LEAD ENRICHMENT AGENT PIPELINE")
    print(f"Target Domains ({len(domains)}): {', '.join(domains)}")
    print("=" * 70 + "\n")

    for domain in domains:
        print(f"🔍 Processing Target Domain: {domain}...")
        try:
            lead_info = await agent.run(domain)
            results.append(lead_info)
            successful += 1
            
            print(f"   🏢 Company: {lead_info.company_name}")
            print(f"   📝 Overview: {lead_info.company_overview}")
            print(f"   🎯 ICP: {lead_info.target_audience}")
            print(f"   📧 Emails: {', '.join(lead_info.contact_points) if lead_info.contact_points else 'None found'}")
            print(f"   👥 Leadership: {len(lead_info.key_leadership)} members found")
            for leader in lead_info.key_leadership:
                link_text = f" [{leader.linkedin_url}]" if leader.linkedin_url else ""
                print(f"      - {leader.name} ({leader.role}){link_text}")
            print(f"   ⭐ Confidence Score: {lead_info.data_confidence_score}")
            print(f"   💰 Token Usage & Cost: {lead_info.cost_metrics.total_tokens} tokens (${lead_info.cost_metrics.estimated_cost_usd:.6f})")
            print("-" * 70)

        except Exception as err:
            print(f"❌ Error enriching domain {domain}: {err}")
            failed += 1

    total_metrics = cost_tracker.get_metrics()
    
    pipeline_result = PipelineResult(
        results=results,
        total_domains=len(domains),
        successful_domains=successful,
        failed_domains=failed,
        total_cost_metrics=total_metrics
    )

    # Save outputs
    save_json_output(pipeline_result, output_json)
    save_csv_output(pipeline_result, output_csv)

    print("\n" + "=" * 70)
    print("📈 PIPELINE EXECUTION SUMMARY")
    print(f"   Total Domains Processed : {len(domains)}")
    print(f"   Successful Enrichments  : {successful}")
    print(f"   Failed Enrichments      : {failed}")
    print(f"   Total Input Tokens      : {total_metrics.input_tokens}")
    print(f"   Total Output Tokens     : {total_metrics.output_tokens}")
    print(f"   Total Estimated Cost    : ${total_metrics.estimated_cost_usd:.6f} USD")
    print("=" * 70 + "\n")

    return pipeline_result


def main():
    parser = argparse.ArgumentParser(description="Autonomous Lead Enrichment Agent")
    parser.add_argument(
        "--domains",
        nargs="+",
        default=["postman.com", "supabase.com", "vapi.ai"],
        help="List of target company domains to analyze (default: postman.com supabase.com vapi.ai)"
    )
    parser.add_argument(
        "--output-json",
        default="output.json",
        help="Output file path for JSON results (default: output.json)"
    )
    parser.add_argument(
        "--output-csv",
        default="output.csv",
        help="Output file path for CSV results (default: output.csv)"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with visible UI for debugging"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed debug log output"
    )

    args = parser.parse_args()
    configure_logging(args.verbose)

    headless = not args.no_headless
    asyncio.run(run_pipeline(args.domains, headless, args.output_json, args.output_csv))


if __name__ == "__main__":
    main()
