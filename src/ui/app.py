"""Streamlit dashboard for CoDex.

Modern single-page design (no sidebar). Tabs:
- Corpus     – stats + drag-and-drop upload + path-based indexing.
- Playground – ask questions, get answers with citations + confidence.
- Traces     – per-query latency / token / cost history (this session).
- Evaluation – latest eval report from reports/report.json.

Run with:  streamlit run src/ui/app.py
Backend expected at http://localhost:8000 (override with API_URL env var).
"""

from __future__ import annotations

import base64
import html
import json
import os
import re
import time
import uuid
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env from repo root (Streamlit does not do this by itself).
_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")
load_dotenv()  # cwd, if you launch from elsewhere

_UI_DIR = Path(__file__).resolve().parent
_FAVICON = _UI_DIR / "assets" / "favicon.png"
_UPLOAD_DIR = _REPO_ROOT / ".uploads"

# ---------------------------------------------------------------------------
# Brand palette
# ---------------------------------------------------------------------------

_BLUE       = "#003b6d"  # TU Braunschweig blue
_RED        = "#be1e2d"  # TU Braunschweig red
_BLUE_LIGHT = "#0a5ca8"
_BG         = "#f5f7fb"
_INK        = "#0f172a"
_MUTED      = "#64748b"

# Playground column width matches tab strip inner (~1280px max − 2×2.5rem gutter).
_CHAT_COL_MAX_PX = 1200
_CHAT_HALF_PX = _CHAT_COL_MAX_PX // 2

# ---------------------------------------------------------------------------
# Global CSS – modern light theme, no sidebar
# ---------------------------------------------------------------------------

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── base ── */
html, body, .stApp, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}
.stApp {{
    background:
        radial-gradient(1200px 600px at -10% -20%, rgba(10,92,168,0.10), transparent 60%),
        radial-gradient(900px 500px at 110% 0%, rgba(190,30,45,0.08), transparent 60%),
        {_BG};
}}

/* ── hide chrome we don't need ── */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu, footer {{
    display: none !important;
}}
/* hide native sidebar; Playground renders its own history panel */
[data-testid="stSidebar"] {{
    display: none !important;
}}
[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

/* ── main container ── */
[data-testid="stMainBlockContainer"] {{
    max-width: 100% !important;
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}}
/* keep tab content readable */
[data-testid="stTabs"] {{
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 2.5rem;
}}

/* ── HERO – full window width, no rounded corners ── */
.hero {{
    background: linear-gradient(135deg, {_BLUE} 0%, {_BLUE_LIGHT} 100%);
    padding: 2.4rem 3rem;
    color: white;
    margin: 0 0 2rem 0;
    box-shadow: 0 6px 24px rgba(0, 59, 109, 0.20);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 2rem;
    position: relative;
    overflow: hidden;
}}
/* subtle decorative shape on the right of the hero */
.hero::before {{
    content: "";
    position: absolute;
    right: -120px; top: -80px;
    width: 360px; height: 360px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.10) 0%, transparent 70%);
    pointer-events: none;
}}
.hero > * {{ position: relative; z-index: 1; }}
.hero-logo {{
    height: 96px;
    width: auto;
    background: transparent;
    display: block;
}}
.hero-left h1 {{
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0;
    line-height: 1;
    color: white;
}}
.hero-left p {{
    margin: 0;
    opacity: 0.85;
    font-size: 0.95rem;
}}
/* status pill in hero */
.hero-status {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255,255,255,0.18);
    backdrop-filter: blur(6px);
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 0.82rem;
    font-weight: 600;
    margin-top: 0.7rem;
}}
.hero-status .dot {{
    width: 8px; height: 8px; border-radius: 50%;
    box-shadow: 0 0 0 3px rgba(255,255,255,0.15);
}}
.dot-on  {{ background: #22c55e; }}
.dot-off {{ background: #ef4444; }}

/* ── tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background: transparent;
    border-bottom: 1px solid #e2e8f0;
    gap: 0.4rem;
    padding: 0;
    margin-bottom: 1.5rem;
}}
button[data-baseweb="tab"] {{
    background: transparent !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    border-radius: 0 !important;
    color: {_MUTED} !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 0.85rem 1.2rem !important;
    transition: color 0.15s, border-color 0.15s;
}}
button[data-baseweb="tab"]:hover {{
    color: {_INK} !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: {_BLUE} !important;
    border-bottom-color: {_RED} !important;
}}

/* ── metric cards ── */
[data-testid="stMetric"] {{
    background: white;
    border-radius: 16px;
    padding: 1.3rem 1.6rem !important;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06), 0 8px 24px rgba(15,23,42,0.04);
    border: 1px solid #eef2f7;
    transition: transform 0.18s, box-shadow 0.18s;
}}
[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 1px 3px rgba(15,23,42,0.08), 0 14px 32px rgba(15,23,42,0.08);
}}
[data-testid="stMetricLabel"] {{
    font-size: 0.74rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {_MUTED} !important;
    font-weight: 600 !important;
}}
[data-testid="stMetricValue"] {{
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    color: {_INK} !important;
    letter-spacing: -0.02em;
}}

/* ── section heading ── */
.section-h {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 1.5rem 0 1rem;
}}
.section-h .bar {{
    width: 4px; height: 22px; border-radius: 4px;
    background: linear-gradient(180deg, {_BLUE}, {_RED});
}}
.section-h h3 {{
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: {_INK};
}}

/* ── cards ── */
.card {{
    background: white;
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06), 0 8px 24px rgba(15,23,42,0.04);
    border: 1px solid #eef2f7;
    margin-bottom: 1.2rem;
}}

/* ── primary buttons ── */
div.stButton > button[kind="primary"],
div.stForm button[kind="primaryFormSubmit"] {{
    background: linear-gradient(135deg, {_RED}, #d63242) !important;
    border: none !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.6rem !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    box-shadow: 0 4px 14px rgba(190,30,45,0.30) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}}
div.stButton > button[kind="primary"]:hover,
div.stForm button[kind="primaryFormSubmit"]:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(190,30,45,0.40) !important;
}}
div.stButton > button[kind="secondary"],
div.stForm button[kind="secondaryFormSubmit"] {{
    background: white !important;
    border: 1px solid #cbd5e1 !important;
    color: {_INK} !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
}}

/* ── file uploader – one giant clickable drop zone ── */
[data-testid="stFileUploaderDropzone"] {{
    position: relative !important;
    background: linear-gradient(180deg, #fafbfd 0%, #f1f5fa 100%) !important;
    border: 2px dashed #cbd5e1 !important;
    border-radius: 14px !important;
    min-height: 200px !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    overflow: hidden !important;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
    border-color: {_BLUE} !important;
    background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%) !important;
}}
/* hide everything Streamlit puts inside – we'll draw our own content */
[data-testid="stFileUploaderDropzone"] * {{
    visibility: hidden !important;
}}
/* the entire dropzone area opens the file picker on click,
   so we only need a giant invisible button covering it.    */
[data-testid="stFileUploaderDropzone"] button {{
    visibility: hidden !important;
    position: absolute !important;
    inset: 0 !important;
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    cursor: pointer !important;
}}
/* our custom centred content (drawn via ::after of the dropzone) */
[data-testid="stFileUploaderDropzone"]::after {{
    content: "☁️\\A Drop PDF files here\\A or click anywhere to browse";
    white-space: pre;
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: {_INK};
    font-weight: 600;
    font-size: 1rem;
    line-height: 1.8;
    pointer-events: none;
}}

/* ── inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {{
    border-radius: 10px !important;
    border: 1px solid #cbd5e1 !important;
    padding: 0.7rem 1rem !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color: {_BLUE} !important;
    box-shadow: 0 0 0 3px rgba(0,59,109,0.12) !important;
}}

/* ── expanders ── */
[data-testid="stExpander"] {{
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    margin-bottom: 0.5rem !important;
}}
[data-testid="stExpander"] summary {{
    font-weight: 600 !important;
    color: {_INK} !important;
}}

/* ── dataframes ── */
[data-testid="stDataFrame"] {{
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}

/* ── Gemini-style chat (custom markup, not st.chat_message) ── */
.gemini-chat-wrap {{
    max-width: {_CHAT_COL_MAX_PX}px;
    margin: 0 auto 5.5rem auto;
    padding: 0 1rem;
}}
.gemini-chat-toolbar {{
    max-width: {_CHAT_COL_MAX_PX}px;
    margin: 0 auto 1rem auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
}}
.gemini-row-user {{
    display: flex;
    justify-content: flex-end;
    margin: 0.65rem 0;
}}
/* one assistant row = one horizontal block with a star in the first column */
div[data-testid="stHorizontalBlock"]:has(.gemini-star) {{
    margin: 0.85rem 0 1.05rem 0 !important;
    align-items: flex-start !important;
}}
.gemini-star {{
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4285f4, #8ab4f8);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.85rem;
    margin-top: 2px;
    box-shadow: 0 1px 4px rgba(66,133,244,0.35);
}}
.gemini-bubble-user {{
    display: inline-block;
    max-width: min(85%, 520px);
    background: #e8f0fe;
    color: #174ea6;
    padding: 0.55rem 1rem;
    border-radius: 22px 22px 6px 22px;
    font-size: 0.98rem;
    line-height: 1.55;
    word-wrap: break-word;
}}
.assistant-answer {{
    color: #1f2937;
    font-size: 0.98rem;
    line-height: 1.65;
}}
.citation-detail {{
    display: inline-block;
    position: relative;
    margin-left: 0.12rem;
    vertical-align: super;
    line-height: 0;
}}
.citation-toggle {{
    position: absolute;
    opacity: 0;
    pointer-events: none;
}}
.citation-trigger {{
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 1rem;
    height: 1rem;
    padding: 0 0.24rem;
    border-radius: 999px;
    border: 1px solid #bfdbfe;
    background: #eff6ff;
    color: #0a5ca8;
    font-size: 0.62rem;
    font-weight: 800;
    line-height: 1;
    box-shadow: 0 1px 2px rgba(15,23,42,0.08);
}}
.citation-trigger:hover {{
    background: #dbeafe;
    border-color: #93c5fd;
}}
.citation-modal {{
    display: none;
    position: fixed;
    inset: 0;
    z-index: 3000;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background: rgba(15,23,42,0.28);
    backdrop-filter: blur(2px);
}}
.citation-toggle:checked ~ .citation-modal {{
    display: flex;
}}
.citation-popover {{
    position: relative;
    width: min(820px, calc(100vw - 2rem));
    max-height: 72vh;
    overflow: auto;
    background: #ffffff;
    border: 1px solid #dbe3ef;
    border-radius: 12px;
    box-shadow: 0 24px 70px rgba(15,23,42,0.28);
    padding: 1rem;
}}
.citation-close {{
    position: sticky;
    top: 0;
    z-index: 1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.75rem;
    height: 1.75rem;
    border-radius: 999px;
    border: 1px solid #cbd5e1;
    background: #ffffff;
    color: #334155;
    cursor: pointer;
    font-size: 1.05rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 0.5rem;
}}
.citation-close:hover {{
    background: #f1f5f9;
}}
.citation-title {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    color: #0f172a;
    font-weight: 700;
    margin-bottom: 0.65rem;
}}
.citation-page-block {{
    padding-top: 0.85rem;
    margin-top: 0.85rem;
    border-top: 1px solid #e2e8f0;
}}
.citation-page-block:first-of-type {{
    padding-top: 0;
    margin-top: 0;
    border-top: none;
}}
.citation-page-heading {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    color: #0f172a;
    font-weight: 800;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}}
.citation-source {{
    color: #64748b;
    font-size: 0.76rem;
    font-weight: 500;
    overflow-wrap: anywhere;
    margin-bottom: 0.7rem;
}}
.citation-page-img {{
    width: 100%;
    max-height: 460px;
    object-fit: contain;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-bottom: 0.75rem;
}}
.citation-page-text {{
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    background: #f8fafc;
    color: #334155;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.75rem;
    font-size: 0.82rem;
    line-height: 1.45;
}}
.citation-page-text mark {{
    background: #fff3a3;
    color: inherit;
    padding: 0.04rem 0.1rem;
    border-radius: 3px;
}}
[data-testid="stChatInput"] {{
    position: fixed;
    bottom: 0;
    /* Match the playground content column width. */
    left: max(2.5rem, calc(50vw - {_CHAT_HALF_PX}px));
    right: max(2.5rem, calc(50vw - {_CHAT_HALF_PX}px));
    width: auto;
    z-index: 999;
    background: transparent;
    padding: 0.75rem 0 1.1rem 0;
    border-top: none;
    box-sizing: border-box;
}}
/* Fill the fixed chat bar */
[data-testid="stChatInput"] > div {{
    position: relative;
    max-width: 100%;
    width: 100%;
    margin: 0;
}}
/* Keep Streamlit widget wrapper transparent */
[data-testid="stChatInput"] > div > * {{
    width: 100% !important;
    box-sizing: border-box !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
/* Keep input and send button in one centered row */
[data-testid="stChatInput"] div:has([data-testid="stChatInputTextArea"]):has([data-testid="stChatInputSubmitButton"]) {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: space-between !important;
    flex: 1 1 auto !important;
    width: 100% !important;
    max-width: 100% !important;
    align-self: stretch !important;
    box-sizing: border-box !important;
    min-height: 54px !important;
    padding: 5px 8px 5px 16px !important;
    border: 1px solid #d7dee8 !important;
    border-radius: 28px !important;
    background: #ffffff !important;
    box-shadow: none !important;
    transition: border-color 0.15s ease !important;
}}
[data-testid="stChatInput"] div:has([data-testid="stChatInputTextArea"]):has([data-testid="stChatInputSubmitButton"]):focus-within {{
    border-color: {_BLUE} !important;
    box-shadow: none !important;
}}
/* Let textarea grow; keep actions compact */
[data-testid="stChatInput"] div:has([data-testid="stChatInputTextArea"]):has([data-testid="stChatInputSubmitButton"]) > *:has([data-testid="stChatInputTextArea"]) {{
    flex: 1 1 auto !important;
    min-width: 0 !important;
    width: auto !important;
    max-width: 100% !important;
}}
[data-testid="stChatInput"] *:has(> [data-testid="stChatInputTextArea"]) {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}}
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="base-input"],
[data-testid="stChatInput"] [data-baseweb="input"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
/* Shrink right action cluster to content */
[data-testid="stChatInput"] div:has([data-testid="stChatInputTextArea"]):has([data-testid="stChatInputSubmitButton"]) > *:last-child {{
    width: auto !important;
    flex-shrink: 0 !important;
}}
/* Keep button inside input pill */
[data-testid="stChatInput"] div:has([data-testid="stChatInputSubmitButton"]) {{
    position: relative !important;
    display: flex !important;
    align-items: center !important;
}}
[data-testid="stChatInput"] textarea {{
    appearance: none !important;
    -webkit-appearance: none !important;
    border-radius: 0 !important;
    border: none !important;
    padding: 0.55rem 0.75rem 0.55rem 0 !important;
    min-height: 42px !important;
    box-shadow: none !important;
    background: transparent !important;
    font-size: 0.98rem !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    resize: none !important;
}}
/* Override inline fit-content width from BaseWeb */
[data-testid="stChatInput"] textarea[data-testid="stChatInputTextArea"] {{
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}}
[data-testid="stChatInput"] textarea:focus {{
    border-color: transparent !important;
    box-shadow: none !important;
    outline: none !important;
}}
[data-testid="stChatInput"] [data-testid="stChatInputSubmitButton"] {{
    position: relative !important;
    right: auto !important;
    top: auto !important;
    bottom: auto !important;
    transform: none !important;
    align-self: center !important;
    margin: 0 !important;
    z-index: 30 !important;
    width: 34px !important;
    height: 34px !important;
    min-width: 34px !important;
    min-height: 34px !important;
    border-radius: 50% !important;
    border: none !important;
    background: {_BLUE} !important;
    color: #ffffff !important;
    box-shadow: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}
[data-testid="stChatInput"] [data-testid="stChatInputSubmitButton"]:not(:disabled):hover {{
    background: {_BLUE_LIGHT} !important;
    color: #ffffff !important;
}}
[data-testid="stChatInput"] [data-testid="stChatInputSubmitButton"]:disabled {{
    opacity: 1 !important;
    background: #e2e8f0 !important;
    color: #94a3b8 !important;
    box-shadow: none !important;
}}
.playground-hero {{
    max-width: {_CHAT_COL_MAX_PX}px;
    margin: 0 auto 1.25rem auto;
    text-align: left;
}}
.playground-hero .eyebrow {{
    color: #444746;
    font-size: 1.35rem;
    margin: 0;
    font-weight: 400;
}}
.playground-hero .title {{
    margin: 0.35rem 0 0;
    font-size: 2.75rem;
    font-weight: 400;
    letter-spacing: -0.03em;
    color: #1f1f1f;
}}
.chat-control-caption {{
    color: #5f6368;
    font-size: 0.9rem;
}}
/* nicer top control buttons */
div.stButton > button[kind="secondary"],
div.stButton > button[kind="tertiary"] {{
    border-radius: 999px !important;
    border: 1px solid #d0d7e2 !important;
    background: #ffffff !important;
    color: #1f1f1f !important;
    font-weight: 600 !important;
    padding: 0.45rem 1rem !important;
    box-shadow: 0 1px 4px rgba(15,23,42,0.06) !important;
}}
div.stButton > button[kind="secondary"]:hover,
div.stButton > button[kind="tertiary"]:hover {{
    border-color: #aecbfa !important;
    box-shadow: 0 4px 12px rgba(66,133,244,0.14) !important;
}}

/* ── alerts ── */
.empty-state {{
    background: white;
    border: 1px solid #eef2f7;
    border-radius: 16px;
    padding: 3rem 2rem;
    text-align: center;
    color: {_MUTED};
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
}}
.empty-state .ico {{
    font-size: 2.8rem; margin-bottom: 0.4rem;
}}
.empty-state h4 {{
    color: {_INK}; margin: 0 0 0.3rem 0; font-weight: 700;
}}
</style>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

API_URL = os.getenv("API_URL", "http://localhost:8000")
STRICT_ABSTENTION_TEXT = "I cannot answer from the provided documents."
FRIENDLY_ABSTENTION_TEXT = (
    "I could not find this in the indexed documents. Try asking about a specific "
    "section, topic, or upload another PDF. (._.)"
)


def _get(path: str) -> tuple[Any, str | None]:
    try:
        import urllib.request
        with urllib.request.urlopen(f"{API_URL}{path}", timeout=5) as r:
            return json.loads(r.read()), None
    except Exception as exc:
        return None, str(exc)


def _post(path: str, payload: dict) -> tuple[Any, str | None]:
    try:
        import urllib.request
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{API_URL}{path}", data=body, method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()), None
    except Exception as exc:
        return None, str(exc)


def _chat_transcript(messages: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages if m.get("content")
    )


def _history_payload(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    payload: list[dict[str, str]] = []
    for message in messages:
        role = str(message.get("role", "user"))
        content = str(message.get("content", "")).strip()
        if content:
            payload.append({"role": role, "content": content})
    return payload


def _is_help_question(prompt: str) -> bool:
    normalized = re.sub(r"[^a-z0-9\s]", " ", prompt.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return bool(
        re.search(r"\b(how|what)\s+can\s+(you|u|codex)\s+(do|help)\b", normalized)
        or re.search(r"\b(can|could)\s+(you|u|codex)\s+help\b", normalized)
        or normalized in {"help", "what can you do", "what can u do", "how can you help me", "how can u help me"}
    )


def _help_answer() -> str:
    return (
        "I am here to help you work with your indexed documents. You can ask me to summarize a PDF, "
        "explain a topic, find where something is mentioned, compare sections, extract requirements, "
        "or answer questions with page references. When I use the documents, I show citation icons so "
        "you can open the referenced pages directly."
    )


def _display_answer_text(answer_text: str) -> str:
    return FRIENDLY_ABSTENTION_TEXT if answer_text.strip() == STRICT_ABSTENTION_TEXT else answer_text


def _strip_citation_summary(text: str) -> str:
    return re.sub(r"\n+\s*_?Citations:\s*(?:\[[^\]]+\]\s*,?\s*)+_?\s*$", "", text).strip()


def _highlight_chunk(page_text: str, chunk_text: str | None) -> str:
    safe_page = html.escape(page_text)
    if not chunk_text:
        return safe_page

    page_pos = page_text.find(chunk_text)
    if page_pos < 0:
        return safe_page

    before = html.escape(page_text[:page_pos])
    highlighted = html.escape(page_text[page_pos:page_pos + len(chunk_text)])
    after = html.escape(page_text[page_pos + len(chunk_text):])
    return f"{before}<mark>{highlighted}</mark>{after}"


def _clean_doc_title(citation: dict[str, Any]) -> str:
    raw_title = str(citation.get("title") or "").strip()
    source = str(citation.get("source") or "").strip()
    if not raw_title and source:
        raw_title = Path(source).stem
    raw_title = raw_title or str(citation.get("doc_id") or "Source")
    return re.sub(r"^\d+_", "", raw_title)


def _citation_label(citation: dict[str, Any]) -> str:
    return f"{_clean_doc_title(citation)} · page {citation.get('page', '?')}"


def _citation_table_rows(citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for citation in citations:
        document = _clean_doc_title(citation)
        page = str(citation.get("page", "–"))
        key = (document, page)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "Document": document,
                "Page": page,
                "Source": citation.get("source") or "–",
            }
        )
    return rows


def _citation_page_block_html(citation: dict[str, Any]) -> str:
    title = _clean_doc_title(citation)
    page_label = f"page {citation.get('page', '?')}"
    source = citation.get("source") or ""
    page_text = citation.get("page_text") or citation.get("chunk_text") or ""
    chunk_text = citation.get("chunk_text") or citation.get("quote")
    page_image = citation.get("page_image")

    image_html = (
        f'<img class="citation-page-img" src="{html.escape(page_image)}" alt="PDF page {html.escape(str(citation.get("page", "")))}">'
        if page_image else ""
    )
    text_html = (
        f'<div class="citation-page-text">{_highlight_chunk(page_text, chunk_text)}</div>'
        if page_text else '<div class="citation-page-text">No page preview is available for this source.</div>'
    )
    source_html = (
        f'<div class="citation-source">{html.escape(source)}</div>'
        if source else ""
    )
    return (
        '<div class="citation-page-block">'
        f'<div class="citation-page-heading"><span>{html.escape(title)}</span><span>{html.escape(page_label)}</span></div>'
        f'{source_html}{image_html}{text_html}'
        '</div>'
    )


def _citation_details_html(
    citation: dict[str, Any],
    ordinal: int,
    modal_id: str | None = None,
) -> str:
    return _citation_group_html([citation], ordinal, modal_id)


def _citation_group_html(
    citations: list[dict[str, Any]],
    ordinal: int,
    modal_id: str | None = None,
) -> str:
    modal_id = modal_id or f"citation-{uuid.uuid4().hex}"
    title = "Reference" if len(citations) == 1 else f"{len(citations)} references"
    labels = ", ".join(_citation_label(citation) for citation in citations)
    page_blocks = "".join(_citation_page_block_html(citation) for citation in citations)
    return (
        '<span class="citation-detail">'
        f'<input class="citation-toggle" id="{html.escape(modal_id)}" type="checkbox">'
        f'<label class="citation-trigger" for="{html.escape(modal_id)}" title="{html.escape(labels)}">{ordinal}</label>'
        '<span class="citation-modal">'
        '<span class="citation-popover">'
        f'<label class="citation-close" for="{html.escape(modal_id)}" title="Close">x</label>'
        f'<div class="citation-title"><span>{html.escape(title)}</span><span>{html.escape(labels)}</span></div>'
        f'{page_blocks}'
        '</span>'
        '</span>'
        '</span>'
    )


def _render_answer_html(
    text: str,
    citations: list[dict[str, Any]] | None = None,
) -> str:
    clean_text = _strip_citation_summary(text or "")
    safe_text = html.escape(clean_text)
    citations = citations or []
    occurrence = 0
    citation_index = 0
    modal_prefix = f"citation-{uuid.uuid4().hex}"

    def replace(match: re.Match[str]) -> str:
        nonlocal occurrence, citation_index
        refs = re.findall(r"([A-Za-z0-9_\-]+):p(\d+)", match.group(1))
        if not refs:
            return match.group(0)
        occurrence += 1
        citation_group = citations[citation_index: citation_index + len(refs)]
        citation_index += len(refs)
        if len(citation_group) < len(refs):
            citation_group = [
                {"doc_id": doc_id, "page": int(page)}
                for doc_id, page in refs
            ]
        return _citation_group_html(
            citation_group,
            occurrence,
            f"{modal_prefix}-{occurrence}",
        )

    rendered = re.sub(
        r"\[((?:[A-Za-z0-9_\-]+:p\d+\s*(?:,\s*)?)+)\]",
        replace,
        safe_text,
    )
    if occurrence == 0 and citations:
        rendered += "<br><br>" + " ".join(
            _citation_details_html(citation, index, f"{modal_prefix}-{index}")
            for index, citation in enumerate(citations, start=1)
        )
    rendered = rendered.replace("\n", "<br>")
    return f'<div class="assistant-answer">{rendered}</div>'


def _gemini_complete(messages: list[dict[str, str]]) -> tuple[str | None, str | None]:
    """Direct Gemini call for Playground proof-of-concept."""
    api_key = (
        os.getenv("GEMINI_API_KEY", "").strip()
        or os.getenv("GOOGLE_API_KEY", "").strip()
        or os.getenv("GOOGLE_GENAI_API_KEY", "").strip()
    )
    if not api_key:
        return (
            None,
            "No Gemini API key found. Set GEMINI_API_KEY in `code/.env` "
            "(or export it before `streamlit run`).",
        )

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    try:
        from google import genai

        # Send a simple text transcript for robust compatibility.
        transcript = _chat_transcript(messages)
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=(
                "You are a helpful assistant for PDF/document Q&A.\n"
                "Keep answers clear and concise.\n\n"
                f"{transcript}\nASSISTANT:"
            ),
        )
        text = (response.text or "").strip()
        if not text:
            return None, "Gemini returned an empty response."
        return text, None
    except Exception as exc:
        return None, f"Gemini error: {exc}"


def _hf_fallback_models() -> list[str]:
    raw = os.getenv("HF_MODEL_FALLBACK", "").strip()
    extra = [m.strip() for m in raw.split(",") if m.strip()]
    defaults = [
        os.getenv("HF_MODEL", "mistralai/Mistral-Nemo-Instruct-2407").strip(),
        "mistralai/Mistral-Nemo-Instruct-2407",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "Qwen/Qwen2.5-1.5B-Instruct",
    ]
    seen: set[str] = set()
    out: list[str] = []
    for m in extra + defaults:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _strip_prompt_prefix(text: str, prompt: str) -> str:
    t = text.strip()
    if t.startswith(prompt):
        return t[len(prompt):].strip()
    return t


def _coerce_hf_text_generation_output(generated: object) -> str:
    if isinstance(generated, str):
        return generated.strip()
    gt = getattr(generated, "generated_text", None)
    if isinstance(gt, str) and gt.strip():
        return gt.strip()
    if isinstance(generated, (list, tuple)):
        return "".join(
            str(x) if not isinstance(x, str) else x for x in generated
        ).strip()
    if isinstance(generated, Iterable):
        return "".join(str(x) for x in generated).strip()
    return str(generated).strip()


def _exc_detail(exc: BaseException) -> str:
    """HF/API errors sometimes have an empty `.args`; avoid silent empty strings in logs."""
    s = str(exc).strip()
    if s:
        return s
    return f"{type(exc).__name__}"


def _hf_chat_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """OpenAI-style messages for InferenceClient.chat_completion."""
    system = (
        "You are a helpful assistant for PDF/document Q&A. "
        "Keep answers clear and concise."
    )
    out: list[dict[str, str]] = [{"role": "system", "content": system}]
    for m in messages:
        raw = (m.get("content") or "").strip()
        if not raw:
            continue
        role = (m.get("role") or "user").lower().strip()
        if role not in ("user", "assistant", "system"):
            role = "user"
        out.append({"role": role, "content": raw})
    return out


def _huggingface_try_model(
    model: str, api_token: str, messages: list[dict[str, str]]
) -> tuple[str | None, str | None]:
    """HF routing: conversational models (e.g. Llama on Novita) need chat_completion, not text_generation."""
    try:
        from huggingface_hub import InferenceClient
    except ImportError:
        return None, "huggingface_hub not installed (pip install huggingface-hub)."

    hf_msgs = _hf_chat_messages(messages)
    prompt = (
        "You are a helpful assistant for PDF/document Q&A.\n"
        "Keep answers clear and concise.\n\n"
        f"{_chat_transcript(messages)}\nASSISTANT:"
    )

    chat_notes: list[str] = []
    try:
        client = InferenceClient(model=model, token=api_token)
        completion = client.chat_completion(
            hf_msgs,
            max_tokens=512,
            temperature=0.2,
        )
        choice0 = completion.choices[0] if completion.choices else None
        assistant_msg = choice0.message if choice0 else None
        raw = (
            ((assistant_msg.content or "").strip()) if assistant_msg else ""
        )
        if assistant_msg is not None and assistant_msg.reasoning:
            reasoning = assistant_msg.reasoning.strip()
            if reasoning and reasoning not in raw:
                raw = f"{reasoning}\n\n{raw}".strip() if raw else reasoning
        if raw:
            return raw, None
        if choice0:
            chat_notes.append(f"finish_reason={choice0.finish_reason!r}")
        chat_notes.append("no assistant content in chat_completion response")
    except Exception as chat_exc:
        chat_notes.append(_exc_detail(chat_exc))

    chat_tail = "; ".join(chat_notes)

    try:
        client = InferenceClient(model=model, token=api_token)
        generated = client.text_generation(
            prompt,
            max_new_tokens=512,
            temperature=0.2,
            return_full_text=False,
        )
        out = _strip_prompt_prefix(
            _coerce_hf_text_generation_output(generated), prompt
        )
        if out:
            return out, None
        return None, f"{chat_tail}; text_generation returned empty."
    except Exception as text_exc:
        return None, f"{chat_tail}; text_generation: {_exc_detail(text_exc)}"


def _huggingface_complete(messages: list[dict[str, str]]) -> tuple[str | None, str | None]:
    """Try HF inference with one or more model IDs (Llama is often 404 on free-tier API)."""
    api_token = (
        os.getenv("HF_API_TOKEN", "").strip()
        or os.getenv("HUGGINGFACEHUB_API_TOKEN", "").strip()
        or os.getenv("HUGGINGFACE_API_TOKEN", "").strip()
    )
    if not api_token:
        return None, "No Hugging Face token found. Set HF_API_TOKEN in `code/.env`."

    errors: list[str] = []
    for model in _hf_fallback_models():
        answer, err = _huggingface_try_model(model, api_token, messages)
        if answer:
            return answer, None
        errors.append(f"{model}: {err or '(unknown error)'}")

    return None, " | ".join(errors) if errors else "Hugging Face fallback failed."


def _chat_complete(messages: list[dict[str, str]]) -> tuple[str | None, str | None, str]:
    """Try Gemini first, then Hugging Face when Gemini is unavailable/quota-limited."""
    answer, gemini_err = _gemini_complete(messages)
    if answer:
        return answer, None, "gemini"

    answer, hf_err = _huggingface_complete(messages)
    if answer:
        return answer, None, "huggingface"

    return None, f"{gemini_err}\n\nFallback also failed: {hf_err}", "none"


def _logo_b64() -> str | None:
    logo = _UI_DIR / "assets" / "tubs_logo.png"
    return base64.b64encode(logo.read_bytes()).decode() if logo.exists() else None


def _section(title: str) -> None:
    import streamlit as st
    st.markdown(
        f"<div class='section-h'><div class='bar'></div><h3>{title}</h3></div>",
        unsafe_allow_html=True,
    )


def _empty(icon: str, title: str, msg: str) -> None:
    import streamlit as st
    st.markdown(
        f"<div class='empty-state'><div class='ico'>{icon}</div>"
        f"<h4>{title}</h4><p style='margin:0'>{msg}</p></div>",
        unsafe_allow_html=True,
    )


def _archive_current_chat_to_history() -> None:
    import streamlit as st

    messages: list[dict[str, Any]] = st.session_state.get("chat_messages", [])
    if not messages:
        return
    history: list[dict[str, object]] = st.session_state.setdefault("chat_history", [])
    first_user = next(
        (m.get("content", "") for m in messages if m.get("role") == "user"),
        "",
    ).strip()
    title = (first_user[:70] + "…") if len(first_user) > 70 else (first_user or "Untitled chat")
    history.append({"title": title, "messages": [dict(m) for m in messages]})


def _render_chat_history_panel() -> None:
    import streamlit as st

    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("chat_messages", [])
    history: list[dict[str, object]] = st.session_state["chat_history"]

    with st.sidebar:
        st.markdown("### Chats")
        if st.button("Close history", key="close_chat_history", use_container_width=True):
            st.session_state["show_chat_history"] = False
            st.rerun()
        query = st.text_input("Search", placeholder="Search conversations", label_visibility="collapsed")
        if st.button("＋ New chat", use_container_width=True):
            _archive_current_chat_to_history()
            st.session_state["chat_messages"] = []
            st.session_state.pop("traces", None)
            st.session_state["show_chat_history"] = False
            st.rerun()

        st.markdown("---")
        shown = 0
        for i in range(len(history) - 1, -1, -1):
            item = history[i]
            label = str(item.get("title", "Untitled chat"))
            if query and query.lower() not in label.lower():
                continue
            if st.button(label, key=f"history_chat_{i}", use_container_width=True):
                messages = item.get("messages", [])
                st.session_state["chat_messages"] = [
                    dict(message) for message in messages
                ] if isinstance(messages, list) else []
                st.session_state["show_chat_history"] = False
                st.rerun()
            shown += 1
        if shown == 0:
            st.caption("No matching chats." if query else "No chats yet.")


# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------


def _hero() -> None:
    import streamlit as st

    _, err = _get("/health")
    online = err is None
    dot_class = "dot-on" if online else "dot-off"
    status_text = "Backend online" if online else "Backend offline"

    logo_b64 = _logo_b64()
    logo_html = (
        f"<img class='hero-logo' src='data:image/png;base64,{logo_b64}'>"
        if logo_b64 else ""
    )

    st.markdown(
        f"""
        <div class='hero'>
            <div class='hero-left'>
                <h1>CoDex</h1>
                <p>Where your PDFs finally start talking back.</p>
                <div class='hero-status'>
                    <span class='dot {dot_class}'></span> {status_text}
                </div>
            </div>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------


def _tab_corpus() -> None:
    import streamlit as st

    def upload_display_name(source: str) -> str:
        return re.sub(r"^\d{13}_", "", Path(source).name)

    def is_already_indexed(upload_name: str, indexed_sources: set[str]) -> bool:
        safe_name = Path(upload_name).name
        return any(source == safe_name or source.endswith(f"_{safe_name}") for source in indexed_sources)

    def pdf_preview_html(source: str) -> str:
        path = Path(source)
        if not path.exists() or path.suffix.lower() != ".pdf":
            return "<p>PDF preview is not available for this file.</p>"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return (
            f'<iframe src="data:application/pdf;base64,{encoded}" '
            'width="100%" height="720" style="border:1px solid #e2e8f0;'
            'border-radius:8px;background:white;"></iframe>'
        )

    def show_pdf_preview(title: str, source: str) -> None:
        if hasattr(st, "dialog"):
            @st.dialog(title, width="large")
            def preview_dialog() -> None:
                st.markdown(pdf_preview_html(source), unsafe_allow_html=True)

            preview_dialog()
        else:
            st.markdown(f"#### {title}")
            st.markdown(pdf_preview_html(source), unsafe_allow_html=True)

    def show_chunks_preview(title: str, chunks: list[dict[str, Any]]) -> None:
        def render_chunks() -> None:
            if not chunks:
                st.info("No chunks are available for this document.")
                return
            for chunk in chunks:
                chunk_id = str(chunk.get("chunk_id", ""))
                page = chunk.get("page", "–")
                start = chunk.get("start", "–")
                end = chunk.get("end", "–")
                text = str(chunk.get("text", ""))
                with st.expander(f"{chunk_id} · page {page} · chars {start}-{end}"):
                    st.text_area(
                        "Chunk text",
                        value=text,
                        height=180,
                        label_visibility="collapsed",
                        key=f"chunk_text_{chunk_id}",
                    )

        if hasattr(st, "dialog"):
            @st.dialog(f"Chunks · {title}", width="large")
            def chunks_dialog() -> None:
                render_chunks()

            chunks_dialog()
        else:
            st.markdown(f"#### Chunks · {title}")
            render_chunks()

    def index_with_progress(paths: list[str], labels: list[str]) -> tuple[dict[str, Any] | None, str | None]:
        progress = st.progress(0)
        status = st.empty()
        total = len(paths)
        latest: dict[str, Any] | None = None

        for index, (path, label) in enumerate(zip(paths, labels, strict=True), start=1):
            status.markdown(f"Indexing **{html.escape(label)}** ({index}/{total})")
            res, err = _post("/index", {"paths": [path]})
            if err:
                progress.empty()
                status.empty()
                return None, f"{label}: {err}"
            latest = res
            progress.progress(index / total)

        status.markdown("Indexing complete.")
        return latest, None

    _section("Library overview")
    stats, err = _get("/stats")
    c1, c2, c3 = st.columns(3)
    c1.metric("Documents", stats.get("documents", "–") if not err else "–")
    c2.metric("Chunks",    stats.get("chunks", "–")    if not err else "–")
    c3.metric("Pages",     stats.get("pages", "–")     if not err else "–")

    documents, doc_err = _get("/documents")
    indexed_sources = {
        Path(str(document.get("source", ""))).name
        for document in documents or []
        if isinstance(document, dict)
    }
    _section("Indexed documents")
    if doc_err:
        st.error(f"Could not load indexed documents: {doc_err}")
    elif documents:
        header = st.columns([5, 1, 1, 1, 1])
        header[0].caption("Document")
        header[1].caption("Pages")
        header[2].caption("Chunks")
        header[3].caption("See file")
        header[4].caption("See chunks")

        selected_preview: tuple[str, str] | None = None
        selected_chunks: tuple[str, list[dict[str, Any]]] | None = None
        for index, document in enumerate(documents):
            source = str(document.get("source", ""))
            title = upload_display_name(source)
            row = st.columns([5, 1, 1, 1, 1])
            row[0].markdown(f"**{html.escape(title)}**")
            row[1].write(document.get("pages", 0))
            row[2].write(document.get("chunks", 0))
            if row[3].button("View", key=f"view_indexed_doc_{index}", use_container_width=True):
                selected_preview = (title, source)
            if row[4].button("Chunks", key=f"view_indexed_chunks_{index}", use_container_width=True):
                chunks = document.get("chunk_details", [])
                selected_chunks = (title, chunks if isinstance(chunks, list) else [])

        if selected_preview is not None:
            show_pdf_preview(*selected_preview)
        if selected_chunks is not None:
            show_chunks_preview(*selected_chunks)
    else:
        st.info("No documents indexed yet.")

    _section("Index new documents")
    upload_tab, path_tab = st.tabs(["☁️  Upload files", "🗂️  File paths"])

    with upload_tab:
        uploaded = st.file_uploader(
            "Upload",
            type=["pdf"], accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded:
            new_uploads = [
                uf for uf in uploaded if not is_already_indexed(uf.name, indexed_sources)
            ]
            if not new_uploads:
                st.info("All selected files are already indexed.")
            else:
                st.caption("New upload queue. These files are not indexed until you press Index.")
                st.markdown("<br>", unsafe_allow_html=True)
                for uf in new_uploads:
                    kb = len(uf.getvalue()) / 1024
                    size = f"{kb:.0f} KB" if kb < 1024 else f"{kb/1024:.1f} MB"
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:12px;"
                        f"background:white;border:1px solid #eef2f7;border-radius:12px;"
                        f"padding:10px 16px;margin-bottom:8px;"
                        f"box-shadow:0 1px 3px rgba(15,23,42,0.04)'>"
                        f"<div style='width:36px;height:36px;border-radius:8px;"
                        f"background:linear-gradient(135deg,{_BLUE},{_BLUE_LIGHT});"
                        f"display:flex;align-items:center;justify-content:center;color:white;"
                        f"font-weight:700;font-size:0.7rem'>PDF</div>"
                        f"<span style='flex:1;font-weight:500;color:{_INK}'>{uf.name}</span>"
                        f"<span style='color:{_MUTED};font-size:0.85rem'>{size}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                st.markdown("")
                c1, c2 = st.columns([1, 4])
                do_index = c1.button(
                    f"Index {len(new_uploads)} file{'s' if len(new_uploads) != 1 else ''}",
                    type="primary", key="btn_upload", use_container_width=True,
                )
                c2.caption("Files are sent to the backend for parsing and indexing.")
                if do_index:
                    saved: list[str] = []
                    labels: list[str] = []
                    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
                    for uf in new_uploads:
                        safe_name = Path(uf.name).name
                        p = _UPLOAD_DIR / f"{int(time.time() * 1000)}_{safe_name}"
                        p.write_bytes(uf.read())
                        saved.append(str(p))
                        labels.append(safe_name)
                    res, err = index_with_progress(saved, labels)
                    if err:
                        st.error(f"Indexing failed: {err}")
                    elif res is not None:
                        st.success(
                            f"✅ {res['documents']} doc(s) · {res['chunks']} chunks · "
                            f"{res['pages']} pages indexed."
                        )
                        st.rerun()

    with path_tab:
        st.caption("One absolute path per line (paths are read by the backend).")
        raw = st.text_area(
            "Paths", height=130,
            placeholder="/data/paper.pdf\n/data/report.pdf",
            label_visibility="collapsed",
        )
        if st.button("Index paths", type="primary", key="btn_paths"):
            paths = [p.strip() for p in raw.splitlines() if p.strip()]
            if not paths:
                st.error("Enter at least one path.")
            else:
                labels = [Path(path).name or path for path in paths]
                res, err = index_with_progress(paths, labels)
                if err:
                    st.error(f"Indexing failed: {err}")
                elif res is not None:
                    st.success(
                        f"✅ {res['documents']} doc(s) · {res['chunks']} chunks · "
                        f"{res['pages']} pages indexed."
                    )
                    st.rerun()


def _tab_playground() -> None:
    import streamlit as st

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    st.session_state.setdefault("chat_messages", [])
    st.session_state.setdefault("show_chat_history", False)
    chat_messages: list[dict[str, Any]] = st.session_state["chat_messages"]

    toggle_label = "Hide history" if st.session_state["show_chat_history"] else "History"
    toggle_col, _ = st.columns([0.14, 0.86])
    if toggle_col.button(toggle_label, key="toggle_chat_history", use_container_width=True):
        st.session_state["show_chat_history"] = not st.session_state["show_chat_history"]
        st.rerun()

    if st.session_state["show_chat_history"]:
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] {
                display: block !important;
                position: fixed !important;
                left: 0 !important;
                top: 0 !important;
                bottom: 0 !important;
                width: 320px !important;
                min-width: 320px !important;
                max-width: 320px !important;
                background: #ffffff !important;
                border-right: 1px solid #e5e7eb !important;
                box-shadow: 0 16px 40px rgba(15, 23, 42, 0.16) !important;
                z-index: 10000 !important;
            }
            [data-testid="stSidebar"] > div:first-child {
                width: 320px !important;
                min-width: 320px !important;
                max-width: 320px !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        _render_chat_history_panel()

    _render_playground_chat(model_name, chat_messages)


def _render_playground_chat(model_name: str, chat_messages: list[dict[str, Any]]) -> None:
    import streamlit as st

    st.markdown(
        f'<div class="gemini-chat-toolbar"><span class="chat-control-caption">RAG backend · Generator: <code>{model_name}</code></span></div>',
        unsafe_allow_html=True,
    )

    if not chat_messages:
        st.markdown(
            """
            <div class="playground-hero">
                <p class="title">What should CoDex look up?</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="gemini-chat-wrap">', unsafe_allow_html=True)
    for msg in chat_messages:
        if msg["role"] == "user":
            safe = html.escape(msg["content"])
            st.markdown(
                f'<div class="gemini-row-user"><span class="gemini-bubble-user">{safe}</span></div>',
                unsafe_allow_html=True,
            )
        else:
            c_star, c_body = st.columns([0.065, 0.935])
            with c_star:
                st.markdown(
                    '<div class="gemini-star" aria-hidden="true">✦</div>',
                    unsafe_allow_html=True,
                )
            with c_body:
                if msg.get("citations"):
                    st.markdown(
                        _render_answer_html(
                            str(msg.get("content", "")),
                            msg.get("citations", []),
                        ),
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(str(msg.get("content", "")))

    # room so the last message is not hidden under the fixed composer
    st.markdown('<div style="height:5.75rem"></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    prompt = st.chat_input("...")
    if prompt:
        chat_messages.append({"role": "user", "content": prompt})
        if _is_help_question(prompt):
            chat_messages.append({"role": "assistant", "content": _help_answer()})
        else:
            with st.spinner("Thinking…"):
                t0 = time.perf_counter()
                res, err = _post(
                    "/query",
                    {"question": prompt, "history": _history_payload(chat_messages[:-1]), "top_k": 10},
                )
                elapsed = (time.perf_counter() - t0) * 1000
            if err:
                chat_messages.append({"role": "assistant", "content": f"Error: {err}"})
            else:
                citations = res.get("citations", [])
                raw_answer_text = res.get("answer") or ""
                answer_text = _display_answer_text(raw_answer_text)
                chat_messages.append({
                    "role": "assistant",
                    "content": answer_text,
                    "citations": citations,
                    "confidence": res.get("confidence", 0.0),
                })
                st.session_state.setdefault("traces", []).append(
                    {
                        "question": prompt,
                        "answer": answer_text,
                        "raw_answer": raw_answer_text,
                        "confidence": res.get("confidence", 0.0),
                        "abstained": res.get("abstained", False),
                        "latency_ms": res.get("latency_ms", {"wall": elapsed}),
                        "tokens": res.get("tokens", {"input": 0, "output": 0}),
                        "cost_eur": res.get("cost_eur", 0.0),
                        "citations": citations,
                        "wall_ms": elapsed,
                    }
                )
        st.rerun()


def _tab_traces() -> None:
    import streamlit as st

    _section("Query traces (this session)")
    traces: list[dict] = st.session_state.get("traces", [])

    if not traces:
        _empty("🔍", "No queries yet", "Head to the Playground tab to ask something.")
        return

    import pandas as pd

    rows = []
    for t in reversed(traces):
        lat = t.get("latency_ms", {})
        tok = t.get("tokens", {})
        rows.append({
            "Question":      t["question"][:55] + ("…" if len(t["question"]) > 55 else ""),
            "Conf.":         f"{t['confidence']:.0%}",
            "Abstained":     "✓" if t["abstained"] else "",
            "Total ms":      f"{t.get('wall_ms', 0):.0f}",
            "Retrieval ms":  f"{lat.get('retrieval', 0):.0f}",
            "Generation ms": f"{lat.get('generation', 0):.0f}",
            "Input tok.":    tok.get("input", "–"),
            "Output tok.":   tok.get("output", "–"),
            "Cost €":        f"{t['cost_eur']:.5f}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    _section("Detail view")
    idx = st.selectbox(
        "Select query",
        range(len(traces)),
        format_func=lambda i: traces[-(i+1)]["question"][:80],
        label_visibility="collapsed",
    )
    if idx is not None:
        t = traces[-(idx+1)]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<p style='color:{_MUTED};font-weight:600;font-size:0.78rem;"
                        f"text-transform:uppercase;letter-spacing:0.08em'>Latency (ms)</p>",
                        unsafe_allow_html=True)
            st.json(t.get("latency_ms", {}))
        with c2:
            st.markdown(f"<p style='color:{_MUTED};font-weight:600;font-size:0.78rem;"
                        f"text-transform:uppercase;letter-spacing:0.08em'>Tokens</p>",
                        unsafe_allow_html=True)
            st.json(t.get("tokens", {}))
        citation_rows = _citation_table_rows(t.get("citations", []))
        if citation_rows:
            st.markdown(f"<p style='color:{_MUTED};font-weight:600;font-size:0.78rem;"
                        f"text-transform:uppercase;letter-spacing:0.08em;margin-top:1rem'>Cited pages</p>",
                        unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(citation_rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No cited pages for this answer.")


def _tab_evaluation() -> None:
    import streamlit as st

    _section("Latest evaluation report")

    report_path = Path("reports/report.json")
    if not report_path.exists():
        _empty("📋", "No report yet", "Run `make smoke` (or `make eval`) to generate one.")
        return

    with report_path.open() as f:
        report: dict = json.load(f)

    meta = report.get("meta", {})
    st.markdown(
        f"<div style='display:flex;gap:1.2rem;flex-wrap:wrap;color:{_MUTED};"
        f"font-size:0.85rem;margin-bottom:1.2rem'>"
        f"<span>Suite: <b style='color:{_INK}'>{meta.get('suite','–')}</b></span>"
        f"<span>Items: <b style='color:{_INK}'>{meta.get('n_items','–')}</b></span>"
        f"<span>Generated: <b style='color:{_INK}'>{meta.get('generated_at','–')}</b></span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    eff = report.get("efficiency", {})
    if eff:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg latency",  f"{eff.get('avg_latency_ms',0):.0f} ms")
        c2.metric("p95 latency",  f"{eff.get('p95_latency_ms',0):.0f} ms")
        c3.metric("Total tokens", eff.get("total_tokens", "–"))
        c4.metric("Total cost",   f"€ {eff.get('total_cost_eur',0):.4f}")

    categories = [k for k in report if k not in ("meta", "efficiency")]
    if categories:
        _section("Metrics by category")
        import pandas as pd
        tabs = st.tabs([c.capitalize() for c in categories])
        for tab, cat in zip(tabs, categories, strict=True):
            with tab:
                data = report[cat]
                if isinstance(data, dict):
                    df = pd.DataFrame([{"Metric": k, "Value": v} for k, v in data.items()])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.write(data)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import streamlit as st

    icon = str(_FAVICON) if _FAVICON.is_file() else "📄"
    st.set_page_config(
        page_title="CoDex · TU Braunschweig",
        layout="wide",
        page_icon=icon,
        initial_sidebar_state="collapsed",
    )
    st.markdown(_CSS, unsafe_allow_html=True)

    _hero()

    corpus_tab, playground_tab, traces_tab, eval_tab = st.tabs(
        ["📁  Corpus", "💬  Playground", "📊  Traces", "🧪  Evaluation"]
    )
    with corpus_tab:
        _tab_corpus()
    with playground_tab:
        _tab_playground()
    with traces_tab:
        _tab_traces()
    with eval_tab:
        _tab_evaluation()


if __name__ == "__main__":  # pragma: no cover
    main()
