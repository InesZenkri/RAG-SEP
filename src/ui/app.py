"""Streamlit dashboard (M6).

Tabs to implement:
- Corpus: document list, indexing status, add-document form.
- Playground: question input, streamed answer with inline citations that
  expand to show the cited chunk, confidence bar, abstain banner.
- Traces: last N queries with per-stage latency, tokens, euro cost.
- Evaluation: latest run report (per-category tables + trend vs. previous run).

Run locally with: ``streamlit run src/ui/app.py``
"""

from __future__ import annotations


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Reliable PDF Search Agent", layout="wide")
    st.title("Reliable PDF Search Agent")
    st.info("UI scaffold. Tabs (Corpus / Playground / Traces / Evaluation) land in M6.")


if __name__ == "__main__":  # pragma: no cover
    main()
