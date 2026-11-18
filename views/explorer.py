import streamlit as st

from src.data import load
from src.metrics import split_labels
from src.ui import components as C, fmt

rv = load.reviews()

C.hero(
    "Yorum Gezgini",
    "Tüm yorumlar, tek yerde",
    "Dashboard'daki her sayının arkasındaki ham kanıt. Filtreleyin, arayın, bir satıra tıklayıp "
    "yorumun tamamını okuyun.",
)

f1, f2, f3 = st.columns([1.1, 1.4, 1])
with f1:
    store = st.segmented_control("Mağaza", ["Tümü", "App Store", "Google Play"], default="Tümü",
                                 key="ex_store")
with f2:
    ratings = st.pills("Yıldız", [1, 2, 3, 4, 5], selection_mode="multi", default=[1, 2, 3, 4, 5],
                       format_func=lambda r: f"{r} ★", key="ex_rating")
with f3:
    langs = sorted(rv["source_lang"].dropna().unique())
    lang_pick = st.multiselect("Dil", langs, format_func=fmt.lang, placeholder="Tüm diller",
                               key="ex_lang")

s1, s2 = st.columns([3, 1], vertical_alignment="bottom")
with s1:
    query = st.text_input("Yorumlarda ara (orijinal + İngilizce çeviri)",
                          placeholder="ör. ads, level, purchase, reklam…", key="ex_q")
with s2:
    hide_short = st.toggle("Çok kısa yorumları gizle", value=False, key="ex_short",
                           help="“ok”, “süper” gibi 20 karakterden kısa yorumları gizler.")

topic_pick = None
if load.is_classified() and "topics" in rv:
    topics = sorted({x for ls in rv["topics"].map(split_labels) for x in ls})
    topic_pick = st.pills("Konu", topics, selection_mode="multi", key="ex_topic")

d = rv.copy()
if store and store != "Tümü":
    d = d[d["store"] == ("app_store" if store == "App Store" else "google_play")]
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

st.caption(f"{fmt.num(len(rv))} yorumdan {fmt.num(len(d))} tanesi gösteriliyor")
if d.empty:
    C.empty_state("Bu filtrelere uyan yorum yok", "Aramayı temizleyin veya yıldız filtresini genişletin.")
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
        "tarih": st.column_config.DateColumn("Tarih", format="D MMM YYYY"),
        "puan": st.column_config.TextColumn("Yıldız", width="small"),
        "magaza": st.column_config.TextColumn("Mağaza", width="small"),
        "ulke": st.column_config.TextColumn(
            "Ülke", width="small",
            help="App Store yorumlarında ülke bilinir; Google Play ülke bilgisi vermez (—)."),
        "dil": st.column_config.TextColumn(
            "Dil", width="small", help="Yorumun gerçekte yazıldığı dil (otomatik tespit)."),
        "text": st.column_config.TextColumn("Yorum (orijinal)", width="large"),
        "ceviri": st.column_config.TextColumn(
            "İngilizce çeviri", width="large",
            help="İngilizce olmayan yorumların İngilizce çevirisi; kaynak dil “Dil” sütununda."),
        "surum": st.column_config.TextColumn("Sürüm", width="small"),
        "thumbs_up": st.column_config.NumberColumn("👍", width="small", format="%d"),
    },
)

rows = event.selection.rows if event and event.selection else []
if rows:
    row = d.iloc[rows[0]]
    C.section("Seçilen yorum", icon="🔎")
    C.quote(row)
    if "topics" in d and split_labels(row.get("topics")):
        st.markdown(" ".join(f"`{x}`" for x in split_labels(row["topics"])))
else:
    st.caption("Yorumun tamamını okumak için bir satır seçin.")

export = d.drop(columns=[c for c in ("is_short", "has_reply") if c in d])
st.download_button("Filtrelenen yorumları indir (CSV)", export.to_csv(index=False).encode("utf-8"),
                   file_name="pulse_yorumlar.csv", mime="text/csv", icon=":material/download:")
