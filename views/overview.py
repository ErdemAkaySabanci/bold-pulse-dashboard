import streamlit as st

from src import insights
from src import metrics as M
from src.data import load
from src.i18n import T
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
RATINGS = T("değerlendirme", "ratings")

C.hero(
    T("PULSE · Oyuncu Analitiği", "PULSE · Player Analytics"),
    T("Oyuncular Market Match!'i nasıl buluyor?", "What do players think of Market Match!?"),
    T(f"App Store ve Google Play'deki <b>{fmt.num(total)}</b> değerlendirme ve <b>{fmt.num(n_rev)}</b> "
      f"yazılı yorumun özeti. Oyuncuların büyük çoğunluğu memnun: ortalama <b>{fmt.num(avg, 2)} ★</b>.",
      f"A summary of <b>{fmt.num(total)}</b> ratings and <b>{fmt.num(n_rev)}</b> written reviews from the "
      f"App Store and Google Play. Most players are happy: the average is <b>{fmt.num(avg, 2)} ★</b>."),
    stats=[(fmt.num(total), RATINGS),
           (f"{fmt.num(avg, 2)} ★", T("ortalama", "average")),
           (fmt.num(n_rev), T("yazılı yorum", "written reviews")),
           (fmt.num(len(countries)), T("ülkeden değerlendirme", "countries rating it"))],
)

k1, k2, k3 = st.columns(3)
with k1:
    C.kpi("App Store", f"{fmt.num(asr['avg_rating'], 2)} ★",
          f"{fmt.num(asr['rating_count'])} {RATINGS} · {fmt.num(asr['countries'])} {T('ülke', 'countries')}", "",
          t["as"], C.trust_n(int(asr["rating_count"]), RATINGS), delay=0.05,
          icon_html=C.store_logo("app_store", 40))
with k2:
    C.kpi("Google Play", f"{fmt.num(gpr['avg_rating'], 2)} ★",
          f"{fmt.num(gpr['rating_count'])} {RATINGS} · {T('dünya geneli', 'worldwide')}", "",
          t["gp"], C.trust_n(int(gpr["rating_count"]), RATINGS), delay=0.12,
          icon_html=C.store_logo("google_play", 40))
with k3:
    neg = int((rv["rating_bucket"] == "negative").sum())
    C.kpi(T("Olumsuz yorum (1–2★)", "Negative reviews (1–2★)"), fmt.num(neg),
          T(f"{fmt.num(n_rev)} yazılı yorumun {fmt.pct(neg / n_rev)}'i 1–2 yıldızlı",
            f"{fmt.pct(neg / n_rev)} of {fmt.num(n_rev)} written reviews are 1–2 stars"), "!",
          t["neg"], C.trust_n(neg, T("yorum", "reviews")), delay=0.19)


C.section(T("Öne çıkan 3 bulgu", "3 key findings"),
          T("Her bulgu doğrudan veriden hesaplanır; kanıtı bir tık uzağında.",
            "Every finding is computed straight from the data; the evidence is one click away."),
          icon="💡", color=t["orange"],
          source=T(f"App Store {fmt.num(asr['rating_count'])} değerlendirme (ülke bazında) · Google Play "
                   f"{fmt.num(gpr['rating_count'])} değerlendirme (dünya geneli) · {fmt.num(n_rev)} yazılı yorum",
                   f"App Store {fmt.num(asr['rating_count'])} ratings (by country) · Google Play "
                   f"{fmt.num(gpr['rating_count'])} ratings (worldwide) · {fmt.num(n_rev)} written reviews"))
# Headline findings only use well-supported evidence. The App Store vs Google Play country
# gap stays on the Markets page: Google Play's per-country counts are unknown.
found = [f for f in (insights.market_finding(countries, gp), insights.ads_finding(rv),
                     insights.satisfaction_finding(R, rv)) if f]
cols = st.columns(len(found))
for i, (col, f) in enumerate(zip(cols, found), start=1):
    with col:
        C.finding(i, f.title, f.body_html, t[f.color_key], C.trust(f.tier, f.badge_detail),
                  delay=0.08 * i)
        st.page_link(f.target, label=T("Kanıtı gör", "See the evidence"), icon=":material/arrow_forward:")

C.section(T("Dünya genelinde değerlendirmeler", "Ratings around the world"),
          T("Baloncuk ne kadar büyükse o ülkeden o kadar çok değerlendirme gelmiş; renk ortalamayı gösterir "
            "(kırmızı düşük, mavi yüksek). Sağdaki + / − ile yakınlaştırıp sürükleyerek gezebilirsiniz.",
            "The bigger the bubble, the more ratings from that country; the colour shows the average "
            "(red low, blue high). Use + / − on the right to zoom, and drag to move around."),
          icon="🌍", color=t["blue"],
          source=C.app_store_source(countries) + T(". Google Play ülke bazında sayı yayınlamadığı için dahil değil",
                                                   ". Google Play is not included because it does not publish "
                                                   "per-country counts"))
charts.show(charts.world_map(countries), key="map", config=charts.MAP_CONFIG)
C.takeaways(insights.map_takeaways(countries))

left, right = st.columns([1.1, 1], gap="large")
with left:
    C.section(T("Yıldızların dağılımı", "Star distribution"),
              T("Her çubuk, o yıldızı veren değerlendirmelerin payı.",
                "Each bar is the share of ratings giving that many stars."),
              icon="⭐", color=t["neu"],
              source=T(f"Yalnızca Google Play · dünya geneli · {fmt.num(gpr['rating_count'])} değerlendirme",
                       f"Google Play only · worldwide · {fmt.num(gpr['rating_count'])} ratings"))
    g = R[(R["store"] == "google_play") & (R["scope"] == "global")].iloc[0]
    shares = [g[f"share_{i}"] for i in range(1, 6)]
    charts.show(charts.star_bars(shares, int(g["rating_count"])), key="stars")
    C.takeaways(insights.stars_takeaways(R))
    C.note(T("Apple yıldız dağılımını yayınlamadığı için yalnızca Google Play gösteriliyor.",
             "Only Google Play is shown because Apple does not publish its star distribution."))
with right:
    C.section(T("Yazılı yorumların tonu", "Tone of written reviews"),
              T("Ton, oyuncunun verdiği yıldızdan gelir.", "Tone comes from the stars the player gave."),
              icon="💬", color=t["purple"], source=C.reviews_source(rv))
    counts = rv["rating_bucket"].value_counts()
    C.segmented_bar([
        (fmt.BUCKET["positive"], int(counts.get("positive", 0)), t["pos"]),
        (fmt.BUCKET["neutral"], int(counts.get("neutral", 0)), t["neu"]),
        (fmt.BUCKET["negative"], int(counts.get("negative", 0)), t["neg"]),
    ], n_rev)
    C.takeaways(insights.tone_takeaways(rv))

C.section(T("Her nokta bir yorum", "Every dot is a review"),
          T("Zaman içinde gelen tüm yazılı yorumlar. Nokta ne kadar büyükse o yorumu faydalı bulan (👍) "
            "oyuncu sayısı o kadar fazla; üzerine gelince yorumu okuyabilirsiniz.",
            "All written reviews over time. The bigger the dot, the more players found the review helpful "
            "(👍); hover to read it."),
          icon="✨", color=t["green"],
          source=C.reviews_source(rv, T("sürüm tarihleri: App Store", "release dates: App Store")))
ev = load.events()
charts.show(charts.review_timeline(rv, ev), key="timeline")
C.takeaways(insights.timeline_takeaways(rv, ev))
