# Papilio AI — Market Entry Intelligence Engine (MVP)

Python-based MVP. Fetches real data from World Bank API, sends it to Claude, returns sourced strategy insights.

**No invented data. No placeholders. Every number has a source.**

---

## File Structure

```
papilio-mvp/
├── main.py           # Orchestrator — run this
├── data_fetch.py     # World Bank API calls
├── ai_engine.py      # Claude reasoning layer
├── requirements.txt  # Dependencies
├── .env.example      # Copy to .env and add your key
└── README.md
```

---

## Setup (3 steps)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API key

```bash
cp .env.example .env
```

Edit `.env` and replace the placeholder with your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-real-key-here
```

Get a key at: https://console.anthropic.com

### 3. Run

```bash
# Full analysis — Hensoldt AG entering Turkey (default example)
python main.py

# Quick test — single GDP insight for any country
python main.py --quick TR
python main.py --quick DE
python main.py --quick IN

# Full analysis for a different country
python main.py --country SA    # Saudi Arabia
python main.py --country PL    # Poland
python main.py --country SG    # Singapore
```

---

## Country Codes (ISO 3166-1 alpha-2)

| Code | Country |
|------|---------|
| TR   | Turkey  |
| DE   | Germany |
| IN   | India   |
| SA   | Saudi Arabia |
| PL   | Poland  |
| SG   | Singapore |
| US   | United States |
| JP   | Japan   |
| BR   | Brazil  |
| ZA   | South Africa |

---

## What the output looks like

```
══════════════════════════════════════════════════════════════════════
  Papilio AI — Market Entry Intelligence Engine  (MVP)
  Data: World Bank Open API | AI: Claude claude-sonnet-4-5
  Rule: Every number is sourced. No invented data.
══════════════════════════════════════════════════════════════════════

  CASE: Hensoldt AG → Turkey (Radar & Electronic Warfare)
  MODE: Joint Venture

STEP 1 — Fetching real-time data from World Bank API
──────────────────────────────────────────────────────
  gdp_usd: 1058440000000.0 (2023)
  gdp_growth_pct: 5.1 (2023)
  military_exp_pct_gdp: 2.3 (2022)
  ...

STEP 2 — Sending to Claude
STEP 3 — Output
══════════════════════════════════════════════════════════════════════

## Market Context
Turkey's GDP reached USD 1.058 trillion in 2023 (Source: World Bank –
GDP (current USD), indicator: NY.GDP.MKTP.CD), with annual growth of
5.1% (Source: World Bank – GDP growth (annual %), indicator:
NY.GDP.MKTP.KD.ZG, 2023)...
```

---

## Architecture

```
User Input (company, country, sector, mode, rationale)
        ↓
data_fetch.py
  → World Bank API (12 indicators)
  → Returns: {value, year, source, url} per indicator
        ↓
format_for_prompt()
  → Converts to text block with inline citations
        ↓
ai_engine.py
  → System prompt: "Only use provided data"
  → Claude claude-sonnet-4-5 generates insight
  → Every number cited with source
        ↓
main.py prints structured output
```

---

## Cost per run

- World Bank API: free, no key required
- Claude API: ~0.01–0.04 USD per full analysis at claude-sonnet-4-5 pricing

---

## Extending this MVP

To add more data sources, add a new fetcher function in `data_fetch.py` following the same pattern:

```python
def get_your_indicator(country_code: str) -> dict:
    # fetch from API
    return {
        "value": <number>,
        "year": <string>,
        "source": "<exact source name>",
        "url": "<direct link>"
    }
```

Then add it to `get_full_country_profile()` in the `fetchers` dict.
