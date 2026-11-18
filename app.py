"""PULSE — Oyuncu Analitiği. Market Match! için yorum ve değerlendirme analitiği.

Run:  streamlit run app.py
"""
import os

import streamlit as st

from src.data import load
from src.ui.components import sidebar_footer
from src.ui.theme import inject_css

st.set_page_config(page_title="PULSE · Oyuncu Analitiği", page_icon="🛒", layout="wide")
inject_css()
st.logo("assets/bold-wordmark-red.png", size="large")

pages = {
    "Dashboard": [
        st.Page("views/overview.py", title="Genel Bakış", icon=":material/space_dashboard:", default=True),
        st.Page("views/markets.py", title="Pazarlar & Platformlar", icon=":material/public:"),
        st.Page("views/voice.py", title="Oyuncu Sesi", icon=":material/forum:"),
        st.Page("views/recommendations.py", title="Benim Ürün Önerilerim", icon=":material/lightbulb:"),
        st.Page("views/explorer.py", title="Yorum Gezgini", icon=":material/manage_search:"),
        st.Page("views/method.py", title="Metodoloji & Veri Kalitesi", icon=":material/science:"),
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
