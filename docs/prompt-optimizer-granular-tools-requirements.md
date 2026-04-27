# Prompt Optimizer Agent: Granular Tools Requirements

## Problem

The current `optimize_prompt` MCP tool runs all optimization iterations (default: 10) in a single blocking call. This takes 30–60 minutes and creates several issues:

- **Timeouts**: Claude Code MCP calls have practical time limits; the tool frequently times out.
- **No visibility**: The caller (Claude) and the user see nothing until the entire run finishes or fails.
- **No steering**: Claude cannot reason about intermediate results, stop early when the score plateaus, or adjust strategy mid-run.
- **Wasted compute**: If iteration 3 already scores 0.95, the remaining 7 iterations are wasted.

## Goal

Expose **granular primitive tools** so that Claude (or any MCP client) can orchestrate the optimization loop externally, one step at a time. Each tool call should complete in **under 5 minutes**.

## Current API Surface (keep as-is)

| Tool | Purpose | Keep? |
|------|---------|-------|
| `optimize_prompt` | Monolithic: runs full loop internally | Yes — keep for non-interactive / CI use |
| `evaluate_single_prompt` | Score a prompt once, return scores + feedback | Yes — already granular, this is the "judge" step |
| `list_examples` | List bundled example configs | Yes |
| `get_example` | Load an example config as YAML | Yes |

## New Tools to Add

### 1. `create_session`

Initialize an optimization session with configuration. Returns a session ID and baseline evaluation.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task` | string | yes | Plain English description of what the prompt should accomplish |
| `system_prompt` | string | yes | The system message for the LLM |
| `user_prompt` | string | yes | The user message template. Must contain `{input}` placeholder |
| `evaluation_criteria` | string | yes | Multi-line text describing what constitutes good output |
| `test_inputs` | array[object] | yes | Test cases. Each dict must have `input` key, optionally `reference` and `name` |
| `output_format` | string | no | Expected output format: `plain`, `markdown`, `json`, or `code`. Default: `plain` |
| `temperature` | number | no | LLM temperature for generation. Default: `0.3` |

**Returns (JSON):**

```json
{
  "session_id": "sess_abc123",
  "baseline_score": {
    "composite": 0.52,
    "structural": 0.60,
    "judge_avg": 0.45,
    "feedback": ["Missing section headings", "Included YAML front matter"]
  },
  "current_prompt": {
    "system_prompt": "...",
    "user_prompt": "..."
  },
  "config": {
    "test_inputs_count": 1,
    "output_format": "markdown"
  }
}
```

**Behavior:**
1. Store session config (task, criteria, test_inputs, output_format, temperature) in server memory, keyed by `session_id`.
2. Run the baseline evaluation (equivalent to `evaluate_single_prompt`) with the provided prompts.
3. Return the session ID, baseline score, and the current prompts.

**Session storage:** In-memory dict is fine. Sessions expire after 2 hours of inactivity. No persistence needed.

---

### 2. `propose_improvement`

Given a session ID and the judge feedback from the last evaluation, propose an improved version of the prompt.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | yes | Session ID from `create_session` |
| `feedback` | string | yes | Judge feedback from the last `evaluate_single_prompt` or `create_session` baseline |
| `strategy_hint` | string | no | Optional hint from the caller about what to try (e.g., "focus on fixing the front matter leakage", "try adding explicit section ordering") |

**Returns (JSON):**

```json
{
  "proposed_system_prompt": "...",
  "proposed_user_prompt": "...",
  "changes_description": "Added explicit instruction to not output YAML front matter. Restructured instructions into numbered list.",
  "iteration": 3
}
```

**Behavior:**
1. Load session config by `session_id`.
2. Use the internal "improver" model (the same one `optimize_prompt` uses internally) to generate a new prompt variant based on the feedback and optional strategy hint.
3. Track the iteration number in the session.
4. Return the proposed prompts and a human-readable description of what changed.

**Important:** This tool does NOT evaluate the proposal. The caller should use `evaluate_single_prompt` (or the new `evaluate_in_session`) for that, then decide whether to accept or reject.

---

### 3. `evaluate_in_session`

Evaluate a prompt candidate within a session context. Thin wrapper around `evaluate_single_prompt` that uses session-stored test inputs and criteria.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | yes | Session ID from `create_session` |
| `system_prompt` | string | yes | System prompt to evaluate |
| `user_prompt` | string | yes | User prompt to evaluate (must contain `{input}`) |

**Returns (JSON):**

```json
{
  "composite": 0.78,
  "structural": 0.85,
  "judge_avg": 0.72,
  "feedback": ["Links section is complete", "Missing performance data from release notes"],
  "vs_baseline": "+0.26",
  "vs_previous": "+0.08",
  "iteration": 3
}
```

**Behavior:**
1. Load session config (test_inputs, evaluation_criteria, output_format, temperature) by `session_id`.
2. Run `evaluate_single_prompt` logic with the provided prompts against session test inputs.
3. Compare score to baseline and previous best, include deltas in the response.
4. If this is the new best, store it in the session as `best_prompt`.

**Why this tool exists:** Avoids the caller having to re-send `test_inputs`, `evaluation_criteria`, and `output_format` on every evaluation call. These are session-level constants.

---

### 4. `accept_improvement`

Accept a proposed improvement as the new current prompt in the session.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | yes | Session ID |
| `system_prompt` | string | yes | The accepted system prompt |
| `user_prompt` | string | yes | The accepted user prompt |

**Returns (JSON):**

```json
{
  "accepted": true,
  "iteration": 3,
  "current_score": 0.78,
  "best_score": 0.78,
  "history": [
    {"iteration": 0, "score": 0.52, "action": "baseline"},
    {"iteration": 1, "score": 0.61, "action": "accepted"},
    {"iteration": 2, "score": 0.55, "action": "rejected"},
    {"iteration": 3, "score": 0.78, "action": "accepted"}
  ]
}
```

---

### 5. `get_session_result`

Get the final result of a session: the best prompt found, its score, and a summary of the optimization history.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | yes | Session ID |

**Returns (JSON):**

```json
{
  "best_prompt": {
    "system_prompt": "...",
    "user_prompt": "..."
  },
  "best_score": {
    "composite": 0.78,
    "structural": 0.85,
    "judge_avg": 0.72
  },
  "baseline_score": {
    "composite": 0.52
  },
  "improvement": "+50%",
  "total_iterations": 5,
  "accepted_iterations": 3,
  "rejected_iterations": 2,
  "history": [...]
}
```

---

## Expected Orchestration Flow (Claude's perspective)

```
1. create_session(task, prompts, criteria, test_inputs)
   → Get session_id, baseline score (0.52), feedback

2. Loop:
   a. propose_improvement(session_id, feedback)
      → Get proposed prompts + changes description

   b. evaluate_in_session(session_id, proposed_prompts)
      → Get score (0.61), new feedback

   c. If score improved:
        accept_improvement(session_id, proposed_prompts)
        → Update current prompt
      Else:
        Skip (don't accept), use feedback for next proposal

   d. If score > 0.9 or plateaued for 3 iterations: break

3. get_session_result(session_id)
   → Get best prompt + report
```

Each step takes 2–5 minutes. Claude sees every score, can explain progress to the user, and can stop early or adjust strategy.

## Implementation Notes

### Session Storage

```python
# Simple in-memory dict, no persistence needed
sessions: dict[str, SessionState] = {}

@dataclass
class SessionState:
    session_id: str
    task: str
    evaluation_criteria: str
    test_inputs: list[dict]
    output_format: str
    temperature: float
    current_system_prompt: str
    current_user_prompt: str
    best_system_prompt: str
    best_user_prompt: str
    baseline_score: float
    best_score: float
    iteration: int
    history: list[dict]
    last_activity: datetime  # for expiration
```

### Reuse Internal Logic

The new tools should reuse the same internal functions that `optimize_prompt` already uses:
- `evaluate_single_prompt` logic → `evaluate_in_session`
- The "improver" / prompt-rewriting logic → `propose_improvement`
- The model pairing / judge logic → stays internal

### Backward Compatibility

- `optimize_prompt` continues to work exactly as before (it can internally use the new primitives if desired).
- `evaluate_single_prompt` stays unchanged.

### Error Handling

- `session_id` not found → return `{"error": "Session not found or expired"}`
- Session expired (>2h inactive) → same error
- Invalid `{input}` placeholder missing → return `{"error": "user_prompt must contain {input} placeholder"}`

## Non-Goals

- No persistence across server restarts (in-memory is fine)
- No concurrent session limits (trust the caller)
- No authentication (MCP server is local)
- No streaming / SSE progress within a single tool call
