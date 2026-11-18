"""Blind hand-labelling of a fixed 50-review sample. Gemini's labels are never shown here,
so the agreement reported on the Methodology page is an independent human check."""
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src import config
from src.data import load
from src.ui import components as C, fmt

SAMPLE_N = 50
SEED = 42
TOPIC_CODES = list(fmt.TOPIC)
COLUMNS = ["review_id", "topics", "level_mentions", "churn_signal", "monetization", "done", "labeled_at"]


def make_sample(rv: pd.DataFrame) -> pd.DataFrame:
    """All 1–3★ reviews plus a seeded random draw of positives, up to 50."""
    crit = rv[rv["rating_bucket"].isin(["negative", "neutral"])]
    pos = rv[rv["rating_bucket"] == "positive"].sample(
        n=min(SAMPLE_N - len(crit), int((rv["rating_bucket"] == "positive").sum())), random_state=SEED)
    ids = pd.concat([crit, pos]).sample(frac=1, random_state=SEED)["review_id"]
    return pd.DataFrame({"review_id": ids.values, "topics": "", "level_mentions": "",
                         "churn_signal": False, "monetization": "", "done": False, "labeled_at": ""})


def load_sheet(rv: pd.DataFrame) -> pd.DataFrame:
    if config.MANUAL_SAMPLE_CSV.exists():
        df = pd.read_csv(config.MANUAL_SAMPLE_CSV, dtype={"review_id": "string"}, keep_default_na=False)
    else:
        df = make_sample(rv)
        df.to_csv(config.MANUAL_SAMPLE_CSV, index=False, encoding="utf-8")
    for c in ("done", "churn_signal"):
        df[c] = df[c].astype(str).str.lower().eq("true")
    return df


rv = load.reviews()
sheet = load_sheet(rv)
n_done = int(sheet["done"].sum())

C.hero(
    "Araçlar · Etiketleme",
    "Yapay zekâyı kör testle doğrula",
    f"Sabit bir örneklemden seçilen <b>{len(sheet)}</b> yorumu sen etiketle: 1–3★ yorumların hepsi ve "
    "rastgele seçilmiş olumlu yorumlar. Gemini'nin etiketleri bu ekranda <b>gösterilmez</b>; "
    "uyum oranı Metodoloji sayfasında hesaplanır.",
    stats=[(f"{n_done} / {len(sheet)}", "etiketlendi")],
)
st.progress(n_done / len(sheet))

if "lab_i" not in st.session_state:
    pending = sheet.index[~sheet["done"]]
    st.session_state.lab_i = int(pending[0]) if len(pending) else 0
i = st.session_state.lab_i

nav1, nav2, nav3 = st.columns([1, 1, 3])
with nav1:
    if st.button("← Önceki", disabled=i == 0, width="stretch"):
        st.session_state.lab_i = i - 1
        st.rerun()
with nav2:
    if st.button("Sonraki →", disabled=i >= len(sheet) - 1, width="stretch"):
        st.session_state.lab_i = i + 1
        st.rerun()
with nav3:
    st.caption(f"Yorum {i + 1} / {len(sheet)}" + (" · ✓ etiketlendi" if sheet.at[i, "done"] else ""))

row = rv[rv["review_id"] == sheet.at[i, "review_id"]].iloc[0]
C.quote(row)

with st.form(f"label_{i}"):
    prev_topics = [t for t in sheet.at[i, "topics"].split(";") if t]
    topics = st.pills("Yorum hangi konulardan bahsediyor? (birden çok seçilebilir)", TOPIC_CODES,
                      selection_mode="multi", default=prev_topics, format_func=fmt.topic)
    prev_mon = [t for t in sheet.at[i, "monetization"].split(";") if t]
    mon = st.pills("Monetizasyon", list(fmt.MONETIZATION), selection_mode="multi", default=prev_mon,
                   format_func=lambda k: fmt.MONETIZATION[k])
    c1, c2 = st.columns(2)
    with c1:
        churn = st.toggle("Oyunu sildiğini / bıraktığını söylüyor", value=bool(sheet.at[i, "churn_signal"]))
    with c2:
        levels = st.text_input("Geçen seviye numaraları (virgülle)", value=sheet.at[i, "level_mentions"].replace(";", ", "))
    if st.form_submit_button("Kaydet & sonraki", type="primary", width="stretch"):
        nums = [s.strip() for s in levels.replace(";", ",").split(",") if s.strip().isdigit()]
        sheet.loc[i, ["topics", "level_mentions", "churn_signal", "monetization", "done", "labeled_at"]] = [
            ";".join(topics or []), ";".join(nums), bool(churn), ";".join(mon or []), True,
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
        sheet[COLUMNS].to_csv(config.MANUAL_SAMPLE_CSV, index=False, encoding="utf-8")
        load.validation.clear()
        nxt = sheet.index[(~sheet["done"]) & (sheet.index > i)]
        st.session_state.lab_i = int(nxt[0]) if len(nxt) else min(i + 1, len(sheet) - 1)
        st.rerun()

C.note("Etiketler <code>data/manual_sample.csv</code> dosyasına kaydedilir. Bu sayfa yerelde çalışırken "
       "yazar; yayınlanan sürümde kayıtlı sonuçlar Metodoloji'de gösterilir.")
