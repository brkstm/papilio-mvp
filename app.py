# app.py — Papilio AI · Strategy Intelligence Dashboard

import re
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from data_fetch import get_country_profile, format_for_prompt
from ai_engine import generate_analysis

load_dotenv()

# ══════════════════════════════════════════════════
# 1. DESIGN TOKENS
# ══════════════════════════════════════════════════

C = {
    "green":  "#10b981", "amber": "#f59e0b", "red":   "#ef4444",
    "bg":     "#0d1117", "card":  "#111827", "border":"rgba(255,255,255,0.07)",
    "muted":  "#6b7280", "text":  "#e5e7eb", "dim":   "#9ca3af",
}
CHART_BASE = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                  font=dict(color="#6b7280", size=9))

# ══════════════════════════════════════════════════
# 2. TRANSLATIONS
# ══════════════════════════════════════════════════

LABELS = {
    "EN": {
        "tab1": "  Executive Summary  ", "tab2": "  Market & Competition  ",
        "tab3": "  Risk & Strategy  ",   "tab4": "  Stakeholders  ",
        "rec": "Recommendation", "market_score": "Market Score",
        "risk_level": "Risk Level", "entry_mode": "Entry Mode",
        "data_coverage": "Data Coverage", "key_insights": "Key Insights",
        "key_risks": "Key Risks", "next_steps": "Next Steps",
        "data_freshness": "Data Freshness", "macro_data": "Macro & economic data",
        "gov_data": "Governance indicators", "freshness_note":
            "Economic and governance indicators may lag due to official publication cycles. "
            "Displayed values represent the latest available official data — not historical estimates.",
        "latest_avail": "Latest available official value",
        "score_comp": "Score Composition", "risk_comp": "Risk Composition",
        "formula": "Combined Score Formula", "econ_profile": "Economic Profile",
        "strat_opp": "Strategic Opportunities", "comp_pos": "Competitive Positioning",
        "ref_comp": "Reference Competitors", "gov_radar": "Governance Risk Radar",
        "gov_detail": "Governance Detail", "entry_blockers": "Entry Blockers",
        "exec_steps": "Execution Steps", "ai_note": "AI Strategy Note",
        "verified_src": "Verified Data Sources", "stakeholders": "Stakeholder Map",
        "power_interest": "Power / Interest Matrix",
        "sh_category": "Category", "sh_name": "Stakeholder",
        "sh_stance": "Stance", "sh_power": "Power", "sh_interest": "Interest",
        "sh_action": "Recommended Action",
        "supporter": "Supporter", "neutral": "Neutral", "resistance": "Resistance",
        "run_btn": "▶  Run Analysis", "lang_label": "Language",
        "case_params": "Case Parameters",
        "market_attr": "Market Attractiveness", "risk_exp": "Risk Exposure",
        "combined": "Combined Entry Score",
        "higher_better": "Higher = better governance · dotted = 60/100 benchmark",
        "ref_note": "⚠ Reference layer only — not sourced from live data. To be replaced in v2.",
        "static_ref": "Static reference only — sourced company data to be integrated in v2.",
    },
    "DE": {
        "tab1": "  Zusammenfassung  ", "tab2": "  Markt & Wettbewerb  ",
        "tab3": "  Risiko & Strategie  ", "tab4": "  Stakeholder  ",
        "rec": "Empfehlung", "market_score": "Markt-Score",
        "risk_level": "Risikoniveau", "entry_mode": "Eintrittsstrategie",
        "data_coverage": "Datenabdeckung", "key_insights": "Kernergebnisse",
        "key_risks": "Hauptrisiken", "next_steps": "Nächste Schritte",
        "data_freshness": "Datenaktualität", "macro_data": "Makro- & Wirtschaftsdaten",
        "gov_data": "Governance-Indikatoren", "freshness_note":
            "Wirtschafts- und Governance-Indikatoren können aufgrund offizieller Publikationszyklen verzögert sein. "
            "Die angezeigten Werte sind die neuesten verfügbaren offiziellen Daten — keine historischen Schätzungen.",
        "latest_avail": "Neuester verfügbarer offizieller Wert",
        "score_comp": "Score-Zusammensetzung", "risk_comp": "Risiko-Zusammensetzung",
        "formula": "Kombinierter Score", "econ_profile": "Wirtschaftsprofil",
        "strat_opp": "Strategische Chancen", "comp_pos": "Wettbewerbspositionierung",
        "ref_comp": "Referenz-Wettbewerber", "gov_radar": "Governance-Risikoradar",
        "gov_detail": "Governance-Detail", "entry_blockers": "Eintrittsbarrieren",
        "exec_steps": "Umsetzungsschritte", "ai_note": "KI-Strategienotiz",
        "verified_src": "Verifizierte Datenquellen", "stakeholders": "Stakeholder-Karte",
        "power_interest": "Macht / Interesse Matrix",
        "sh_category": "Kategorie", "sh_name": "Stakeholder",
        "sh_stance": "Haltung", "sh_power": "Macht", "sh_interest": "Interesse",
        "sh_action": "Empfohlene Maßnahme",
        "supporter": "Unterstützer", "neutral": "Neutral", "resistance": "Widerstand",
        "run_btn": "▶  Analyse starten", "lang_label": "Sprache",
        "case_params": "Fallparameter",
        "market_attr": "Marktattraktivität", "risk_exp": "Risikoexposition",
        "combined": "Kombinierter Eintrittswert",
        "higher_better": "Höher = bessere Governance · gepunktet = Benchmark 60/100",
        "ref_note": "⚠ Nur Referenzschicht — keine Live-Daten. Wird in v2 ersetzt.",
        "static_ref": "Nur statische Referenz — verifizierte Unternehmensdaten werden in v2 integriert.",
    },
}

# ══════════════════════════════════════════════════
# 3. PAGE CONFIG + CSS
# ══════════════════════════════════════════════════

st.set_page_config(page_title="Papilio AI", page_icon="🦋",
                   layout="wide", initial_sidebar_state="expanded")

def inject_css():
    g, a, r, bg, card, bdr, mu, tx, di = (
        C["green"], C["amber"], C["red"], C["bg"], C["card"],
        C["border"], C["muted"], C["text"], C["dim"]
    )
    st.markdown(f"""<style>
html,body,[class*="css"]{{background:{bg};color:{tx};font-family:'Inter',-apple-system,sans-serif;}}
.block-container{{padding:1rem 2rem 2rem;}}
div[data-testid="stSidebar"]{{background:#090e18;border-right:1px solid {bdr};}}
#MainMenu,footer,.stDeployButton{{visibility:hidden;display:none;}}

.card{{background:{card};border:1px solid {bdr};border-radius:12px;padding:18px 20px;margin-bottom:14px;}}
.card-xs{{background:{card};border:1px solid {bdr};border-radius:8px;padding:11px 14px;margin-bottom:8px;}}

.slbl{{font-size:.67rem;letter-spacing:.13em;text-transform:uppercase;color:{mu};margin-bottom:11px;
       display:flex;align-items:center;gap:8px;}}
.slbl::after{{content:'';flex:1;height:1px;background:{bdr};}}

.v-enter{{background:linear-gradient(135deg,#052e16,#064e3b);border:1px solid #059669;
          border-radius:14px;padding:24px 28px;margin-bottom:20px;}}
.v-wait{{background:linear-gradient(135deg,#1c1003,#292504);border:1px solid #d97706;
         border-radius:14px;padding:24px 28px;margin-bottom:20px;}}
.v-hold{{background:linear-gradient(135deg,#1f0707,#2d0b0b);border:1px solid #dc2626;
         border-radius:14px;padding:24px 28px;margin-bottom:20px;}}
.v-eyebrow{{font-size:.68rem;letter-spacing:.13em;text-transform:uppercase;color:{di};margin-bottom:6px;}}
.v-headline{{font-size:2rem;font-weight:800;letter-spacing:-.03em;margin-bottom:5px;line-height:1.1;}}
.v-driver{{font-size:.9rem;color:{di};margin-bottom:18px;line-height:1.55;}}
.v-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:16px;}}
.v-cell{{background:rgba(0,0,0,.28);border-radius:9px;padding:12px 15px;}}
.v-cell-lbl{{font-size:.67rem;color:{mu};text-transform:uppercase;letter-spacing:.09em;margin-bottom:5px;}}
.v-cell-val{{font-size:1.25rem;font-weight:800;line-height:1.1;}}

.kpi-row{{display:grid;grid-template-columns:repeat(5,1fr);gap:9px;margin-bottom:18px;}}
.kpi-cell{{background:{card};border:1px solid {bdr};border-radius:10px;padding:14px 15px;}}
.kpi-lbl{{font-size:.68rem;color:{mu};text-transform:uppercase;letter-spacing:.07em;margin-bottom:4px;}}
.kpi-val{{font-size:1.5rem;font-weight:800;margin:0 0 3px;line-height:1;}}
.kpi-yr{{font-size:.68rem;color:{mu};}}

.box-ok{{background:rgba(16,185,129,.06);border-left:3px solid {g};
         border-radius:0 9px 9px 0;padding:12px 15px;margin-bottom:9px;font-size:.88rem;line-height:1.62;}}
.box-rh{{background:rgba(239,68,68,.07);border-left:3px solid {r};
         border-radius:0 9px 9px 0;padding:12px 15px;margin-bottom:9px;font-size:.88rem;line-height:1.62;}}
.box-rm{{background:rgba(245,158,11,.07);border-left:3px solid {a};
         border-radius:0 9px 9px 0;padding:12px 15px;margin-bottom:9px;font-size:.88rem;line-height:1.62;}}

.box-step{{background:rgba(0,153,255,.06);border-left:3px solid #3b82f6;
           border-radius:0 9px 9px 0;padding:11px 14px;margin-bottom:8px;font-size:.87rem;line-height:1.6;}}

.bdg{{display:inline-block;font-size:.65rem;font-weight:700;padding:2px 8px;border-radius:4px;
      text-transform:uppercase;letter-spacing:.06em;margin-right:5px;}}
.bdg-h{{background:rgba(239,68,68,.15);color:{r};}}
.bdg-m{{background:rgba(245,158,11,.15);color:{a};}}
.bdg-l{{background:rgba(16,185,129,.15);color:{g};}}

.pill-r{{display:inline-block;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25);
         color:{r};border-radius:6px;padding:4px 12px;font-size:.8rem;margin:3px 3px 3px 0;font-weight:500;}}
.pill-g{{display:inline-block;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);
         color:{g};border-radius:6px;padding:4px 12px;font-size:.8rem;margin:3px 3px 3px 0;font-weight:500;}}

.ai-title{{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
           color:{mu};margin:14px 0 5px;}}
.ai-body{{font-size:.87rem;line-height:1.75;color:#cbd5e1;padding:12px 15px;
          background:rgba(255,255,255,.03);border-radius:8px;border:1px solid {bdr};}}

.cbar-wrap{{margin-bottom:9px;}}
.cbar-head{{display:flex;justify-content:space-between;margin-bottom:4px;}}
.cbar-lbl{{font-size:.81rem;color:{tx};}}
.cbar-val{{font-size:.81rem;font-weight:700;font-family:monospace;}}
.cbar-bg{{background:rgba(255,255,255,.06);border-radius:3px;height:4px;}}
.cbar-sub{{font-size:.69rem;color:{mu};margin-top:2px;}}

.src-row{{display:flex;justify-content:space-between;align-items:center;
          padding:6px 0;border-bottom:1px solid {bdr};font-size:.8rem;}}
.src-row:last-child{{border-bottom:none;}}
.src-lbl{{color:{di};max-width:68%;}}
.src-val{{font-weight:600;font-family:'SF Mono','Fira Code',monospace;font-size:.77rem;text-align:right;}}

.ref-note{{font-size:.7rem;color:{mu};background:rgba(245,158,11,.05);
           border:1px solid rgba(245,158,11,.18);border-radius:6px;padding:7px 12px;margin-bottom:10px;}}
.freshness-block{{background:rgba(59,130,246,.05);border:1px solid rgba(59,130,246,.2);
                  border-radius:10px;padding:14px 18px;margin-bottom:16px;}}
.freshness-title{{font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;
                  color:#60a5fa;margin-bottom:8px;font-weight:700;}}
.freshness-row{{display:flex;justify-content:space-between;align-items:center;
                padding:4px 0;font-size:.82rem;}}
.freshness-note{{font-size:.76rem;color:{mu};margin-top:9px;line-height:1.55;
                 border-top:1px solid rgba(255,255,255,.06);padding-top:8px;}}

.gauge-lbl{{text-align:center;font-size:.72rem;color:{mu};text-transform:uppercase;
            letter-spacing:.1em;margin-top:-6px;}}

div[data-baseweb="tab-list"]{{background:transparent;border-bottom:1px solid {bdr};gap:0;}}
div[data-baseweb="tab"]{{background:transparent;color:{mu};font-size:.85rem;font-weight:500;
                          padding:10px 18px;border-radius:0;}}
div[aria-selected="true"]{{color:{tx}!important;border-bottom:2px solid {g}!important;
                            background:transparent!important;}}

.step-row{{display:flex;gap:12px;align-items:flex-start;margin-bottom:9px;}}
.step-tag{{flex-shrink:0;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);
           border-radius:5px;padding:3px 10px;font-size:.68rem;font-weight:700;
           color:{g};white-space:nowrap;margin-top:2px;letter-spacing:.04em;}}
.step-desc{{font-size:.85rem;color:{tx};line-height:1.58;}}

.sh-card{{background:{card};border:1px solid {bdr};border-radius:10px;
          padding:13px 15px;margin-bottom:8px;display:flex;gap:14px;align-items:flex-start;}}
.sh-icon{{font-size:1.4rem;flex-shrink:0;margin-top:1px;}}
.sh-name{{font-size:.92rem;font-weight:700;color:{tx};margin-bottom:2px;}}
.sh-role{{font-size:.78rem;color:{mu};margin-bottom:5px;}}
.sh-action{{font-size:.8rem;color:{di};line-height:1.5;}}
.sh-badges{{display:flex;gap:5px;margin-bottom:5px;flex-wrap:wrap;}}
.sh-bdg{{display:inline-block;font-size:.65rem;font-weight:600;padding:2px 8px;border-radius:4px;
         text-transform:uppercase;letter-spacing:.05em;}}
.sh-sup{{background:rgba(16,185,129,.12);color:{g};}}
.sh-neu{{background:rgba(107,114,128,.15);color:{mu};}}
.sh-res{{background:rgba(239,68,68,.12);color:{r};}}
.sh-pow{{background:rgba(245,158,11,.1);color:{a};}}
</style>""", unsafe_allow_html=True)

inject_css()


# ══════════════════════════════════════════════════
# 4. DATA HELPERS
# ══════════════════════════════════════════════════

def gv(data, key):
    try:    return data[key]["value"]
    except: return None

def gy(data, key):
    try:    return data[key]["year"] or "–"
    except: return "–"

def fmt_usd(v):
    if v is None: return "N/A"
    if v >= 1e12: return f"${v/1e12:.2f}T"
    if v >= 1e9:  return f"${v/1e9:.1f}B"
    if v >= 1e6:  return f"${v/1e6:.1f}M"
    return f"${v:,.0f}"

def fmt_pct(v, d=1):
    return "N/A" if v is None else f"{v:.{d}f}%"

def fmt_rank(v):
    return "N/A" if v is None else f"{v:.0f} / 100"

def tlight(v, lo=40, hi=65, invert=False):
    if v is None: return C["muted"]
    good, bad = C["green"], C["red"]
    if invert: good, bad = C["red"], C["green"]
    return good if v >= hi else (C["amber"] if v >= lo else bad)

def is_defense(sector):
    return any(k in sector.lower() for k in ("defense","military","radar","aerospace","weapon"))

def latest_year(data, *keys):
    years = [gy(data, k) for k in keys if gy(data, k) != "–"]
    return max(years) if years else "–"

# ══════════════════════════════════════════════════
# 5. HTML COMPONENTS
# ══════════════════════════════════════════════════

def slbl(text): return f'<div class="slbl">{text}</div>'

def insight_box(title, body, source):
    return (f'<div class="box-ok"><strong>{title}:</strong> {body} '
            f'<span style="color:{C["muted"]};font-size:.76rem">{source}</span></div>')

def risk_box(sev, title, body, source):
    s   = sev.lower()
    cls = "box-rh" if s == "high" else "box-rm"
    bdg = "bdg-h"  if s == "high" else "bdg-m"
    return (f'<div class="{cls}"><span class="bdg {bdg}">{sev.upper()}</span>'
            f'<strong>{title}:</strong> {body} '
            f'<span style="color:{C["muted"]};font-size:.76rem">{source}</span></div>')

def step_box(number, text):
    return (f'<div class="box-step">'
            f'<span style="font-weight:700;color:#60a5fa">Step {number}:</span> {text}'
            f'</div>')

def pill_r(text): return f'<span class="pill-r">⚠ {text}</span>'
def pill_g(text): return f'<span class="pill-g">+ {text}</span>'

def cbar(label, pts, mx, color, sub=""):
    pct = min(100, max(0, (pts or 0) / mx * 100))
    sub_html = f'<div class="cbar-sub">{sub}</div>' if sub else ""
    return (f'<div class="cbar-wrap">'
            f'<div class="cbar-head"><span class="cbar-lbl">{label}</span>'
            f'<span class="cbar-val" style="color:{color}">{pts:.0f} / {mx}</span></div>'
            f'<div class="cbar-bg"><div style="background:{color};width:{pct:.0f}%;height:4px;border-radius:3px"></div></div>'
            f'{sub_html}</div>')

def kpi_cell(lbl, val, sub, color):
    return (f'<div class="kpi-cell"><div class="kpi-lbl">{lbl}</div>'
            f'<div class="kpi-val" style="color:{color}">{val}</div>'
            f'<div class="kpi-yr">{sub}</div></div>')

def step_row(phase, desc):
    return (f'<div class="step-row"><div class="step-tag">{phase}</div>'
            f'<div class="step-desc">{desc}</div></div>')

def freshness_block(macro_yr, gov_yr, T):
    return f"""<div class="freshness-block">
      <div class="freshness-title">🕐 {T["data_freshness"]}</div>
      <div class="freshness-row">
        <span style="color:{C['dim']}">{T["macro_data"]}</span>
        <span style="font-weight:700;color:{C['text']}">{T["latest_avail"]}: <span style="color:{C['green']}">{macro_yr}</span></span>
      </div>
      <div class="freshness-row">
        <span style="color:{C['dim']}">{T["gov_data"]}</span>
        <span style="font-weight:700;color:{C['text']}">{T["latest_avail"]}: <span style="color:{C['amber']}">{gov_yr}</span></span>
      </div>
      <div class="freshness-note">{T["freshness_note"]}</div>
    </div>"""

# ══════════════════════════════════════════════════
# 6. SCORING
# ══════════════════════════════════════════════════

def compute_market_score(data, sector):
    defense = is_defense(sector)
    gdp_g   = gv(data,"gdp_growth_pct") or 0
    fdi     = gv(data,"fdi_pct_gdp") or 0
    exports = gv(data,"exports_pct_gdp") or 0
    mil_pct = gv(data,"military_exp_pct_gdp") or 0
    gdp_pc  = gv(data,"gdp_per_capita_usd") or 0
    if defense:
        comps = [
            ("GDP Growth",     gdp_g,   min(25,(gdp_g/8)*25),      25, f"{gdp_g:.1f}% annual"),
            ("Defense Budget", mil_pct, min(30,(mil_pct/4)*30),    30, f"{mil_pct:.1f}% of GDP"),
            ("FDI Openness",   fdi,     min(20,(fdi/4)*20),        20, f"{fdi:.1f}% of GDP"),
            ("Trade Openness", exports, min(15,(exports/40)*15),   15, f"{exports:.1f}% exports/GDP"),
            ("Mkt Maturity",   gdp_pc,  min(10,(gdp_pc/20000)*10), 10, "GDP per capita proxy"),
        ]
    else:
        comps = [
            ("GDP Growth",     gdp_g,   min(25,(gdp_g/8)*25),      25, f"{gdp_g:.1f}% annual"),
            ("FDI Openness",   fdi,     min(30,(fdi/4)*30),        30, f"{fdi:.1f}% of GDP"),
            ("Trade Openness", exports, min(25,(exports/40)*25),   25, f"{exports:.1f}% exports/GDP"),
            ("Mkt Maturity",   gdp_pc,  min(20,(gdp_pc/20000)*20), 20, "GDP per capita proxy"),
        ]
    total = max(0, min(100, round(sum(c[2] for c in comps))))
    return total, comps

def compute_risk_score(data):
    pol = gv(data,"political_stability") or 50
    rol = gv(data,"rule_of_law_rank") or 50
    cor = gv(data,"corruption_control") or 50
    inf = gv(data,"inflation_pct") or 5
    comps = [
        ("Political Stability", pol, round((1-pol/100)*40), 40, "inverted rank · w=40%"),
        ("Rule of Law",         rol, round((1-rol/100)*30), 30, "inverted rank · w=30%"),
        ("Corruption Control",  cor, round((1-cor/100)*20), 20, "inverted rank · w=20%"),
        ("Inflation Risk",      inf, round(min(10,abs(inf)/50*10)), 10, f"{inf:.1f}% CPI · w=10%"),
    ]
    total = max(0, min(100, round(sum(c[2] for c in comps))))
    return total, comps

def compute_verdict(ms, rs, entry_mode):
    if ms >= 60 and rs <= 55:
        return dict(cls="v-enter", color=C["green"],
                    label=f"ENTER — {entry_mode}",
                    driver="Market attractiveness outweighs governance risk at current entry parameters.")
    if ms >= 45 and rs <= 70:
        return dict(cls="v-wait", color=C["amber"],
                    label=f"CONDITIONAL ENTRY — {entry_mode}",
                    driver="Entry viable under risk mitigation. Governance constraints require structural safeguards.")
    return dict(cls="v-hold", color=C["red"],
                label="HOLD — Reassess Entry",
                driver="Risk-adjusted opportunity does not meet threshold at current market and governance parameters.")

# ══════════════════════════════════════════════════
# 7. STAKEHOLDER LOGIC
# ══════════════════════════════════════════════════

def build_stakeholders(industry, entry_mode, country, ms, rs):
    defense    = is_defense(industry)
    high_risk  = rs >= 60
    is_jv      = "Joint Venture" in entry_mode
    is_acq     = "Acquisition" in entry_mode

    stakeholders = []

    # Government / Procurement
    if defense:
        stakeholders.append({
            "icon": "🏛️", "category": "Government / Procurement",
            "name": f"Defense Procurement Agency ({country})",
            "role": "Key buyer, regulatory gatekeeper, local content enforcer",
            "stance": "neutral",
            "power": 95, "interest": 90,
            "action": "Engage early via formal capability briefings. Submit local content plan before procurement cycle opens. Identify decision-maker at director level.",
        })
    else:
        stakeholders.append({
            "icon": "🏛️", "category": "Government",
            "name": f"Ministry of Economy / Investment Authority ({country})",
            "role": "FDI gatekeeper, tax & permit authority",
            "stance": "neutral",
            "power": 88, "interest": 75,
            "action": "Initiate through official investment promotion channel. Present job creation and technology transfer commitments.",
        })

    # Regulator
    if defense:
        stakeholders.append({
            "icon": "📋", "category": "Regulatory",
            "name": "Export Control Authority (BAFA / US State Dept.)",
            "role": "ITAR/EAR license approval — critical path item",
            "stance": "neutral",
            "power": 85, "interest": 60,
            "action": "File Commodity Jurisdiction request immediately. Engage legal counsel specialized in dual-use export. Target <25% US content to minimize ITAR exposure.",
        })
    else:
        stakeholders.append({
            "icon": "📋", "category": "Regulatory",
            "name": f"Sector Regulator ({country})",
            "role": "Licensing, compliance, operating permits",
            "stance": "neutral",
            "power": 78, "interest": 55,
            "action": "Map all required licenses in pre-entry phase. Assign dedicated compliance owner.",
        })

    # Local Partner / JV
    if is_jv:
        stakeholders.append({
            "icon": "🤝", "category": "Local Partners",
            "name": "Local JV Partner (Target TBD)",
            "role": "License holder, local content vehicle, political access",
            "stance": "supporter",
            "power": 70, "interest": 95,
            "action": "Screen 3–5 candidates on capability, government relationships, and ownership structure. Conduct full governance DD before term sheet.",
        })
    elif is_acq:
        stakeholders.append({
            "icon": "🏢", "category": "Target Company",
            "name": "Acquisition Target Management",
            "role": "Operational continuity, knowledge transfer, client retention",
            "stance": "neutral",
            "power": 60, "interest": 85,
            "action": "Prepare management retention plan pre-closing. Align on strategic roadmap to reduce uncertainty and defection risk.",
        })

    # Local Competition
    stakeholders.append({
        "icon": "⚡", "category": "Competitors",
        "name": "Local Incumbents",
        "role": "Established market share, government relationships",
        "stance": "resistance",
        "power": 72 if defense else 65, "interest": 80,
        "action": "Map competitive response risk. Differentiate on technology gap. Consider co-opetition in non-core segments.",
    })

    # International peers
    stakeholders.append({
        "icon": "🌐", "category": "International Peers",
        "name": "European / US Competitors",
        "role": "Technology peers competing for same contracts",
        "stance": "resistance",
        "power": 65, "interest": 75,
        "action": "Monitor their local partnership activity. Accelerate partner selection to close the window before they establish exclusive relationships.",
    })

    # Internal — Board
    stakeholders.append({
        "icon": "🎯", "category": "Internal",
        "name": "Group Board / CFO",
        "role": "Investment approval, risk tolerance, reporting",
        "stance": "neutral",
        "power": 90, "interest": 70,
        "action": "Present risk-adjusted NPV with Base/Bull/Bear scenarios. Frame as strategic foothold, not isolated revenue bet. Provide quarterly milestone gate reviews.",
    })

    # Political risk (only if high governance risk)
    if high_risk:
        stakeholders.append({
            "icon": "⚠️", "category": "Risk Factor",
            "name": "Political Environment",
            "role": "Regime instability, policy reversal, contract enforcement",
            "stance": "resistance",
            "power": 80, "interest": 40,
            "action": "Structure all contracts under international arbitration (ICC/ICSID). Include force majeure and political risk clauses. Obtain political risk insurance.",
        })

    return stakeholders

def chart_power_interest(stakeholders):
    stance_colors = {"supporter": C["green"], "neutral": C["amber"], "resistance": C["red"]}
    fig = go.Figure()
    for sh in stakeholders:
        color = stance_colors.get(sh["stance"], C["muted"])
        fig.add_trace(go.Scatter(
            x=[sh["interest"]], y=[sh["power"]],
            mode="markers+text",
            marker=dict(size=16, color=color, opacity=0.8,
                        line=dict(width=1.5, color="rgba(255,255,255,.2)")),
            text=[sh["name"].split("(")[0].strip()[:20]],
            textposition="top center",
            textfont=dict(size=8, color=C["text"]),
            name=sh["name"].split("(")[0].strip()[:22],
            showlegend=False,
        ))
    fig.add_shape(type="line", x0=50, x1=50, y0=0, y1=100,
                  line=dict(color="rgba(255,255,255,.1)", width=1, dash="dot"))
    fig.add_shape(type="line", x0=0, x1=100, y0=50, y1=50,
                  line=dict(color="rgba(255,255,255,.1)", width=1, dash="dot"))
    fig.update_layout(
        **CHART_BASE, height=300,
        margin=dict(l=40, r=20, t=30, b=40),
        xaxis=dict(title="Interest →", range=[0,105], tickfont=dict(size=9, color=C["muted"]),
                   gridcolor=C["border"]),
        yaxis=dict(title="Power →", range=[0,105], tickfont=dict(size=9, color=C["muted"]),
                   gridcolor=C["border"]),
        annotations=[
            dict(x=25, y=95, text="Manage closely", showarrow=False,
                 font=dict(size=8, color=C["muted"])),
            dict(x=80, y=95, text="Key players", showarrow=False,
                 font=dict(size=8, color=C["muted"])),
            dict(x=25, y=5,  text="Monitor", showarrow=False,
                 font=dict(size=8, color=C["muted"])),
            dict(x=80, y=5,  text="Keep informed", showarrow=False,
                 font=dict(size=8, color=C["muted"])),
        ],
    )
    return fig

# ══════════════════════════════════════════════════
# 8. CHARTS
# ══════════════════════════════════════════════════

def chart_gauge(score, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, domain={"x":[0,1],"y":[0,1]},
        gauge=dict(
            axis=dict(range=[0,100], tickfont=dict(size=8, color=C["muted"])),
            bar=dict(color=color, thickness=0.22),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            steps=[dict(range=[0,40],  color="rgba(16,185,129,.06)"),
                   dict(range=[40,70], color="rgba(245,158,11,.06)"),
                   dict(range=[70,100],color="rgba(239,68,68,.06)")],
        ),
        number=dict(font=dict(size=34, color=color, family="Inter")),
    ))
    fig.update_layout(**CHART_BASE, height=160, margin=dict(l=20,r=20,t=10,b=0))
    return fig

def chart_bar(data):
    items = [("GDP Growth %",   gv(data,"gdp_growth_pct")      or 0, C["green"]),
             ("Inflation %",    gv(data,"inflation_pct")         or 0, C["red"]),
             ("Military % GDP", gv(data,"military_exp_pct_gdp")  or 0, C["amber"]),
             ("FDI % GDP",      gv(data,"fdi_pct_gdp")          or 0, C["green"]),
             ("Exports % GDP",  gv(data,"exports_pct_gdp")       or 0, C["green"])]
    labels, vals, colors = zip(*items)
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=colors,
                            text=[f"{v:.1f}" for v in vals],
                            textposition="outside", textfont=dict(size=11, color=C["text"])))
    fig.update_layout(**CHART_BASE, height=240, bargap=0.38,
                      margin=dict(l=10,r=10,t=14,b=30),
                      xaxis=dict(tickfont=dict(size=10,color=C["muted"]),gridcolor=C["border"]),
                      yaxis=dict(tickfont=dict(size=9,color=C["muted"]),gridcolor=C["border"]))
    return fig

def chart_radar(data):
    labels = ["Political<br>Stability","Rule<br>of Law","Corruption<br>Control"]
    vals   = [gv(data,"political_stability") or 0,
              gv(data,"rule_of_law_rank") or 0,
              gv(data,"corruption_control") or 0]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=labels+[labels[0]],
                                   fill="toself", fillcolor="rgba(239,68,68,.11)",
                                   line=dict(color=C["red"],width=1.5), name="Country profile"))
    fig.add_trace(go.Scatterpolar(r=[60,60,60,60], theta=labels+[labels[0]],
                                   fill="toself", fillcolor="rgba(16,185,129,.05)",
                                   line=dict(color=C["green"],width=1,dash="dot"), name="Benchmark 60"))
    fig.update_layout(**CHART_BASE, height=255, margin=dict(l=30,r=30,t=20,b=20),
                      polar=dict(bgcolor="rgba(0,0,0,0)",
                                 radialaxis=dict(range=[0,100],tickfont=dict(size=7,color=C["muted"]),gridcolor=C["border"]),
                                 angularaxis=dict(tickfont=dict(size=9,color=C["text"]),gridcolor=C["border"])),
                      legend=dict(font=dict(size=9,color=C["muted"]),bgcolor="rgba(0,0,0,0)"))
    return fig

def chart_positioning():
    groups = [
        ("Local incumbents",    C["amber"], 0.7, [("Aselsan",55,82,60),("Roketsan",42,65,40),("Baykar",35,58,35)]),
        ("International peers", C["muted"], 0.6, [("Thales",78,45,35),("Leonardo",68,38,30),("Aerojet",82,30,26)]),
        ("Target position",     C["green"], 1.0, [("Our Target",80,16,22)]),
    ]
    fig = go.Figure()
    for label, color, opacity, pts in groups:
        fig.add_trace(go.Scatter(
            x=[p[1] for p in pts], y=[p[2] for p in pts], mode="markers+text",
            marker=dict(size=[p[3]*.52 for p in pts], color=color, opacity=opacity,
                        line=dict(width=1.5,color="rgba(255,255,255,.12)")),
            text=[p[0] for p in pts], textposition="top center",
            textfont=dict(size=9,color=C["text"]), name=label))
    fig.update_layout(**CHART_BASE, height=265, margin=dict(l=30,r=20,t=20,b=40),
                      xaxis=dict(title="Technology maturity →",range=[10,100],
                                 tickfont=dict(size=9,color=C["muted"]),gridcolor=C["border"]),
                      yaxis=dict(title="Local market presence →",range=[0,100],
                                 tickfont=dict(size=9,color=C["muted"]),gridcolor=C["border"]),
                      legend=dict(font=dict(size=9,color=C["muted"]),bgcolor="rgba(0,0,0,0)",
                                  orientation="h",yanchor="bottom",y=1.02))
    return fig

# ══════════════════════════════════════════════════
# 9. AI TEXT PARSER
# ══════════════════════════════════════════════════

def parse_ai_sections(text):
    sections = re.split(r"\n(?=\d+[\.\)\s])", text.strip())
    parsed = []
    for sec in sections:
        m = re.match(r"^\d+[\.\)\s]+(.+?)\n(.+)", sec.strip(), re.DOTALL)
        if m:
            parsed.append((m.group(1).strip(), m.group(2).strip()))
        elif sec.strip():
            parsed.append(("Analysis", sec.strip()))
    return parsed or [("Strategy Note", text.strip())]

# ══════════════════════════════════════════════════
# 10. SIDEBAR
# ══════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        f'<div style="font-size:1.35rem;font-weight:800;color:{C["green"]};'
        f'letter-spacing:-.02em;margin-bottom:2px">🦋 Papilio AI</div>'
        f'<div style="font-size:.69rem;color:{C["muted"]};text-transform:uppercase;'
        f'letter-spacing:.11em;margin-bottom:16px">Strategy Intelligence</div>',
        unsafe_allow_html=True)

    lang = st.radio("Language / Sprache", ["EN", "DE"], horizontal=True,
                    label_visibility="collapsed")
    T = LABELS[lang]

    st.markdown(f'<div style="font-size:.68rem;color:{C["muted"]};text-transform:uppercase;'
                f'letter-spacing:.1em;margin:14px 0 8px">{T["case_params"]}</div>',
                unsafe_allow_html=True)
    company    = st.text_input("Company",      "Hensoldt AG")
    country    = st.text_input("Country Code", "TR", help="ISO 3166-1 alpha-2 e.g. TR, DE, IN, SA")
    industry   = st.text_input("Sector",       "Radar & Electronic Warfare")
    entry_mode = st.selectbox(T["entry_mode"],
                              ["Joint Venture","Acquisition","Greenfield","Export / Licensing"])
    st.write("")
    run = st.button(T["run_btn"], use_container_width=True, type="primary")
    st.markdown(f'<div style="margin-top:24px;font-size:.68rem;color:#374151;line-height:1.85">'
                f'Data: World Bank Open API<br>AI: GPT-4o-mini · temp 0.1<br>'
                f'Rule: every figure sourced</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# 11. EMPTY STATE
# ══════════════════════════════════════════════════

if not run and "result" not in st.session_state:
    T0 = LABELS.get("EN")
    st.markdown(
        f'<div style="padding:90px 0;text-align:center">'
        f'<div style="font-size:2.8rem;margin-bottom:14px">🦋</div>'
        f'<div style="font-size:1.1rem;font-weight:700;color:{C["text"]};margin-bottom:6px">'
        f'Papilio AI — Market Entry Intelligence</div>'
        f'<div style="font-size:.87rem;color:{C["muted"]}">'
        f'Configure the case in the sidebar and click <strong style="color:{C["text"]}">Run Analysis</strong></div>'
        f'</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════
# 12. PIPELINE
# ══════════════════════════════════════════════════

if run:
    with st.spinner("Fetching country data from World Bank…"):
        profile = get_country_profile(country, verbose=False)
    with st.spinner("Generating strategy note — GPT-4o-mini…"):
        prompt_data = format_for_prompt(profile)
        ai_text = generate_analysis(prompt_data, company, country, industry, entry_mode)
    st.session_state.update(dict(
        result=ai_text, profile=profile, company=company,
        country=country, industry=industry, entry_mode=entry_mode))

ai_text    = st.session_state["result"]
profile    = st.session_state["profile"]
company    = st.session_state["company"]
country    = st.session_state["country"]
industry   = st.session_state["industry"]
entry_mode = st.session_state["entry_mode"]
data       = profile["indicators"]
T          = LABELS[lang]

ms, ms_comp = compute_market_score(data, industry)
rs, rs_comp = compute_risk_score(data)
verdict     = compute_verdict(ms, rs, entry_mode)
combined    = round(ms * 0.55 + (100 - rs) * 0.45)
risk_label  = "High" if rs >= 65 else "Medium" if rs >= 40 else "Low"
risk_color  = C["red"] if rs >= 65 else C["amber"] if rs >= 40 else C["green"]

macro_yr  = latest_year(data, "gdp_usd","gdp_growth_pct","inflation_pct","fdi_pct_gdp",
                        "military_exp_usd","exports_pct_gdp","gdp_per_capita_usd")
gov_yr    = latest_year(data, "political_stability","rule_of_law_rank","corruption_control")
stakeholders = build_stakeholders(industry, entry_mode, country, ms, rs)

# ══════════════════════════════════════════════════
# 13. TABS
# ══════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    T["tab1"], T["tab2"], T["tab3"], T["tab4"],
])


# ── TAB 1 · EXECUTIVE SUMMARY ──────────────────────
with tab1:
    vc = verdict["color"]

    # Verdict block
    st.markdown(f"""
    <div class="{verdict['cls']}">
      <div class="v-eyebrow">Papilio AI · {company} · {country} · {industry}</div>
      <div class="v-headline" style="color:{vc}">{verdict['label']}</div>
      <div class="v-driver">{verdict['driver']}</div>
      <div class="v-grid">
        <div class="v-cell">
          <div class="v-cell-lbl">{T["market_score"]}</div>
          <div class="v-cell-val" style="color:{tlight(ms)}">{ms}<span style="font-size:.85rem;font-weight:500;opacity:.6"> / 100</span></div>
        </div>
        <div class="v-cell">
          <div class="v-cell-lbl">{T["risk_level"]}</div>
          <div class="v-cell-val" style="color:{risk_color}">{risk_label}<span style="font-size:.85rem;font-weight:500;opacity:.6"> ({rs}/100)</span></div>
        </div>
        <div class="v-cell">
          <div class="v-cell-lbl">{T["entry_mode"]}</div>
          <div class="v-cell-val" style="color:{C['text']};font-size:1rem">{entry_mode}</div>
        </div>
        <div class="v-cell">
          <div class="v-cell-lbl">{T["data_coverage"]}</div>
          <div class="v-cell-val" style="color:{C['text']}">{profile['available_count']}<span style="font-size:.85rem;font-weight:500;opacity:.6"> / 12</span></div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Data Freshness block
    st.markdown(freshness_block(macro_yr, gov_yr, T), unsafe_allow_html=True)

    # Gauges
    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(chart_gauge(ms, tlight(ms)), use_container_width=True, config={"displayModeBar":False})
        st.markdown(f'<div class="gauge-lbl">{T["market_attr"]}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        st.markdown(slbl(T["score_comp"]), unsafe_allow_html=True)
        for label,raw,pts,mx,note in ms_comp:
            st.markdown(cbar(label, pts, mx, tlight(ms), note), unsafe_allow_html=True)
    with g2:
        st.plotly_chart(chart_gauge(rs, tlight(rs,invert=True)), use_container_width=True, config={"displayModeBar":False})
        st.markdown(f'<div class="gauge-lbl">{T["risk_exp"]}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        st.markdown(slbl(T["risk_comp"]), unsafe_allow_html=True)
        for label,raw,pts,mx,note in rs_comp:
            st.markdown(cbar(label, pts, mx, tlight(rs,invert=True), note), unsafe_allow_html=True)
    with g3:
        st.plotly_chart(chart_gauge(combined, tlight(combined)), use_container_width=True, config={"displayModeBar":False})
        st.markdown(f'<div class="gauge-lbl">{T["combined"]}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        st.markdown(slbl(T["formula"]), unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:.82rem;color:{C["muted"]};line-height:1.8;padding:6px 0">'
            f'Market Score × 0.55<br>+ (100 − Risk) × 0.45<br>'
            f'= <strong style="color:{C["text"]};font-size:.9rem">{ms} × 0.55 + {100-rs} × 0.45 = {combined}</strong>'
            f'</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    # Insights + Risks
    ci, cr = st.columns(2)
    with ci:
        st.markdown(slbl(T["key_insights"]), unsafe_allow_html=True)
        gdp_v = gv(data,"gdp_usd");   gdp_g = gv(data,"gdp_growth_pct")
        mil_u = gv(data,"military_exp_usd"); mil_p = gv(data,"military_exp_pct_gdp")
        fdi_v = gv(data,"fdi_pct_gdp")
        if gdp_v and gdp_g:
            st.markdown(insight_box("Economy",
                f"GDP {fmt_usd(gdp_v)} — {T['latest_avail']}: {gy(data,'gdp_usd')}. "
                f"Growing {fmt_pct(gdp_g)} annually.",
                "WB NY.GDP.MKTP.CD"), unsafe_allow_html=True)
        if mil_u and mil_p:
            st.markdown(insight_box("Defense market",
                f"{fmt_usd(mil_u)} military expenditure ({T['latest_avail']}: {gy(data,'military_exp_usd')}), "
                f"{fmt_pct(mil_p)} of GDP — structural demand signal.",
                "SIPRI via WB MS.MIL.XPND.CD"), unsafe_allow_html=True)
        if fdi_v:
            rel = "above" if fdi_v >= 3 else "below"
            rec = "receptive" if fdi_v >= 3 else "below median"
            st.markdown(insight_box("FDI environment",
                f"Net inflows {fmt_pct(fdi_v)} of GDP ({T['latest_avail']}: {gy(data,'fdi_pct_gdp')}), "
                f"{rel} OECD 3% median — {rec} for foreign entry.",
                "WB BX.KLT.DINV.WD.GD.ZS"), unsafe_allow_html=True)

    with cr:
        st.markdown(slbl(T["key_risks"]), unsafe_allow_html=True)
        pol = gv(data,"political_stability"); rol = gv(data,"rule_of_law_rank")
        inf = gv(data,"inflation_pct")
        if pol is not None:
            sev = "high" if pol < 30 else "medium" if pol < 55 else "low"
            msg = ("Elevated regime risk — mitigate via contractual exit clauses."
                   if pol < 30 else "Moderate — standard political risk provisions adequate.")
            st.markdown(risk_box(sev, "Political Stability",
                f"{fmt_rank(pol)} ({T['latest_avail']}: {gy(data,'political_stability')}). {msg}",
                "WB PV.PER.RNK"), unsafe_allow_html=True)
        if rol is not None:
            sev = "high" if rol < 35 else "medium" if rol < 60 else "low"
            st.markdown(risk_box(sev, "Rule of Law",
                f"{fmt_rank(rol)} ({T['latest_avail']}: {gy(data,'rule_of_law_rank')}). "
                "Contract enforceability requires JV safeguards and international arbitration.",
                "WB RL.PER.RNK"), unsafe_allow_html=True)
        if inf is not None and abs(inf) > 8:
            sev = "high" if abs(inf) > 15 else "medium"
            msg = ("FX and cost-base risk material — USD/EUR denomination required."
                   if abs(inf) > 15 else "Elevated — monitor FX exposure on local cost base.")
            st.markdown(risk_box(sev, "Inflation",
                f"{fmt_pct(inf)} ({T['latest_avail']}: {gy(data,'inflation_pct')}). {msg}",
                "WB FP.CPI.TOTL.ZG"), unsafe_allow_html=True)

    # Next Steps
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    st.markdown(slbl(T["next_steps"]), unsafe_allow_html=True)
    ns1 = ("Confirm partner selection" if "Joint Venture" in entry_mode
           else "Finalize acquisition target" if "Acquisition" in entry_mode
           else "Establish legal entity")
    ns2 = "File export control application (BAFA/ITAR)" if is_defense(industry) else "Submit FDI registration"
    ns3 = ("Present Local Content Plan to procurement authority" if is_defense(industry)
           else "Secure first customer / distribution agreement")
    st.markdown(step_box(1, ns1), unsafe_allow_html=True)
    st.markdown(step_box(2, ns2), unsafe_allow_html=True)
    st.markdown(step_box(3, ns3), unsafe_allow_html=True)


# ── TAB 2 · MARKET & COMPETITION ────────────────────
with tab2:
    gv2 = gv(data,"gdp_growth_pct") or 0
    fv2 = gv(data,"fdi_pct_gdp") or 0
    iv2 = gv(data,"inflation_pct") or 0
    st.markdown(f"""
    <div class="kpi-row">
      {kpi_cell("GDP", fmt_usd(gv(data,"gdp_usd")),
                f"{T['latest_avail']}: {gy(data,'gdp_usd')} · World Bank", C["green"])}
      {kpi_cell("GDP Growth", fmt_pct(gv(data,"gdp_growth_pct")),
                f"{T['latest_avail']}: {gy(data,'gdp_growth_pct')} · annual",
                C["green"] if gv2>=3 else C["amber"])}
      {kpi_cell("Military Spend", fmt_usd(gv(data,"military_exp_usd")),
                f"{T['latest_avail']}: {gy(data,'military_exp_usd')} · SIPRI", C["amber"])}
      {kpi_cell("FDI Inflows", f"{fmt_pct(gv(data,'fdi_pct_gdp'))} GDP",
                f"{T['latest_avail']}: {gy(data,'fdi_pct_gdp')} · World Bank",
                C["green"] if fv2>=2 else C["muted"])}
      {kpi_cell("Inflation", fmt_pct(gv(data,"inflation_pct")),
                f"{T['latest_avail']}: {gy(data,'inflation_pct')} · CPI",
                C["red"] if iv2>15 else C["amber"] if iv2>8 else C["green"])}
    </div>""", unsafe_allow_html=True)

    mc1, mc2 = st.columns([1.1, 0.9])
    with mc1:
        st.markdown(slbl(T["econ_profile"]), unsafe_allow_html=True)
        st.plotly_chart(chart_bar(data), use_container_width=True, config={"displayModeBar":False})
        st.markdown(slbl(T["strat_opp"]), unsafe_allow_html=True)
        opps = []
        if (gv(data,"military_exp_pct_gdp") or 0) >= 2:
            opps.append(f"Defense budget {fmt_pct(gv(data,'military_exp_pct_gdp'))} GDP — active procurement cycle")
        if gv2 >= 3:
            opps.append(f"GDP growth {fmt_pct(gv2)} — expanding domestic demand")
        if fv2 >= 2:
            opps.append(f"FDI inflows {fmt_pct(fv2)} GDP — structurally open to foreign entry")
        if entry_mode == "Joint Venture":
            opps.append("JV structure satisfies local content requirements")
        for o in opps:
            st.markdown(pill_g(o), unsafe_allow_html=True)

    with mc2:
        st.markdown(slbl(T["comp_pos"]), unsafe_allow_html=True)
        st.markdown(f'<div class="ref-note">{T["ref_note"]}</div>', unsafe_allow_html=True)
        st.plotly_chart(chart_positioning(), use_container_width=True, config={"displayModeBar":False})
        st.markdown(slbl(T["ref_comp"]), unsafe_allow_html=True)
        comp_df = pd.DataFrame([
            {"Competitor":"Aselsan",  "Segment":"Defense Electronics","Presence":"Dominant","Threat":"High"},
            {"Competitor":"Baykar",   "Segment":"UAV / Systems",      "Presence":"Growing", "Threat":"Medium"},
            {"Competitor":"Thales",   "Segment":"Radar / C2",         "Presence":"Medium",  "Threat":"High"},
            {"Competitor":"Leonardo", "Segment":"Defense Electronics", "Presence":"Medium",  "Threat":"Medium"},
        ])
        st.dataframe(comp_df, use_container_width=True, hide_index=True)
        st.markdown(f'<div style="font-size:.69rem;color:{C["muted"]};margin-top:5px">{T["static_ref"]}</div>',
                    unsafe_allow_html=True)


# ── TAB 3 · RISK & STRATEGY ────────────────────────
with tab3:
    r1, r2 = st.columns([0.85, 1.15])

    with r1:
        st.markdown(slbl(T["gov_radar"]), unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:.73rem;color:{C["muted"]};margin-bottom:8px">{T["higher_better"]}</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(chart_radar(data), use_container_width=True, config={"displayModeBar":False})
        st.markdown(slbl(T["gov_detail"]), unsafe_allow_html=True)
        for label, key, ind in [
            ("Political Stability","political_stability","PV.PER.RNK"),
            ("Rule of Law",        "rule_of_law_rank",   "RL.PER.RNK"),
            ("Corruption Control", "corruption_control", "CC.PER.RNK"),
        ]:
            v = gv(data, key)
            color = C["green"] if (v or 0)>=60 else C["amber"] if (v or 0)>=35 else C["red"]
            st.markdown(
                f'<div style="margin-bottom:12px">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
                f'<span style="font-size:.82rem;color:{C["text"]}">{label}</span>'
                f'<span style="font-size:.82rem;font-weight:700;color:{color}">{fmt_rank(v)}</span></div>'
                f'<div style="background:rgba(255,255,255,.06);border-radius:3px;height:4px">'
                f'<div style="background:{color};width:{int(v or 0)}%;height:4px;border-radius:3px"></div></div>'
                f'<div style="font-size:.69rem;color:{C["muted"]};margin-top:2px">'
                f'{T["latest_avail"]}: {gy(data,key)} · {ind}</div>'
                f'</div>', unsafe_allow_html=True)

    with r2:
        st.markdown(slbl(T["entry_blockers"]), unsafe_allow_html=True)
        blockers = []
        if is_defense(industry):
            blockers += ["ITAR/EAR export control","Local content ≥ 50% (SSB)","Security clearance required"]
        if entry_mode == "Joint Venture":
            blockers.append("JV partner due diligence")
        pv = gv(data,"political_stability") or 50
        cv = gv(data,"corruption_control") or 50
        iv3 = gv(data,"inflation_pct") or 5
        if pv < 30: blockers.append("Political risk — regime instability")
        if cv < 35: blockers.append("Corruption risk — contract integrity")
        if abs(iv3) > 15: blockers.append(f"FX/inflation exposure ({fmt_pct(iv3)})")
        for b in blockers:
            st.markdown(pill_r(b), unsafe_allow_html=True)

        STEPS = {
            "Joint Venture":[
                ("Phase 1 · Q1–Q2","Partner identification & DD. Governance vetting, capability alignment, reference checks."),
                ("Phase 2 · Q3",   "Term sheet & JV agreement. Legal structure, IP licensing, local content plan submitted."),
                ("Phase 3 · Q4–Q6","Regulatory approvals. Security clearance, export license, entity registration."),
                ("Phase 4 · Y2",   "First contract award. Production ramp, technology transfer, local content milestone."),
                ("Phase 5 · Y3+",  "Scale. Full-rate production, local engineering capacity, next program expansion."),
            ],
            "Acquisition":[
                ("Phase 1","Target screening — capability, revenue, government relationships."),
                ("Phase 2","Financial & legal DD. Regulatory pre-clearance for sector FDI."),
                ("Phase 3","Close & integrate. Management retention, technology & compliance alignment."),
                ("Phase 4","Value creation. Synergy realization, cross-sell into existing contracts."),
            ],
        }
        steps = STEPS.get(entry_mode, [
            ("Phase 1","Market assessment and local partner identification."),
            ("Phase 2","Regulatory setup and entity establishment."),
            ("Phase 3","First contracts and production ramp."),
            ("Phase 4","Scale and optimization."),
        ])
        st.markdown(f'<div style="margin-top:18px">{slbl(T["exec_steps"] + " — " + entry_mode)}</div>',
                    unsafe_allow_html=True)
        for phase, desc in steps:
            st.markdown(step_row(phase, desc), unsafe_allow_html=True)

        st.markdown(f'<div style="margin-top:20px">{slbl(T["ai_note"] + " — GPT-4o-mini")}</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:.69rem;color:{C["muted"]};margin-bottom:10px">'
            f'Based solely on verified World Bank indicators · no external knowledge used · '
            f'retrieved {profile.get("retrieved_at","")}</div>', unsafe_allow_html=True)
        for title, body in parse_ai_sections(ai_text):
            st.markdown(f'<div class="ai-title">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ai-body">{body}</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    st.markdown(slbl(T["verified_src"]), unsafe_allow_html=True)
    src_keys = list(data.keys()); half = len(src_keys)//2
    sc1, sc2 = st.columns(2)
    for col, keys in [(sc1, src_keys[:half]), (sc2, src_keys[half:])]:
        with col:
            for k in keys:
                dp = data[k]; v = dp["value"]; yr = dp.get("year") or "–"
                color = C["green"] if dp["status"]=="ok" else C["red"]
                if "usd" in k:                                              val_s = fmt_usd(v)
                elif any(x in k for x in ("stability","rank","corruption","law")): val_s = fmt_rank(v)
                elif v is not None:                                         val_s = fmt_pct(v)
                else:                                                       val_s = "N/A"
                st.markdown(
                    f'<div class="src-row"><span class="src-lbl">{dp["label"][:46]}</span>'
                    f'<span class="src-val" style="color:{color}">{val_s} '
                    f'<span style="color:{C["muted"]};font-size:.72rem">({T["latest_avail"]}: {yr})</span>'
                    f'</span></div>', unsafe_allow_html=True)


# ── TAB 4 · STAKEHOLDERS ────────────────────────────
with tab4:
    s1, s2 = st.columns([1.05, 0.95])

    with s1:
        st.markdown(slbl(T["stakeholders"]), unsafe_allow_html=True)

        stance_label = {"supporter": T["supporter"], "neutral": T["neutral"], "resistance": T["resistance"]}
        stance_cls   = {"supporter": "sh-sup", "neutral": "sh-neu", "resistance": "sh-res"}

        for sh in stakeholders:
            s = sh["stance"]
            power_cls = "sh-pow" if sh["power"] >= 75 else "sh-neu"
            st.markdown(
                f'<div class="sh-card">'
                f'<div class="sh-icon">{sh["icon"]}</div>'
                f'<div style="flex:1">'
                f'<div class="sh-badges">'
                f'<span class="sh-bdg {stance_cls[s]}">{stance_label[s]}</span>'
                f'<span class="sh-bdg {power_cls}">{T["sh_power"]}: {sh["power"]}</span>'
                f'<span class="sh-bdg sh-neu">{T["sh_interest"]}: {sh["interest"]}</span>'
                f'</div>'
                f'<div class="sh-name">{sh["name"]}</div>'
                f'<div class="sh-role">{sh["category"]} · {sh["role"]}</div>'
                f'<div class="sh-action">→ {sh["action"]}</div>'
                f'</div></div>', unsafe_allow_html=True)

    with s2:
        st.markdown(slbl(T["power_interest"]), unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:.73rem;color:{C["muted"]};margin-bottom:8px">'
            f'<span style="color:{C["green"]}">●</span> {T["supporter"]}  '
            f'<span style="color:{C["amber"]}">●</span> {T["neutral"]}  '
            f'<span style="color:{C["red"]}">●</span> {T["resistance"]}</div>',
            unsafe_allow_html=True)
        st.plotly_chart(chart_power_interest(stakeholders), use_container_width=True,
                        config={"displayModeBar":False})

        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        st.markdown(slbl("Summary by Stance"), unsafe_allow_html=True)

        for stance, lbl, cls in [("supporter",T["supporter"],"sh-sup"),
                                   ("neutral",  T["neutral"],  "sh-neu"),
                                   ("resistance",T["resistance"],"sh-res")]:
            group = [sh for sh in stakeholders if sh["stance"]==stance]
            if not group:
                continue
            names = ", ".join(sh["name"].split("(")[0].strip() for sh in group)
            st.markdown(
                f'<div style="margin-bottom:10px;padding:10px 14px;border-radius:8px;'
                f'background:{C["card"]};border:1px solid {C["border"]}">'
                f'<span class="sh-bdg {cls}" style="margin-bottom:6px;display:inline-block">{lbl} ({len(group)})</span>'
                f'<div style="font-size:.82rem;color:{C["dim"]};line-height:1.55">{names}</div>'
                f'</div>', unsafe_allow_html=True)
