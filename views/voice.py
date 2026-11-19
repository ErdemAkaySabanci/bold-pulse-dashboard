import streamlit as st

from src import insights
from src import metrics as M
from src.data import load
from src.ui import components as C, fmt

rv_all = load.reviews()
classified = load.is_classified() and "topics" in rv_all and rv_all["is_classified"].any()
n = len(rv_all)
neg = int((rv_all["rating_bucket"] == "negative").sum())
neu = int((rv_all["rating_bucket"] == "neutral").sum())
ads = len(insights.ad_mentions(rv_all))

C.hero(
    "Halkın Nabzı",
    "Oyuncular tam olarak ne söylüyor?",
    f"<b>{fmt.num(n)}</b> yazılı yorumun <b>{neg}</b>'i olumsuz (1–2★), <b>{neu}</b>'i nötr (3★). Yorum sayısı az "
    "olduğu için burada yüzdeler yerine yorumların kendisi konuşuyor.",
    stats=[(fmt.num(n), "yazılı yorum"), (str(neg), "olumsuz · 1–2★"), (str(neu), "nötr · 3★"),
           (f"{ads} / {neg + neu}", "1–3★ yorumda reklam geçiyor")],
)

C.data_source(C.reviews_source(rv_all, "konular: Gemini, 1–3★ yorumlar elle kontrol edildi"
                                 if classified else ""))

SORTS = {
    "En yeni": (["date"], [False]),
    "En eski": (["date"], [True]),
    "En düşük yıldız": (["rating", "date"], [True, False]),
    "En çok beğenilen": (["thumbs_up", "date"], [False, False]),
}
TONES = {"Olumsuz · 1–2★": "negative", "Nötr · 3★": "neutral", "Olumlu · 4–5★": "positive"}

f1, f2, f3 = st.columns([1, 1.25, 1.4])
with f1:
    store = st.segmented_control("Mağaza", ["Tümü", "App Store", "Google Play"], default="Tümü",
                                 key="voice_store")
with f2:
    tone = st.segmented_control("Ton", ["Tümü", *TONES], default="Tümü", key="voice_tone")
with f3:
    sort = st.segmented_control("Sırala", list(SORTS), default="En yeni", key="voice_sort")

rv = rv_all
if store and store != "Tümü":
    rv = rv[rv["store"] == ("app_store" if store == "App Store" else "google_play")]
if tone and tone != "Tümü":
    rv = rv[rv["rating_bucket"] == TONES[tone]]

# Category filter: AI topics (human-checked on the sample) plus two behaviour labels.
pick = None
if classified:
    topic_sets = rv_all["topics"].map(M.split_labels)
    counts = {k: int(topic_sets.map(lambda ls, k=k: k in ls).sum()) for k in fmt.TOPIC}
    cats = {k: f"{fmt.topic(k)} · {c}" for k, c in sorted(counts.items(), key=lambda x: -x[1]) if c >= 2}
    cats["_churn"] = f"🚪 Oyunu bırakanlar · {int(rv_all['churn_signal'].sum())}"
    cats["_request"] = f"🙏 İstekler · {int(rv_all['is_request'].sum())}"
    pick = st.pills("Kategori", list(cats), format_func=cats.get, key="voice_cat")
    if pick == "_churn":
        rv = rv[rv["churn_signal"]]
    elif pick == "_request":
        rv = rv[rv["is_request"]]
    elif pick:
        rv = rv[rv["topics"].map(lambda v: pick in M.split_labels(v))]

by, asc = SORTS.get(sort or "En yeni")
rv = rv.sort_values(by, ascending=asc)

C.note(f"<b>{len(rv)}</b> yorum gösteriliyor."
       + (" Kategoriler yapay zekâ ile etiketlendi; 1–3★ yorumların hepsi elle kontrol edildi. "
          "Bir yorum birden fazla kategoriye girebilir." if classified else ""))

if rv.empty:
    C.empty_state("Bu seçimde yorum yok", "Filtrelerden birini gevşetmeyi deneyin.")
for _, row in rv.iterrows():
    if pick == "_request" and row.get("request_text"):
        st.markdown(f"**İstek:** {row['request_text']}")
    C.quote(row)
