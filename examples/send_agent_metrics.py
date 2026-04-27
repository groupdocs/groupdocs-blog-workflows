"""
Example: Send Agent Metrics to the centralized endpoint.

Usage:
    export AGENT_METRICS_ENDPOINT="https://your-endpoint/api/agent-runs"
    python send_agent_metrics.py
"""

import json
import os
import time
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone

ENDPOINT = os.environ.get("AGENT_METRICS_ENDPOINT")
if not ENDPOINT:
    raise SystemExit("Set AGENT_METRICS_ENDPOINT environment variable first")

# --- Simulate agent work ---
start = time.time()
items_discovered = 10
items_succeeded = 8
items_failed = 2
token_usage = 4200
api_calls = 6
# ----------------------------

now = datetime.now(timezone.utc)
run_id = f"example_agent_{uuid.uuid4().hex[:8]}"

payload = {
    "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z",
    "agent_name": "Docs Translator",
    "agent_owner": "Vladimir Litvinchik",
    "job_type": "test",
    "run_id": run_id,
    "status": "success",
    "product": "GroupDocs.Total",
    "platform": "All",
    "website": "groupdocs.com",
    "website_section": "Blog",
    "item_name": "Translation",
    "items_discovered": items_discovered,
    "items_failed": items_failed,
    "items_succeeded": items_succeeded,
    "run_duration_ms": int((time.time() - start) * 1000),
    "token_usage": token_usage,
    "api_calls_count": api_calls,
}

data = json.dumps(payload, indent=2)
print(f"Sending metrics to {ENDPOINT}\n{data}\n")

req = urllib.request.Request(
    ENDPOINT,
    data=data.encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"Success: {resp.status} (run_id: {run_id})")
except (urllib.error.URLError, urllib.error.HTTPError) as e:
    print(f"Failed: {e}")
