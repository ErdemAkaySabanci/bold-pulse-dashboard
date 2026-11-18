import streamlit as st

from src import insights
from src import metrics as M
from src.data import load
from src.ui import charts, components as C, fmt
from src.ui.theme import tok

t = tok()
R = load.ratings()
countries = M.app_store_countries(R)
gp = M.gp_local(R)
gap = M.platform_gap(R)
prior = float(countries["prior"].iloc[0])
sold_in = int((R["store"] == "app_store").sum())
n_reliable = int((countries["n"] >= M.DIRECTIONAL_N).sum())
best = countries[countries["n"] >= M.STRONG_N].sort_values("avg_rating").iloc[-1]
worst = countries[countries["n"] >= M.STRONG_N].sort_values("avg_rating").iloc[0]

C.hero(
    "Pazarlar & Platformlar",
    "Oyun hangi ülkede daha çok seviliyor?",
    f"Oyun App Store'da <b>{sold_in}</b> ülkede yayında, <b>{len(countries)}</b> ülkeden değerlendirme almış. "
    f"Karşılaştırma için yeterli değerlendirmesi (20+) olan <b>{n_reliable}</b> ülke var.",
    stats=[(fmt.num(len(countries)), "ülkeden değerlendirme"),
           (fmt.num(n_reliable), "karşılaştırılabilir ülke"),
           (f"{fmt.country(best['country'])} {fmt.num(best['avg_rating'], 2)} ★", "büyük pazarlarda en yüksek"),
           (f"{fmt.country(worst['country'])} {fmt.num(worst['avg_rating'], 2)} ★", "büyük pazarlarda en düşük")],
)

C.section("Değerlendirmeler hangi ülkelerden geliyor?",
          "Kutunun büyüklüğü o ülkeden gelen değerlendirme sayısı, rengi ortalama yıldız. "
          "10'dan az değerlendirmesi olan ülkeler “Diğer” kutusunda.", icon="🧺", color=t["orange"])
charts.show(charts.market_treemap(countries), key="treemap")
C.takeaways(insights.concentration_takeaways(countries))

C.section("Ülke sıralaması",
          "Nokta ülkenin ortalaması; arkasındaki soluk çubuk gerçek değerin olası aralığı. "
          "Kırmızı çubuk, aralığın tamamı mağaza ortalamasının altında demektir.",
          icon="🏁", color=t["blue"])
min_n = st.select_slider(
    "En az kaç değerlendirmesi olan ülkeler gösterilsin?", options=[1, 5, 10, 20, 50, 100], value=20,
    help="Birkaç değerlendirmeyle hesaplanan ortalama yanıltıcı olabilir; bu yüzden varsayılan 20.")
view = countries[countries["n"] >= min_n]
below = set(insights.below_average_markets(countries, min_n=max(min_n, M.DIRECTIONAL_N))["country"])
if view.empty:
    C.empty_state("Bu eşikte ülke yok", "Eşiği düşürmeyi deneyin.")
else:
    charts.show(charts.market_ranking(view, prior, below), key="ranking")
    C.takeaways(insights.ranking_takeaways(countries))
    with st.expander("Tablo olarak gör"):
        tbl = view.assign(ulke=view["country"].map(fmt.country),
                          guven=view["tier"].map(lambda x: fmt.TRUST[x][1]))
        st.dataframe(
            tbl[["ulke", "n", "avg_rating", "ci_low", "ci_high", "bayes_avg", "guven"]],
            hide_index=True, width="stretch",
            column_config={
                "ulke": "Ülke", "n": st.column_config.NumberColumn("Değerlendirme", format="%d"),
                "avg_rating": st.column_config.NumberColumn("Ortalama", format="%.2f"),
                "ci_low": st.column_config.NumberColumn("Aralık (alt)", format="%.2f"),
                "ci_high": st.column_config.NumberColumn("Aralık (üst)", format="%.2f"),
                "bayes_avg": st.column_config.NumberColumn(
                    "Düzeltilmiş ort.", format="%.2f",
                    help="Az değerlendirmeli ülkelerin ortalaması mağaza ortalamasına doğru çekilir; "
                         "sıralamayı adil yapar."),
                "guven": "Güven",
            })

C.section("App Store mu, Google Play mi?",
          "Her satır bir ülke: iki logo, o ülkede iki mağazanın yıldız ortalaması. Çizgi uzadıkça "
          "iki mağazanın oyuncuları daha farklı düşünüyor. Google Play'in değeri, Google Play web "
          "sitesinin o ülke için gösterdiği ortalamadır; kaç oya dayandığını Google yayınlamıyor.", icon="📱", color=t["purple"])
C.store_legend()
g = gap[gap["as_n"] >= min_n]
if g.empty:
    C.empty_state("Bu eşikte ortak ülke yok", "Eşiği düşürmeyi deneyin.")
else:
    charts.show(charts.platform_dumbbell(g), key="dumbbell")
    C.takeaways(insights.platform_takeaways(gap, max(min_n, M.DIRECTIONAL_N)))
C.note("Eşik yalnızca App Store sayısına uygulanır.")

with st.expander("Google Play ülke ortalamaları"):
    gtab = gp.assign(ulke=gp["country"].map(fmt.country)).sort_values("avg_rating")
    st.dataframe(
        gtab[["ulke", "avg_rating", "low_share", "share_5"]], hide_index=True, width="stretch",
        column_config={
            "ulke": "Ülke",
            "avg_rating": st.column_config.NumberColumn("Ortalama", format="%.2f"),
            "low_share": st.column_config.ProgressColumn(
                "1–2★ oranı", format="percent", min_value=0.0,
                max_value=float(max(0.25, gtab["low_share"].max()))),
            "share_5": st.column_config.NumberColumn("5★ oranı", format="percent"),
        })
    glob = R[(R["store"] == "google_play") & (R["scope"] == "global")].iloc[0]
    C.note("Google Play web sitesi ülke ortalamasını gösterir; Google Play Games (PC) uygulaması "
           f"ise dünya geneli ortalamayı ({fmt.num(glob['avg_rating'], 2)}, {fmt.num(glob['rating_count'])} "
           "değerlendirme) tek ondalıkla gösterir. İkisi de bu veriyle uyumludur.")
