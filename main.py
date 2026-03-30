"""
main.py  —  Papilio AI Market Entry Intelligence Engine
---------------------------------------------------
Orchestrates: data fetch → prompt build → AI analysis → structured print

Usage:
    python main.py                      # full Turkey / Hensoldt example
    python main.py --quick TR           # quick single-country snapshot
    python main.py --country IN         # full analysis, India
    python main.py --country SA --mode Acquisition
"""

import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

from data_fetch import get_country_profile, format_for_prompt
from ai_engine import generate_insight, generate_quick_insight


# ── Default configuration ──────────────────────────────────────────────────────

DEFAULT = {
    "country_code": "TR",
    "company":      "Hensoldt AG",
    "sector":       "Radar & Electronic Warfare",
    "target_market":"Turkey",
    "entry_mode":   "Joint Venture",
    "rationale": (
        "Hensoldt is evaluating a joint venture with a Turkish defense electronics firm "
        "to access the SSB procurement pipeline, including the KAAN 5th-generation fighter "
        "avionics program. Turkey's 75% domestic content mandate by 2030 creates a structural "
        "requirement for local production partnerships by international defense suppliers."
    ),
}


# ── Formatting helpers ─────────────────────────────────────────────────────────

SEP  = "=" * 68
SEP2 = "-" * 68


def line(char="=", w=68):
    print(char * w)


def header():
    line()
    print("  Papilio AI  —  Market Entry Intelligence Engine")
    print("  Model : gpt-4o-mini  |  Data: World Bank Open API")
    print("  Rule  : every number sourced · no invented data")
    line()
    print()


def print_structured_output(result: dict, config: dict):
    """Renders the structured AI output dict as readable console output."""

    line()
    print(f"  CASE   : {config['company']}  →  {config['target_market']}")
    print(f"  SECTOR : {config['sector']}")
    print(f"  MODE   : {config['entry_mode']}")
    line()
    print()

    # ── Market Context ──
    mc = result.get("market_context", {})
    print("MARKET CONTEXT")
    print(SEP2)
    print(mc.get("insight", "Not available"))
    if mc.get("value") and mc.get("year") and mc.get("source"):
        print(f"\n  Key figure : {mc['value']}  ({mc['year']})")
        print(f"  Source     : {mc['source']}")
    print()

    # ── Entry Rationale ──
    er = result.get("entry_rationale", {})
    print("ENTRY RATIONALE")
    print(SEP2)
    print(er.get("insight", "Not available"))
    if er.get("implication"):
        print(f"\n  Implication: {er['implication']}")
    print()

    # ── Key Risks ──
    risks = result.get("key_risks", [])
    print("KEY RISKS")
    print(SEP2)
    if risks:
        for i, r in enumerate(risks, 1):
            severity = r.get("severity", "?")
            sev_tag = f"[{severity.upper()}]"
            print(f"  {i}. {sev_tag} {r.get('risk', 'Unknown risk')}")
            print(f"     {r.get('evidence', 'No evidence provided')}")
    else:
        print("  No risks identified (check data coverage)")
    print()

    # ── Data Gaps ──
    gaps = result.get("data_gaps", [])
    print("DATA GAPS")
    print(SEP2)
    if gaps:
        for g in gaps:
            print(f"  • {g}")
    else:
        print("  None — full data coverage")
    print()

    # ── Sources ──
    sources = result.get("sources_used", [])
    print("SOURCES USED")
    print(SEP2)
    if sources:
        for s in sources:
            print(f"  • {s}")
    else:
        print("  (none listed)")
    print()

    # ── Hallucination check ──
    hc = result.get("hallucination_check", "")
    print("HALLUCINATION GUARD")
    print(SEP2)
    print(f"  {hc}")
    print()

    # ── Error signal ──
    if "_error" in result:
        print("ERROR")
        print(SEP2)
        print(f"  {result['_error']}")
        print()

    line()
    print("  All figures sourced from World Bank Open Data API.")
    print("  Structured output is machine-readable JSON internally.")
    line()


# ── Pipeline functions ─────────────────────────────────────────────────────────

def run_full_analysis(config: dict):
    header()
    print(f"  Running full analysis: {config['company']} → {config['target_market']}\n")

    # Step 1: Fetch
    print("STEP 1 / 3  —  Fetching live data from World Bank API")
    print(SEP2)
    profile = get_country_profile(config["country_code"], verbose=True)
    data_block = format_for_prompt(profile)

    print("Data block preview (first 600 chars):")
    print(SEP2)
    print(data_block[:600])
    print("  ...")
    print()

    # Step 2: AI
    print("STEP 2 / 3  —  Sending to GPT-4o-mini (hallucination guard ON)")
    print(SEP2)
    print("  temperature : 0.1  (near-deterministic)")
    print("  response    : JSON (enforced by API parameter)")
    print("  instruction : cite every number · no external knowledge")
    print()

    result = generate_insight(
        data_block    = data_block,
        company       = config["company"],
        sector        = config["sector"],
        target_market = config["target_market"],
        entry_mode    = config["entry_mode"],
        rationale     = config["rationale"],
    )

    # Step 3: Output
    print("STEP 3 / 3  —  Structured output")
    print()
    print_structured_output(result, config)

    # Also save JSON to file
    out_file = f"papilio_output_{config['country_code'].lower()}.json"
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({
                "config":  config,
                "profile": {
                    "country_code":    profile["country_code"],
                    "retrieved_at":    profile["retrieved_at"],
                    "available_count": profile["available_count"],
                },
                "result": result,
            }, f, indent=2, ensure_ascii=False)
        print(f"\n  JSON output saved to: {out_file}")
    except OSError as e:
        print(f"\n  (Could not save JSON: {e})")


def run_quick_test(country_code: str):
    header()
    print(f"  Quick snapshot: {country_code.upper()}\n")

    print("Fetching data ...")
    print(SEP2)
    profile = get_country_profile(country_code, verbose=True)
    data_block = format_for_prompt(profile)

    print("Sending to GPT-4o-mini ...")
    result = generate_quick_insight(data_block, country_code.upper())

    print()
    line()
    mc = result.get("market_context", {})
    print(mc.get("insight", "No insight returned"))
    if mc.get("value"):
        print(f"\n  Key figure : {mc['value']}  ({mc.get('year', '?')})")
        print(f"  Source     : {mc.get('source', '?')}")
    line()


def check_env():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or key.startswith("sk-proj-your"):
        print("ERROR: OPENAI_API_KEY not configured.")
        print("  1. Open .env")
        print("  2. Set OPENAI_API_KEY=sk-proj-...")
        print("  Get your key at: https://platform.openai.com/api-keys")
        sys.exit(1)


def parse_args() -> dict:
    """Minimal argument parser — no external dependencies."""
    args = sys.argv[1:]
    config = DEFAULT.copy()

    if "--quick" in args:
        idx = args.index("--quick")
        cc = args[idx + 1] if idx + 1 < len(args) else "TR"
        return {"_mode": "quick", "country_code": cc}

    if "--country" in args:
        idx = args.index("--country")
        config["country_code"] = args[idx + 1] if idx + 1 < len(args) else "TR"
        config["target_market"] = config["country_code"]

    if "--mode" in args:
        idx = args.index("--mode")
        config["entry_mode"] = args[idx + 1] if idx + 1 < len(args) else "Joint Venture"

    if "--company" in args:
        idx = args.index("--company")
        config["company"] = args[idx + 1] if idx + 1 < len(args) else DEFAULT["company"]

    config["_mode"] = "full"
    return config


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    check_env()
    config = parse_args()

    if config.get("_mode") == "quick":
        run_quick_test(config["country_code"])
    else:
        run_full_analysis(config)
