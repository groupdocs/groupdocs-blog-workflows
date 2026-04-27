# Prompt Optimizer Agent: Improvement Proposals

## Session History

Two optimization sessions were conducted on the same task (release blog post prompt) to validate improvements.

### Session 1 — Before improvements (original granular tools only)
- 5 iterations, 2 accepted / 3 rejected
- Best judge score: 3.775 (+16.2% from baseline 3.25)
- Output quality: truncated — missing "How to get the update" and "Resources" sections
- Key blocker: no way to correct persistent judge false positives, no visibility into actual output

### Session 2 — After improvements (`provide_feedback` + `generated_outputs`)
- 3 iterations, 1 accepted / 2 rejected
- Best judge score: 3.775 (same — judge is the ceiling)
- Output quality: **complete** — all sections present, correct version changes, proper Resources format, 214 tokens
- Key difference: `provide_feedback` corrected the judge's false "truncated input" claim; `generated_outputs` let the orchestrator verify output quality directly

### Comparison

| Metric | Session 1 | Session 2 | Impact |
|--------|:---------:|:---------:|--------|
| Iterations to best judge score | 2 | 1 | 50% fewer iterations |
| Total iterations needed | 5 | 3 | 40% faster convergence |
| All sections present in output | No | **Yes** | Truncation solved |
| Correct Resources format | No | **Yes** | `provide_feedback` hint worked |
| Direct download handled | Duplicated NuGet link | **Correctly omitted** | Prompt fix from output inspection |
| Output tokens | Truncated | 214 (complete) | Removing example template freed budget |

---

## Problems Observed

### Solved in Session 2

#### 1. No way to feed caller insights back to the optimizer
**Status: SOLVED** via `provide_feedback` tool.

Claude could see the judge was wrong about "truncated HTML input" and that the real bottleneck was worker model output length. With `provide_feedback(correction)`, the optimizer stopped chasing phantom issues. With `provide_feedback(ceiling)`, it focused on making the prompt shorter instead of adding more instructions.

#### 2. No output inspection
**Status: SOLVED** via `generated_outputs` field in `evaluate_in_session` response.

Seeing the actual 214-token output let Claude diagnose real issues (duplicated download link, wrong Resources pattern) vs false judge complaints. In session 1, Claude was flying blind.

### Still Open

#### 3. Judge false positives
The judge (`qwen3-next`) consistently claims the HTML input is "truncated at 'GroupD'" when the full table with all 6 rows is present. This dominated every evaluation in both sessions and is the primary reason scores plateau at 3.775. The `provide_feedback(correction)` mitigates this for `propose_improvement`, but it does NOT change the judge's scoring — the composite score remains artificially low.

#### 4. Score plateau at judge ceiling
Both sessions hit 3.775 and couldn't improve further. The iterations 3-5 in session 1 and iterations 2-3 in session 2 were all rejected at the same score. The plateau detection flag (`plateau_detected`) was implemented and works, but the optimizer has no way to escape the ceiling when the judge itself is the bottleneck.

#### 5. No learning across sessions
Session 2 started from scratch. We re-discovered that "removing the example template saves tokens and fixes truncation" — something already proven in session 1. The optimizer should have known this upfront.

#### 6. Judge score ≠ actual quality
Session 2, iteration 3 produced the best actual output (all sections, correct format, complete, 214 tokens) but scored 3.425 — *lower* than iteration 1's 3.775 which had a truncated Resources section. The automated score is misleading. The orchestrator can work around this by inspecting `generated_outputs`, but there should be a mechanism to flag this discrepancy.

---

## Implemented Improvements

### A. Caller Feedback Tool (`provide_feedback`) — DONE

Lets the orchestrator inject observations that override or supplement judge feedback.

```
provide_feedback(session_id, feedback, feedback_type)
```

| Feedback Type | Purpose | Effect on `propose_improvement` |
|---------------|---------|-------------------------------|
| `correction` | Judge was wrong about something | Overrides conflicting judge feedback |
| `hint` | Strategic direction to try | Included as context for improver |
| `constraint` | Hard requirement to preserve | Treated as non-negotiable |
| `ceiling` | Issue can't be fixed by prompt changes | Improver stops trying to fix it |

**Validated impact:** In session 2, two `correction` feedbacks and one `ceiling` feedback led to faster convergence (3 iterations vs 5) and better actual output quality.

### B. Return Generated Output — DONE

`evaluate_in_session` now returns `generated_outputs` with the actual worker model output and `token_count` per test case.

**Validated impact:** Enabled the orchestrator to:
- Catch the duplicated NuGet link in Direct download (invisible to the judge)
- Verify that version changes were correct despite judge claiming they were fabricated
- Confirm output completeness (214 tokens, no truncation)

### C. Plateau Detection — DONE

`propose_improvement` returns `plateau_detected: true` when score hasn't improved for 3 consecutive iterations.

**Validated impact:** Session 2 would have triggered this at iteration 3. In session 1 it would have triggered at iteration 4, saving one wasted iteration.

---

## Remaining Improvements to Implement

### D. Judge Calibration (`calibrate_judge`)

**Priority: P0** — This is now the single biggest blocker. The judge consistently mis-scores good outputs.

Before starting optimization, run a calibration step where the judge evaluates a known-good reference output.

```
calibrate_judge(session_id, reference_output, expected_score_range)
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session_id` | string | yes | Session ID |
| `reference_output` | string | yes | A known-good output that should score high |
| `expected_score_range` | string | yes | e.g., "7-10" — what a human would rate this |

**Returns:**
```json
{
  "judge_score": 4.2,
  "expected_range": "7-10",
  "calibration": "MISALIGNED",
  "recommendation": "Judge is scoring 40-60% below expected. Consider adjusting evaluation criteria or switching judge model.",
  "false_positive_patterns": ["Claims input is truncated when it is not"]
}
```

**Why it's P0 now:** In both sessions, the judge was the ceiling. The `provide_feedback(correction)` workaround helps `propose_improvement` but doesn't fix the score. If we had detected the judge misalignment upfront, we could have:
1. Adjusted the evaluation criteria to avoid triggering the false positive
2. Switched to a different judge model
3. Known that the 3.775 score was actually closer to 7-8 in real quality

**Implementation approach:**
1. Run the judge against the reference output with the session's evaluation criteria
2. Compare the judge's score to the expected range
3. If misaligned, analyze the judge's feedback to detect systematic patterns (e.g., always claiming truncation)
4. Return actionable recommendations

---

### E. Session Learnings Store (`save_session_learnings` / `get_learnings`)

**Priority: P1** — High long-term value, compounds over time.

Persist what worked and what didn't across sessions so the optimizer starts smarter.

**New tools:**

```
save_session_learnings(session_id, learnings)
get_learnings(task_type?)
```

**Learnings from our two sessions that should be persisted:**

```json
{
  "task_type": "release_blog_post",
  "learnings": [
    {
      "type": "strategy_effective",
      "description": "Numbered CRITICAL RULES outperform prose '## Instructions' format",
      "score_delta": "+0.5",
      "sessions": ["sess_2348f67eb0fd", "sess_42ac1c2a5b89"]
    },
    {
      "type": "strategy_effective",
      "description": "Removing example template when worker model has limited output budget frees ~400 input tokens and fixes truncation",
      "score_delta": "N/A (quality improvement, not score)",
      "sessions": ["sess_42ac1c2a5b89"]
    },
    {
      "type": "strategy_effective",
      "description": "Concrete link patterns in OUTPUT STRUCTURE skeleton (e.g. showing exact Resources format) are followed more reliably than abstract rules",
      "sessions": ["sess_42ac1c2a5b89"]
    },
    {
      "type": "strategy_ineffective",
      "description": "Adding an OUTPUT SKELETON while keeping the example template does not help — too many tokens consumed by both",
      "score_delta": "0.0",
      "sessions": ["sess_2348f67eb0fd"]
    },
    {
      "type": "model_limitation",
      "description": "gpt-oss worker model truncates output at ~500 tokens, insufficient for full blog posts with detailed fix descriptions",
      "affected_criteria": ["completeness", "structure"]
    },
    {
      "type": "judge_issue",
      "description": "qwen3-next judge falsely reports HTML table input as truncated when the table is complete. Happens every iteration. Dominates scoring.",
      "frequency": "100% of evaluations in both sessions",
      "workaround": "provide_feedback(correction) mitigates for propose_improvement but does not fix scoring"
    }
  ]
}
```

**Storage:** JSON file on disk, persists across server restarts. Simple append-only log per task type.

**Integration:** `propose_improvement` should automatically consult stored learnings before generating proposals, applying effective strategies and avoiding ineffective ones.

---

### F. Score Override / Quality Flag

**Priority: P1** — New proposal based on session 2 findings.

The orchestrator should be able to flag that the actual output quality disagrees with the judge score, so the session result reflects reality.

**New parameter on `accept_improvement`:**

```
accept_improvement(
    session_id,
    system_prompt,
    user_prompt,
    override_quality="good"  # NEW: "good", "acceptable", "poor"
)
```

**Why:** Session 2, iteration 3 produced the best actual output but scored lower (3.425) than iteration 1 (3.775) which had a worse output. The orchestrator should be able to accept based on quality inspection, not just score. The `override_quality` flag is stored in history so the session result can report both judge score and caller assessment.

**Updated `get_session_result` return:**
```json
{
  "best_by_score": { "iteration": 1, "score": 3.775 },
  "best_by_caller": { "iteration": 3, "score": 3.425, "quality": "good" },
  "recommendation": "Caller-assessed best (iteration 3) differs from score-based best (iteration 1). Consider using the caller-preferred prompt."
}
```

---

## Updated Implementation Priority

| Priority | Improvement | Status | Impact |
|----------|-------------|--------|--------|
| ~~**P0**~~ | ~~A. Caller Feedback (`provide_feedback`)~~ | **DONE** | Validated: faster convergence, better output |
| ~~**P0**~~ | ~~B. Return Generated Output~~ | **DONE** | Validated: enables output-based diagnosis |
| ~~**P1**~~ | ~~C. Plateau Detection~~ | **DONE** | Validated: prevents wasted iterations |
| **P0** | D. Judge Calibration (`calibrate_judge`) | TODO | Now the biggest blocker — judge is the ceiling |
| **P1** | E. Session Learnings Store | TODO | High long-term — compounds over time |
| **P1** | F. Score Override / Quality Flag | TODO | Fixes score ≠ quality discrepancy |

## Updated Orchestration Flow

```
1. create_session(...)
   → Get session_id, baseline score, feedback

2. calibrate_judge(session_id, known_good_output, "7-10")        ← NEW
   → Verify judge is reasonable before investing in iterations
   → If MISALIGNED: adjust criteria or switch model

3. Loop:
   a. propose_improvement(session_id, feedback)
      → Get proposed prompts + plateau_detected flag

   b. IF plateau_detected:
        → provide_feedback(session_id, diagnosis, "correction" or "ceiling")
        → OR break

   c. evaluate_in_session(session_id, proposed_prompts)
      → Get score, feedback, AND generated_outputs

   d. Inspect generated_outputs:                                  ← ENABLED BY B
      → If judge feedback contradicts actual output:
          provide_feedback(session_id, "judge wrong about X", "correction")
      → If output is truncated:
          provide_feedback(session_id, "model output truncation", "ceiling")

   e. If score improved: accept_improvement(...)
      Else if output quality is good despite score:
          accept_improvement(..., override_quality="good")        ← NEW
      Else: reject_improvement(...)

4. save_session_learnings(session_id, distilled_insights)         ← NEW

5. get_session_result(session_id)
   → Get best prompt by score AND by caller assessment
```
