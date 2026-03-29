#!/usr/bin/env python3
"""
Agent Metrics Reporter
Reports agent run metrics to the centralized metrics endpoint.

Uses only Python stdlib (no external dependencies).
Reads AGENT_METRICS_ENDPOINT from environment.
"""

import os
import sys
import json
import uuid
import urllib.request
import urllib.error
import argparse
from datetime import datetime, timezone


def send_metrics(payload, endpoint):
    """Send metrics payload to the endpoint. Returns True on success."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"Metrics reported (run_id: {payload['run_id']}, status code: {resp.status})")
            return True
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"Warning: Failed to report metrics: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Report agent run metrics to the centralized endpoint"
    )
    parser.add_argument("--agent-name", required=True, help="Agent name")
    parser.add_argument("--agent-owner", default="Vladimir Litvinchik", help="Agent owner")
    parser.add_argument("--job-type", required=True, help="Job type")
    parser.add_argument("--run-id", help="Unique run ID (auto-generated if omitted)")
    parser.add_argument("--status", required=True, choices=["success", "failure"], help="Run status")
    parser.add_argument("--product", default="GroupDocs.Total", help="Product name")
    parser.add_argument("--platform", default="All", help="Platform")
    parser.add_argument("--website", default="groupdocs.com", help="Website")
    parser.add_argument("--website-section", default="Blog", help="Website section")
    parser.add_argument("--item-name", default="Translation", help="Item name")
    parser.add_argument("--items-discovered", type=int, default=0, help="Items discovered")
    parser.add_argument("--items-failed", type=int, default=0, help="Items failed")
    parser.add_argument("--items-succeeded", type=int, default=0, help="Items succeeded")
    parser.add_argument("--run-duration-ms", type=int, default=0, help="Run duration in ms")
    parser.add_argument("--token-usage", type=int, default=0, help="Total LLM token usage")
    parser.add_argument("--api-calls-count", type=int, default=0, help="LLM API calls count")

    args = parser.parse_args()

    endpoint = os.environ.get("AGENT_METRICS_ENDPOINT")
    if not endpoint:
        print("AGENT_METRICS_ENDPOINT not set, skipping metrics reporting", file=sys.stderr)
        sys.exit(0)

    run_id = args.run_id
    if not run_id:
        slug = args.agent_name.lower().replace(" ", "_")
        run_id = f"{slug}_{uuid.uuid4().hex[:8]}"

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_name": args.agent_name,
        "agent_owner": args.agent_owner,
        "job_type": args.job_type,
        "run_id": run_id,
        "status": args.status,
        "product": args.product,
        "platform": args.platform,
        "website": args.website,
        "website_section": args.website_section,
        "item_name": args.item_name,
        "items_discovered": args.items_discovered,
        "items_failed": args.items_failed,
        "items_succeeded": args.items_succeeded,
        "run_duration_ms": args.run_duration_ms,
        "token_usage": args.token_usage,
        "api_calls_count": args.api_calls_count,
    }

    send_metrics(payload, endpoint)


if __name__ == "__main__":
    main()
