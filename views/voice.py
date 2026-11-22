import streamlit as st

from src import insights
from src import metrics as M
from src.data import load
from src.i18n import T
from src.ui import components as C, fmt

rv_all = load.reviews()
classified = load.is_classified() and "topics" in rv_all and rv_all["is_classified"].any()
n = len(rv_all)
neg = int((rv_all["rating_bucket"] == "negative").sum())
neu = int((rv_all["rating_bucket"] == "neutral").sum())
ads = len(insights.ad_mentions(rv_all))

C.hero(
    T("Halkın Nabzı", "Player Pulse"),
    T("Oyuncular tam olarak ne söylüyor?", "What exactly are players saying?"),
    T(f"<b>{fmt.num(n)}</b> yazılı yorumun <b>{neg}</b>'i olumsuz (1–2★), <b>{neu}</b>'i nötr (3★). Yorum sayısı az "
      "olduğu için burada yüzdeler yerine yorumların kendisi konuşuyor.",
      f"Of <b>{fmt.num(n)}</b> written reviews, <b>{neg}</b> are negative (1–2★) and <b>{neu}</b> neutral (3★). "
      "With this few reviews, the reviews themselves do the talking here instead of percentages."),
    stats=[(fmt.num(n), T("yazılı yorum", "written reviews")),
           (str(neg), T("olumsuz · 1–2★", "negative · 1–2★")),
           (str(neu), T("nötr · 3★", "neutral · 3★")),
           (f"{ads} / {neg + neu}", T("1–3★ yorumda reklam geçiyor", "1–3★ reviews mention ads"))],
)

C.data_source(C.reviews_source(rv_all, T("konular: Gemini, 1–3★ yorumlar elle kontrol edildi",
                                         "topics: Gemini, all 1–3★ reviews checked by hand")
                                 if classified else ""))

# Stable option keys; only the labels change with the language, so filters survive a switch.
SORTS = {
    "new": (T("En yeni", "Newest"), ["date"], [False]),
    "old": (T("En eski", "Oldest"), ["date"], [True]),
    "low": (T("En düşük yıldız", "Lowest stars"), ["rating", "date"], [True, False]),
    "liked": (T("En çok beğenilen", "Most liked"), ["thumbs_up", "date"], [False, False]),
}
STORES = {"all": T("Tümü", "All"), "app_store": "App Store", "google_play": "Google Play"}
TONES = {"all": T("Tümü", "All"), "negative": T("Olumsuz · 1–2★", "Negative · 1–2★"),
         "neutral": T("Nötr · 3★", "Neutral · 3★"), "positive": T("Olumlu · 4–5★", "Positive · 4–5★")}

f1, f2, f3 = st.columns([1, 1.25, 1.4])
with f1:
    store = st.segmented_control(T("Mağaza", "Store"), list(STORES), format_func=STORES.get, default="all",
                                 key="voice_store_k")
with f2:
    tone = st.segmented_control(T("Ton", "Tone"), list(TONES), format_func=TONES.get, default="all",
                                key="voice_tone_k")
with f3:
    sort = st.segmented_control(T("Sırala", "Sort"), list(SORTS), format_func=lambda k: SORTS[k][0],
                                default="new", key="voice_sort_k")

rv = rv_all
if store and store != "all":
    rv = rv[rv["store"] == store]
if tone and tone != "all":
    rv = rv[rv["rating_bucket"] == tone]

# Category filter: AI topics (human-checked on the sample) plus two behaviour labels.
pick = None
if classified:
    topic_sets = rv_all["topics"].map(M.split_labels)
    counts = {k: int(topic_sets.map(lambda ls, k=k: k in ls).sum()) for k in fmt.TOPIC}
    cats = {k: f"{fmt.topic(k)} · {c}" for k, c in sorted(counts.items(), key=lambda x: -x[1]) if c >= 2}
    cats["_churn"] = f"🚪 {T('Oyunu bırakanlar', 'Players who quit')} · {int(rv_all['churn_signal'].sum())}"
    cats["_request"] = f"🙏 {T('İstekler', 'Requests')} · {int(rv_all['is_request'].sum())}"
    pick = st.pills(T("Kategori", "Category"), list(cats), format_func=cats.get, key="voice_cat")
    if pick == "_churn":
        rv = rv[rv["churn_signal"]]
    elif pick == "_request":
        rv = rv[rv["is_request"]]
    elif pick:
        rv = rv[rv["topics"].map(lambda v: pick in M.split_labels(v))]

_, by, asc = SORTS.get(sort or "new")
rv = rv.sort_values(by, ascending=asc)

C.note(T(f"<b>{len(rv)}</b> yorum gösteriliyor.", f"Showing <b>{len(rv)}</b> reviews.")
       + (T(" Kategoriler yapay zekâ ile etiketlendi; 1–3★ yorumların hepsi elle kontrol edildi. "
            "Bir yorum birden fazla kategoriye girebilir.",
            " Categories were labelled by AI; every 1–3★ review was checked by hand. A review can fall into "
            "more than one category.") if classified else ""))

if rv.empty:
    C.empty_state(T("Bu seçimde yorum yok", "No reviews for this selection"),
                  T("Filtrelerden birini gevşetmeyi deneyin.", "Try loosening one of the filters."))
for _, row in rv.iterrows():
    if pick == "_request" and row.get("request_text"):
        st.markdown(f"**{T('İstek', 'Request')}:** {row['request_text']}")
    C.quote(row)
