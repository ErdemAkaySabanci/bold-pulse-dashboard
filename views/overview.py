import streamlit as st

from src import config, insights
from src import metrics as M
from src.data import load
from src.ui import charts, components as C, fmt
from src.ui.theme import tok

t = tok()
R = load.ratings()
rv = load.reviews()

summary = M.store_summary(R).set_index("store")
total = int(summary["rating_count"].sum())
avg = M.overall_avg(summary.reset_index())
countries = M.app_store_countries(R)
gp = M.gp_local(R)
gap = M.platform_gap(R)
matrix = M.topic_matrix(rv) if load.is_classified() and "topics" in rv else None
n_rev = len(rv)
asr, gpr = summary.loc["app_store"], summary.loc["google_play"]

C.hero(
    "PULSE · Oyuncu Analitiği",
    "Oyuncular Market Match!'i nasıl buluyor?",
    f"App Store ve Google Play'deki <b>{fmt.num(total)}</b> değerlendirme ve <b>{fmt.num(n_rev)}</b> "
    f"yazılı yorumun özeti. Oyuncuların büyük çoğunluğu memnun: ortalama <b>{fmt.num(avg, 2)} ★</b>.",
    stats=[(fmt.num(total), "değerlendirme"),
           (f"{fmt.num(avg, 2)} ★", "ortalama"),
           (fmt.num(n_rev), "yazılı yorum"),
           (fmt.num(len(countries)), "ülkeden değerlendirme")],
)

k1, k2, k3 = st.columns(3)
with k1:
    C.kpi("App Store", f"{fmt.num(asr['avg_rating'], 2)} ★",
          f"{fmt.num(asr['rating_count'])} değerlendirme · {fmt.num(asr['countries'])} ülke", "",
          t["as"], C.trust_n(int(asr["rating_count"]), "değerlendirme"), delay=0.05,
          icon_html=C.store_logo("app_store", 40))
with k2:
    C.kpi("Google Play", f"{fmt.num(gpr['avg_rating'], 2)} ★",
          f"{fmt.num(gpr['rating_count'])} değerlendirme · dünya geneli", "",
          t["gp"], C.trust_n(int(gpr["rating_count"]), "değerlendirme"), delay=0.12,
          icon_html=C.store_logo("google_play", 40))
with k3:
    neg = int((rv["rating_bucket"] == "negative").sum())
    C.kpi("Olumsuz yorum (1–2★)", fmt.num(neg),
          f"{fmt.num(n_rev)} yazılı yorumun {fmt.pct(neg / n_rev)}'i 1–2 yıldızlı", "!",
          t["neg"], C.trust_n(neg, "yorum"), delay=0.19)

us = countries[countries["country"] == "us"]
_off = config.OFFICIAL_DISPLAY
checks = []
if len(us):
    o = _off["app_store_us"]
    checks.append({"label": o["label"], "ours_avg": float(us["avg_rating"].iloc[0]),
                   "ours_n": int(us["n"].iloc[0]), "shown_avg": o["avg"], "shown_count_text": o["count_text"],
                   "ok": M.matches_display(float(us["avg_rating"].iloc[0]), int(us["n"].iloc[0]), o["avg"], o["count"])})
o = _off["google_play"]
checks.append({"label": o["label"], "ours_avg": float(gpr["avg_rating"]), "ours_n": int(gpr["rating_count"]),
               "shown_avg": o["avg"], "shown_count_text": o["count_text"],
               "ok": M.matches_display(float(gpr["avg_rating"]), int(gpr["rating_count"]), o["avg"], o["count"])})
C.official_check(checks)

C.section("Öne çıkan 3 bulgu", "Her bulgu doğrudan veriden hesaplanır; kanıtı bir tık uzağında.",
          icon="💡", color=t["orange"],
          source=(f"App Store {fmt.num(asr['rating_count'])} değerlendirme (ülke bazında) · Google Play "
                  f"{fmt.num(gpr['rating_count'])} değerlendirme (dünya geneli) · {fmt.num(n_rev)} yazılı yorum"))
# Headline findings only use well-supported evidence. The App Store vs Google Play country
# gap stays on the Markets page: Google Play's per-country counts are unknown.
found = [f for f in (insights.market_finding(countries, gp), insights.ads_finding(rv),
                     insights.satisfaction_finding(R, rv)) if f]
cols = st.columns(len(found))
for i, (col, f) in enumerate(zip(cols, found), start=1):
    with col:
        C.finding(i, f.title, f.body_html, t[f.color_key], C.trust(f.tier, f.badge_detail),
                  delay=0.08 * i)
        st.page_link(f.target, label="Kanıtı gör", icon=":material/arrow_forward:")

C.section("Dünya genelinde değerlendirmeler",
          "Baloncuk ne kadar büyükse o ülkeden o kadar çok değerlendirme gelmiş; renk ortalamayı gösterir "
          "(kırmızı düşük, mavi yüksek).", icon="🌍", color=t["blue"],
          source=C.app_store_source(countries) + ". Google Play ülke bazında sayı yayınlamadığı için dahil değil")
charts.show(charts.world_map(countries), key="map")
C.takeaways(insights.map_takeaways(countries))

left, right = st.columns([1.1, 1], gap="large")
with left:
    C.section("Yıldızların dağılımı", "Her çubuk, o yıldızı veren değerlendirmelerin payı.",
              icon="⭐", color=t["neu"],
              source=f"Yalnızca Google Play · dünya geneli · {fmt.num(gpr['rating_count'])} değerlendirme")
    g = R[(R["store"] == "google_play") & (R["scope"] == "global")].iloc[0]
    shares = [g[f"share_{i}"] for i in range(1, 6)]
    charts.show(charts.star_bars(shares, int(g["rating_count"])), key="stars")
    C.takeaways(insights.stars_takeaways(R))
    C.note("Apple yıldız dağılımını yayınlamadığı için yalnızca Google Play gösteriliyor.")
with right:
    C.section("Yazılı yorumların tonu", "Ton, oyuncunun verdiği yıldızdan gelir.", icon="💬",
              color=t["purple"], source=C.reviews_source(rv))
    counts = rv["rating_bucket"].value_counts()
    C.segmented_bar([
        ("Olumlu (4–5★)", int(counts.get("positive", 0)), t["pos"]),
        ("Nötr (3★)", int(counts.get("neutral", 0)), t["neu"]),
        ("Olumsuz (1–2★)", int(counts.get("negative", 0)), t["neg"]),
    ], n_rev)
    C.takeaways(insights.tone_takeaways(rv))

C.section("Her nokta bir yorum",
          "Zaman içinde gelen tüm yazılı yorumlar. Nokta ne kadar büyükse o yorumu faydalı bulan (👍) "
          "oyuncu sayısı o kadar fazla; üzerine gelince yorumu okuyabilirsiniz.", icon="✨", color=t["green"],
          source=C.reviews_source(rv, "sürüm tarihleri: App Store"))
ev = load.events()
charts.show(charts.review_timeline(rv, ev), key="timeline")
C.takeaways(insights.timeline_takeaways(rv, ev))
