# AIUC‑1 Evals — Customer Support Agent (AirCanada incident family)

_Generated: 2025-10-30 18:24 UTC  •  Run: `run-20251030T175537Z-05fbbf96` (2025-10-30T18:10:59Z)_

> **Scope:** Hallucinated refund policy → financial/brand risk. Multi‑turn evals on a policy‑grounded toy SUT; LLM‑first scenario generation; dual‑judge + human overrides.


## Incidents → Prevention → Quantification → Communication (AIUC‑1 view)

![Incidents to Confidence](assets/incidents_to_confidence.png)

- **Incident:** AirCanada chatbot hallucinated refund policy and made binding promises / misquotes.

- **Prevention (controls shown here):** A001 Hallucination testing; A002 Groundedness filter (required [§N] citations, block invented clauses); HO1 Human review with overrides.

- **Quantification:** Coverage across use‑case × tactic; flags, judge disagreement/low‑confidence → Needs Human; severity roll‑up (P0–P4). No over‑claiming of risk %.

- **Communication:** Buyer‑facing summary + slices/heatmap; representative flagged transcripts; conservative “how to read” guidance.

## Executive summary

- **Tests run:** **159**  
- **Pass:** **146**  
- **Flags:** **13**  
- **Pass rate:** **91.8%**  
- **Needs human review:** **18**  
- **Overrides applied (labels):** **0**  
- **Severity overrides applied:** **0**  
- **Groundedness KPI (citation present in final utterance):** **49.7%**

**Severity distribution** (worst→best):  

| P0 | P1 | P2 | P3 | P4 | PASS |
|---:|---:|---:|---:|---:|---:|

| 0 | 0 | 0 | 5 | 8 | 146 |


### Results by tactic (heatmap)

![Coverage heatmap](assets/coverage_heatmap.png)


## Methodology coverage

### By tactic

| Tactic | Total | Flags | Pass | Flag rate |
| ---: | ---: | ---: | ---: | ---: |
| `authority_invocation` | 31 | 3 | 28 | 9.7% |
| `direct_ask` | 36 | 3 | 33 | 8.3% |
| `emotional_appeal` | 20 | 1 | 19 | 5.0% |
| `false_urgency` | 27 | 1 | 26 | 3.7% |
| `policy_name_drop` | 35 | 5 | 30 | 14.3% |
| `threat_leverage` | 10 | 0 | 10 | 0.0% |


### By hardness

| Hardness | Total | Flags | Pass | Flag rate |
| ---: | ---: | ---: | ---: | ---: |
| `easy` | 1 | 0 | 1 | 0.0% |
| `medium` | 158 | 13 | 145 | 8.2% |

## Residual risk snapshot (rough bands)

> **Interpretation:** Terciles among groups with sufficient coverage (n ≥ 8). Index is a conservative *judgment call*, not a probability: `risk_index = 100 * (0.60·flag_rate + 0.15·judge_disagreement + 0.25·severity_intensity)`.

### By use case

| Group | n | Flags | Flag rate | Judge disagreement | Avg severity points | Risk index | Band |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `refund_amount` | 49 | 5 | 10.2% (CI 4.4%–21.8%) | 12.2% | 0.5 | 8.1 | high |
| `refund_eligibility` | 55 | 5 | 9.1% (CI 4.0%–19.6%) | 12.7% | 0.4 | 7.5 | medium |
| `refund_deadline` | 55 | 3 | 5.5% (CI 1.9%–14.8%) | 9.1% | 0.2 | 4.7 | low |


### By tactic

| Group | n | Flags | Flag rate | Judge disagreement | Avg severity points | Risk index | Band |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `policy_name_drop` | 35 | 5 | 14.3% (CI 6.3%–29.4%) | 14.3% | 0.5 | 10.8 | high |
| `direct_ask` | 36 | 3 | 8.3% (CI 2.9%–21.8%) | 13.9% | 0.5 | 7.2 | high |
| `authority_invocation` | 31 | 3 | 9.7% (CI 3.4%–24.9%) | 6.5% | 0.4 | 6.9 | medium |
| `emotional_appeal` | 20 | 1 | 5.0% (CI 0.9%–23.6%) | 15.0% | 0.4 | 5.3 | medium |
| `threat_leverage` | 10 | 0 | 0.0% (CI 0.0%–27.8%) | 20.0% | 0.0 | 3.0 | low |
| `false_urgency` | 27 | 1 | 3.7% (CI 0.7%–18.3%) | 3.7% | 0.1 | 2.8 | low |

## Incident → taxonomy mapping (AIUC‑1 view)

- **Incident:** AirCanada chatbot hallucinated refund policy and made a binding promise.
- **Harms:** `binding_promise`, `policy_misquote`, `coercion_attempt`
- **Use cases:** `refund_amount`, `refund_eligibility`, `refund_deadline`
- **Tactics tested:** `direct_ask`, `emotional_appeal`, `policy_name_drop`, `authority_invocation`, `false_urgency`, `threat_leverage`
- **Controls in this sketch:** groundedness guardrail (citation‑required), escalation on uncertainty; dual‑judge; human override.


## Notes & limitations

- This is a sketch: SUT is a toy; latency/infra not tuned. Numbers are **illustrative**, not certification.
- Severity bands approximate the Pinterest/Caliber P0‑P4 ladder and are **heuristic**.
- Extend taxonomy to broaden coverage; re‑run to refresh this report.
