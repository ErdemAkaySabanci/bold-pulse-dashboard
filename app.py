"""PULSE — Oyuncu Analitiği / Player Analytics. Market Match! için yorum ve değerlendirme analitiği.

Run:  streamlit run app.py        English link: …/?lang=en
"""
import os

import streamlit as st

from src.data import load
from src.i18n import LANGS, T
from src.ui.components import sidebar_footer
from src.ui.theme import inject_css

# --- language: URL (?lang=en) on first load, then the session keeps it across pages
if "lang" not in st.session_state:
    qp = st.query_params.get("lang", "tr")
    st.session_state["lang"] = qp if qp in LANGS else "tr"
if st.session_state.get("lang_switch") is None:
    st.session_state["lang_switch"] = st.session_state["lang"].upper()


def _set_lang() -> None:
    v = st.session_state.get("lang_switch")
    if v:
        st.session_state["lang"] = v.lower()
    else:  # clicking the active option deselects it; keep the current language selected
        st.session_state["lang_switch"] = st.session_state["lang"].upper()


st.set_page_config(page_title=T("PULSE · Oyuncu Analitiği", "PULSE · Player Analytics"), page_icon="🛒",
                   layout="wide")
inject_css()
st.logo("assets/bold-wordmark-red.png", size="large")

# TR | EN switch, pinned to the top-right corner of every page (see .st-key-lang-switch in theme.py)
with st.container(key="lang-switch"):
    st.segmented_control("Dil / Language", ["TR", "EN"], key="lang_switch", on_change=_set_lang,
                         label_visibility="collapsed")
if st.query_params.get("lang") != st.session_state["lang"]:
    st.query_params["lang"] = st.session_state["lang"]

pages = {
    "Dashboard": [
        # The recommendations are the heart of the dashboard, so they open first.
        st.Page("views/recommendations.py", title=T("Benim Ürün Önerilerim", "My Recommendations"),
                icon=":material/lightbulb:", default=True),
        st.Page("views/overview.py", title=T("Genel Bakış", "Overview"), icon=":material/space_dashboard:"),
        st.Page("views/voice.py", title=T("Halkın Nabzı", "Player Pulse"), icon=":material/forum:"),
        st.Page("views/markets.py", title=T("Pazarlar & Platformlar", "Markets & Platforms"),
                icon=":material/public:"),
        st.Page("views/context.py", title=T("Sektörle Kıyas", "Industry Benchmark"), icon=":material/insights:"),
        st.Page("views/explorer.py", title=T("Yorum Database'i", "Review Database"),
                icon=":material/manage_search:"),
    ],
}
# Labeling tool is only for re-labelling locally: PULSE_TOOLS=1 streamlit run app.py
if os.getenv("PULSE_TOOLS") == "1":
    pages["Araçlar"] = [st.Page("views/labeling.py", title="Etiketleme", icon=":material/fact_check:")]
nav = st.navigation(pages)

ratings_total = int(
    load.ratings().query("(store == 'app_store' and scope == 'local') or "
                         "(store == 'google_play' and scope == 'global')")["rating_count"].sum()
)
sidebar_footer(len(load.reviews()), ratings_total, load.collected_at())

nav.run()
