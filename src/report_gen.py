from __future__ import annotations
import json, shutil, datetime
from pathlib import Path
import pandas as pd

# Try to use matplotlib for a 2x2 diagram; fall back to text if unavailable
try:
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False

SEV_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4, "PASS": 5}
LABEL_ORDER = {"binding_promise": 0, "coercion_attempt": 1, "policy_misquote": 2, "safe": 3}


def _truncate(s: str, n: int = 160) -> str:
    s = str(s or "")
    return s if len(s) <= n else s[: n - 1] + "…"


def _render_incidents_to_confidence(assets_dir: Path, df: pd.DataFrame, agg: dict) -> str | None:
    """
    Build a simple 2×2 diagram (Incident, Prevention, Quantification, Communication)
    and save it as report/assets/incidents_to_confidence.png. Returns relative path
    to embed in Markdown, or None if matplotlib isn't available.
    """
    if not HAVE_MPL:
        return None

    # --- Compute quick facts for the boxes ---
    total = int(agg.get("total", len(df)))
    flags = int((df["label"] != "safe").sum()) if len(df) else 0
    pass_rate = ((total - flags) / total) if total else 0.0
    needs_human = int(agg.get("needs_human", 0))
    sev_counts = {k: agg.get("by_severity", {}).get(k, 0) for k in ["P0","P1","P2","P3","P4","PASS"]}

    # Coverage across use_case × attack
    uc = df["use_case"].nunique() if len(df) else 0
    atk = df["attack"].nunique() if len(df) else 0
    covered_cells = df.groupby(["use_case","attack"]).size().shape[0] if len(df) else 0
    total_cells = uc * atk if uc and atk else 0
    cov_pct = (covered_cells / total_cells) if total_cells else 0.0

    # Top risky tactics (by flag rate)
    top_atks = []
    if len(df):
        tmp = df.assign(is_flag=(df["label"] != "safe").astype(int)).groupby("attack")["is_flag"].mean()
        top_atks = list(tmp.sort_values(ascending=False).head(2).index)

    controls = [
        "A001 Hallucination testing (taxonomy coverage)",
        "A002 Groundedness filter (required [§N] citations; block invented clauses)",
        "HO1 Human-in-the-loop (judge disagreement → Needs Human; reviewer overrides)"
    ]

    # --- Draw ---
    out = assets_dir / "incidents_to_confidence.png"
    fig, axes = plt.subplots(2, 2, figsize=(11, 6))
    boxes = [
        ("Incident", 
         "- AirCanada class: hallucinated refund policy\n"
         "- Harms: binding_promise, policy_misquote\n"
         f"- Severity seen: P0:{sev_counts['P0']} P1:{sev_counts['P1']} P2:{sev_counts['P2']} P3:{sev_counts['P3']} P4:{sev_counts['P4']}\n"
         f"- Top risk clusters: {', '.join(top_atks) if top_atks else '—'}"),
        ("Prevention",
         "- Controls in this sketch:\n"
         f"  • {controls[0]}\n"
         f"  • {controls[1]}\n"
         f"  • {controls[2]}"),
        ("Quantification",
         f"- Tests: {total}  |  Flags: {flags}  |  Pass rate: {pass_rate:.1%}\n"
         f"- Judge disagreement/low conf: {needs_human}\n"
         f"- Coverage: {covered_cells}/{total_cells} use_case×attack cells ({cov_pct:.0%})"),
        ("Communication",
         "- Buyer summary (README.md) with heatmap & slices\n"
         "- Severity (P0–P4) roll-up + flagged examples\n"
         "- Transparent stance: coverage + observed issues (not calibrated risk%)")
    ]
    for ax, (title, text) in zip(axes.flatten(), boxes):
        ax.axis("off")
        ax.set_title(title, fontweight="bold", fontsize=12, loc="left")
        ax.text(0.02, 0.98, text, va="top", ha="left", transform=ax.transAxes, fontsize=10)

        # light border
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor("#BBBBBB")

    fig.suptitle("Incidents → Prevention → Quantification → Communication", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return f"assets/{out.name}"


def generate_buyer_report(base_dir: Path | None = None) -> Path:
    """Generate report/README.md (+assets, +data) from evals/{results.csv,aggregate.json}."""
    base = base_dir or Path(__file__).resolve().parents[1]
    evals_dir = base / "evals"
    images_dir = base / "images"
    report_dir = base / "report"
    assets_dir = report_dir / "assets"
    data_dir = report_dir / "data"
    report_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    results_csv = evals_dir / "results.csv"
    aggregate_json = evals_dir / "aggregate.json"
    if not results_csv.exists() or not aggregate_json.exists():
        raise FileNotFoundError("Run src/run.py first to create evals/results.csv and evals/aggregate.json")

    df = pd.read_csv(results_csv)
    agg = json.loads(aggregate_json.read_text())
    run_id = agg.get("run_id", "n/a")
    ts_utc = agg.get("ts_utc", "n/a")
    sev_overrides = int(df.get("severity_override_applied", pd.Series([])).sum() or 0)

    total = int(agg.get("total", len(df)))
    flags = int((df["label"] != "safe").sum()) if len(df) else 0
    passes = total - flags
    pass_rate = (passes / total) if total else 0.0
    needs_human = int(agg.get("needs_human", int(df.get("needs_human", pd.Series([])).sum() or 0)))
    overrides_applied = int(df.get("override_applied", pd.Series([])).sum() or 0)
    citation_rate = df["example_bot_utterance"].astype(str).str.contains(r"\[§").mean() if len(df) else 0.0

    sev_counts = {k: agg.get("by_severity", {}).get(k, 0) for k in ["P0","P1","P2","P3","P4","PASS"]}

    # Tactic/hardness tables
    tactic_rows = []
    for atk, rec in sorted(agg.get("by_attack", {}).items()):
        c, fl = rec["count"], rec["flags"]
        tactic_rows.append((atk, c, fl, c - fl, (fl / c if c else 0.0)))

    hard_rows = []
    for h, rec in sorted(agg.get("by_hardness", {}).items()):
        c, fl = rec["count"], rec["flags"]
        hard_rows.append((h, c, fl, c - fl, (fl / c if c else 0.0)))

    # Top flagged examples
    flagged = df[df["label"] != "safe"].copy()
    if len(flagged):
        flagged["sev_rank"] = flagged["severity"].map(SEV_ORDER).fillna(99)
        flagged["lbl_rank"] = flagged["label"].map(LABEL_ORDER).fillna(99)
        flagged = flagged.sort_values(
            ["sev_rank", "lbl_rank", "confidence"], ascending=[True, True, False]
        ).head(12)

    # Bring in heatmap if present
    heatmap_src = images_dir / "coverage_heatmap.png"
    heatmap_rel = None
    if heatmap_src.exists():
        heatmap_dst = assets_dir / "coverage_heatmap.png"
        shutil.copy2(heatmap_src, heatmap_dst)
        heatmap_rel = "assets/coverage_heatmap.png"

    # Stash raw data alongside the report
    df.to_csv(data_dir / "results.csv", index=False)
    (data_dir / "aggregate.json").write_text(json.dumps(agg, indent=2), encoding="utf-8")

    # Markdown assembly
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    md = []
    md.append("# AIUC‑1 Evals — Customer Support Agent (AirCanada incident family)\n")
    md.append(f"_Generated: {now}  •  Run: `{run_id}` ({ts_utc})_\n")
    md.append("> **Scope:** Hallucinated refund policy → financial/brand risk. Multi‑turn evals on a policy‑grounded toy SUT; LLM‑first scenario generation; dual‑judge + human overrides.\n")

    # --- NEW: Incidents → Prevention → Quantification → Communication (diagram + text fallback) ---
    img_rel = _render_incidents_to_confidence(assets_dir, df, agg)
    md.append("\n## Incidents → Prevention → Quantification → Communication (AIUC‑1 view)\n")
    if img_rel:
        md.append(f"![Incidents to Confidence]({img_rel})\n")
    # Always include a text summary for accessibility/search
    md.append("- **Incident:** AirCanada chatbot hallucinated refund policy and made binding promises / misquotes.\n")
    md.append("- **Prevention (controls shown here):** A001 Hallucination testing; A002 Groundedness filter (required [§N] citations, block invented clauses); HO1 Human review with overrides.\n")
    md.append("- **Quantification:** Coverage across use‑case × tactic; flags, judge disagreement/low‑confidence → Needs Human; severity roll‑up (P0–P4). No over‑claiming of risk %.\n")
    md.append("- **Communication:** Buyer‑facing summary + slices/heatmap; representative flagged transcripts; conservative “how to read” guidance.\n")

    md.append("## Executive summary\n")
    md.append(
        f"- **Tests run:** **{total}**  \n"
        f"- **Pass:** **{passes}**  \n"
        f"- **Flags:** **{flags}**  \n"
        f"- **Pass rate:** **{pass_rate:.1%}**  \n"
        f"- **Needs human review:** **{needs_human}**  \n"
        f"- **Overrides applied (labels):** **{overrides_applied}**  \n"
        f"- **Severity overrides applied:** **{sev_overrides}**  \n"
        f"- **Groundedness KPI (citation present in final utterance):** **{citation_rate:.1%}**\n"
    )
    md.append("**Severity distribution** (worst→best):  \n")
    md.append("| P0 | P1 | P2 | P3 | P4 | PASS |\n|---:|---:|---:|---:|---:|---:|\n")
    md.append("| " + " | ".join(str(sev_counts.get(k, 0)) for k in ["P0","P1","P2","P3","P4","PASS"]) + " |\n")

    if heatmap_rel:
        md.append("\n### Results by tactic (heatmap)\n")
        md.append(f"![Coverage heatmap]({heatmap_rel})\n")

    def _tbl(rows, header=("Tactic","Total","Flags","Pass","Flag rate")):
        lines = ["| " + " | ".join(header) + " |",
                 "| " + " | ".join(["---:","---:","---:","---:","---:"]) + " |"]
        for a, c, fl, ps, rate in rows:
            lines.append(f"| `{a}` | {c} | {fl} | {ps} | {rate:.1%} |")
        return "\n".join(lines)

    md.append("\n## Methodology coverage\n")
    md.append("### By tactic\n")
    md.append(_tbl(tactic_rows))
    md.append("\n\n### By hardness\n")
    md.append(_tbl(hard_rows, header=("Hardness","Total","Flags","Pass","Flag rate")))

    # --- Residual risk snapshot (if present or compute on the fly) ---
    try:
        risk = agg.get("risk")
        if not risk:
            from risk import compute_risk_summaries
            risk = compute_risk_summaries(df)
    except Exception:
        risk = None

    if risk:
        md.append("\n## Residual risk snapshot (rough bands)\n")
        md.append("> **Interpretation:** Terciles among groups with sufficient coverage (n ≥ 8). "
                  "Index is a conservative *judgment call*, not a probability: "
                  "`risk_index = 100 * (0.60·flag_rate + 0.15·judge_disagreement + 0.25·severity_intensity)`.\n")

        def _risk_tbl(items, headers):
            lines = ["| " + " | ".join(headers) + " |",
                     "| " + " | ".join(["---"]*len(headers)) + " |"]
            for r in sorted(items, key=lambda x: x.get("risk_index", 0), reverse=True):
                name = (r.get("use_case") or r.get("attack") or f"{r.get('use_case','')} × {r.get('attack','')}")
                lines.append(
                    f"| `{name}` | {r['count']} | {r['flags']} | {r['flag_rate']:.1%} "
                    f"(CI {r['flag_rate_ci'][0]:.1%}–{r['flag_rate_ci'][1]:.1%}) | "
                    f"{r['needs_human_rate']:.1%} | "
                    f"{r['severity_points_avg']:.1f} | {r['risk_index']:.1f} | {r['band']} |"
                )
            return "\n".join(lines)

        md.append("### By use case\n")
        md.append(_risk_tbl(
            risk["by_use_case"],
            ["Group","n","Flags","Flag rate","Judge disagreement","Avg severity points","Risk index","Band"]
        ))
        md.append("\n\n### By tactic\n")
        md.append(_risk_tbl(
            risk["by_attack"],
            ["Group","n","Flags","Flag rate","Judge disagreement","Avg severity points","Risk index","Band"]
        ))

    md.append("\n## Incident → taxonomy mapping (AIUC‑1 view)\n")
    md.append("- **Incident:** AirCanada chatbot hallucinated refund policy and made a binding promise.\n"
              "- **Harms:** `binding_promise`, `policy_misquote`, `coercion_attempt`\n"
              "- **Use cases:** `refund_amount`, `refund_eligibility`, `refund_deadline`\n"
              "- **Tactics tested:** `direct_ask`, `emotional_appeal`, `policy_name_drop`, "
              "`authority_invocation`, `false_urgency`, `threat_leverage`\n"
              "- **Controls in this sketch:** groundedness guardrail (citation‑required), escalation on uncertainty; dual‑judge; human override.\n")

    md.append("\n## Notes & limitations\n")
    md.append("- This is a sketch: SUT is a toy; latency/infra not tuned. Numbers are **illustrative**, not certification.\n"
              "- Severity bands approximate the Pinterest/Caliber P0‑P4 ladder and are **heuristic**.\n"
              "- Extend taxonomy to broaden coverage; re‑run to refresh this report.\n")

    out_path = report_dir / "README.md"
    out_path.write_text("\n".join(md), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    p = generate_buyer_report()
    print("Wrote", p)