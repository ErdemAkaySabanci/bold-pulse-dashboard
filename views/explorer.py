import streamlit as st

from src.data import load
from src.i18n import T
from src.metrics import split_labels
from src.ui import components as C, fmt

rv = load.reviews()

C.hero(
    T("Yorum Database'i", "Review Database"),
    T("Tüm yorumlar, tek yerde", "Every review in one place"),
    T("Dashboard'daki her sayının arkasındaki ham kanıt. Filtreleyin, arayın, bir satıra tıklayıp "
      "yorumun tamamını okuyun.",
      "The raw evidence behind every number in the dashboard. Filter, search, and click a row to read the "
      "full review."),
)
C.data_source(C.reviews_source(rv, T("İngilizce çeviriler: Gemini, elle kontrol edildi",
                                     "English translations: Gemini, checked by hand")))

STORES = {"all": T("Tümü", "All"), "app_store": "App Store", "google_play": "Google Play"}
f1, f2, f3 = st.columns([1.1, 1.4, 1])
with f1:
    store = st.segmented_control(T("Mağaza", "Store"), list(STORES), format_func=STORES.get, default="all",
                                 key="ex_store_k")
with f2:
    ratings = st.pills(T("Yıldız", "Stars"), [1, 2, 3, 4, 5], selection_mode="multi", default=[1, 2, 3, 4, 5],
                       format_func=lambda r: f"{r} ★", key="ex_rating")
with f3:
    langs = sorted(rv["source_lang"].dropna().unique())
    lang_pick = st.multiselect(T("Dil", "Language"), langs, format_func=fmt.lang,
                               placeholder=T("Tüm diller", "All languages"), key="ex_lang")

s1, s2 = st.columns([3, 1], vertical_alignment="bottom")
with s1:
    query = st.text_input(T("Yorumlarda ara (orijinal + İngilizce çeviri)",
                            "Search reviews (original + English translation)"),
                          placeholder=T("ör. ads, level, purchase, reklam…", "e.g. ads, level, purchase…"),
                          key="ex_q")
with s2:
    hide_short = st.toggle(T("Çok kısa yorumları gizle", "Hide very short reviews"), value=False, key="ex_short",
                           help=T("“ok”, “süper” gibi 20 karakterden kısa yorumları gizler.",
                                  "Hides reviews shorter than 20 characters, such as “ok” or “super”."))

topic_pick = None
if load.is_classified() and "topics" in rv:
    topics = sorted({x for ls in rv["topics"].map(split_labels) for x in ls})
    topic_pick = st.pills(T("Konu", "Topic"), topics, selection_mode="multi", format_func=fmt.topic,
                          key="ex_topic")

d = rv.copy()
if store and store != "all":
    d = d[d["store"] == store]
d = d[d["rating"].isin(ratings or [])]
if lang_pick:
    d = d[d["source_lang"].isin(lang_pick)]
if query:
    # Search the original and the English translation ("ads" also finds "Werbung").
    hay = d["text"].str.lower() + " " + d["text_en"].fillna("").str.lower()
    d = d[hay.str.contains(query.lower(), regex=False)]
if hide_short:
    d = d[~d["is_short"]]
if topic_pick:
    d = d[d["topics"].map(split_labels).map(lambda ls: bool(set(ls) & set(topic_pick)))]
d = d.sort_values("date", ascending=False).reset_index(drop=True)

st.caption(T(f"{fmt.num(len(rv))} yorumdan {fmt.num(len(d))} tanesi gösteriliyor",
             f"Showing {fmt.num(len(d))} of {fmt.num(len(rv))} reviews"))
if d.empty:
    C.empty_state(T("Bu filtrelere uyan yorum yok", "No reviews match these filters"),
                  T("Aramayı temizleyin veya yıldız filtresini genişletin.",
                    "Clear the search or widen the star filter."))
    st.stop()

table = d.assign(
    tarih=d["date"].dt.tz_convert(None),
    puan=d["rating"].map(fmt.stars),
    magaza=d["store"].map(fmt.STORE),
    ulke=[fmt.country(c) if s == "app_store" else "—" for s, c in zip(d["store"], d["country"])],
    dil=d["source_lang"].map(fmt.lang),
    ceviri=[en if (en and sl not in ("en", "und")) else "" for en, sl in zip(d["text_en"], d["source_lang"])],
    surum=d["app_version"].fillna("—"),
)
event = st.dataframe(
    table[["tarih", "puan", "magaza", "ulke", "dil", "text", "ceviri", "surum", "thumbs_up"]],
    hide_index=True, width="stretch", height=480,
    on_select="rerun", selection_mode="single-row", key="ex_table",
    column_config={
        "tarih": st.column_config.DateColumn(T("Tarih", "Date"), format="D MMM YYYY"),
        "puan": st.column_config.TextColumn(T("Yıldız", "Stars"), width="small"),
        "magaza": st.column_config.TextColumn(T("Mağaza", "Store"), width="small"),
        "ulke": st.column_config.TextColumn(
            T("Ülke", "Country"), width="small",
            help=T("App Store yorumlarında ülke bilinir; Google Play ülke bilgisi vermez (—).",
                   "The country is known for App Store reviews; Google Play does not give it (—).")),
        "dil": st.column_config.TextColumn(
            T("Dil", "Language"), width="small",
            help=T("Yorumun gerçekte yazıldığı dil (otomatik tespit).",
                   "The language the review is actually written in (auto-detected).")),
        "text": st.column_config.TextColumn(T("Yorum (orijinal)", "Review (original)"), width="large"),
        "ceviri": st.column_config.TextColumn(
            T("İngilizce çeviri", "English translation"), width="large",
            help=T("İngilizce olmayan yorumların İngilizce çevirisi; kaynak dil “Dil” sütununda.",
                   "English translation of non-English reviews; the source language is in “Language”.")),
        "surum": st.column_config.TextColumn(T("Sürüm", "Version"), width="small"),
        "thumbs_up": st.column_config.NumberColumn("👍", width="small", format="%d"),
    },
)

rows = event.selection.rows if event and event.selection else []
if rows:
    row = d.iloc[rows[0]]
    C.section(T("Seçilen yorum", "Selected review"), icon="🔎")
    C.quote(row)
    if "topics" in d and split_labels(row.get("topics")):
        st.markdown(" ".join(f"`{fmt.topic(x)}`" for x in split_labels(row["topics"])))
else:
    st.caption(T("Yorumun tamamını okumak için bir satır seçin.", "Select a row to read the full review."))

export = d.drop(columns=[c for c in ("is_short", "has_reply") if c in d])
st.download_button(T("Filtrelenen yorumları indir (CSV)", "Download filtered reviews (CSV)"),
                   export.to_csv(index=False).encode("utf-8"),
                   file_name=T("pulse_yorumlar.csv", "pulse_reviews.csv"), mime="text/csv",
                   icon=":material/download:")
