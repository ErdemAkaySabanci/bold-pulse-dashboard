import streamlit as st

from src import insights
from src import metrics as M
from src.data import load
from src.i18n import T
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
    T("Pazarlar & Platformlar", "Markets & Platforms"),
    T("Oyun hangi ülkede daha çok seviliyor?", "Where is the game liked most?"),
    T(f"Oyun App Store'da <b>{sold_in}</b> ülkede yayında, <b>{len(countries)}</b> ülkeden değerlendirme almış. "
      f"Karşılaştırma için yeterli değerlendirmesi (20+) olan <b>{n_reliable}</b> ülke var.",
      f"The game is live in <b>{sold_in}</b> App Store countries and has ratings from <b>{len(countries)}</b>. "
      f"<b>{n_reliable}</b> countries have enough ratings (20+) to compare."),
    stats=[(fmt.num(len(countries)), T("ülkeden değerlendirme", "countries rating it")),
           (fmt.num(n_reliable), T("karşılaştırılabilir ülke", "comparable countries")),
           (f"{fmt.country(best['country'])} {fmt.num(best['avg_rating'], 2)} ★",
            T("büyük pazarlarda en yüksek", "highest of the large markets")),
           (f"{fmt.country(worst['country'])} {fmt.num(worst['avg_rating'], 2)} ★",
            T("büyük pazarlarda en düşük", "lowest of the large markets"))],
)

C.section(T("Değerlendirmeler hangi ülkelerden geliyor?", "Where do the ratings come from?"),
          T("Kutunun büyüklüğü o ülkeden gelen değerlendirme sayısı, rengi ortalama yıldız. "
            "10'dan az değerlendirmesi olan ülkeler “Diğer” kutusunda.",
            "Box size is the number of ratings from that country, colour is the average star rating. "
            "Countries with fewer than 10 ratings are grouped under “Other”."),
          icon="🧺", color=t["orange"], source=C.app_store_source(countries))
charts.show(charts.market_treemap(countries), key="treemap")
C.takeaways(insights.concentration_takeaways(countries))

C.section(T("Ülke sıralaması", "Country ranking"),
          T("Nokta ülkenin ortalaması; arkasındaki soluk çubuk gerçek değerin olası aralığı. "
            "Kırmızı çubuk, aralığın tamamı mağaza ortalamasının altında demektir.",
            "The dot is the country's average; the faint bar behind it is the likely range of the true value. "
            "A red bar means the whole range sits below the store average."),
          icon="🏁", color=t["blue"], source=C.app_store_source(countries))
min_n = st.select_slider(
    T("En az kaç değerlendirmesi olan ülkeler gösterilsin?", "Show countries with at least how many ratings?"),
    options=[1, 5, 10, 20, 50, 100], value=20, key="min_n",
    help=T("Birkaç değerlendirmeyle hesaplanan ortalama yanıltıcı olabilir; bu yüzden varsayılan 20.",
           "An average from a handful of ratings can mislead, so the default is 20."))
view = countries[countries["n"] >= min_n]
below = set(insights.below_average_markets(countries, min_n=max(min_n, M.DIRECTIONAL_N))["country"])
if view.empty:
    C.empty_state(T("Bu eşikte ülke yok", "No countries at this threshold"),
                  T("Eşiği düşürmeyi deneyin.", "Try a lower threshold."))
else:
    charts.show(charts.market_ranking(view, prior, below), key="ranking")
    C.takeaways(insights.ranking_takeaways(countries))
    with st.expander(T("Tablo olarak gör", "View as a table")):
        tbl = view.assign(ulke=view["country"].map(fmt.country),
                          guven=view["tier"].map(lambda x: fmt.TRUST[x][1]))
        st.dataframe(
            tbl[["ulke", "n", "avg_rating", "ci_low", "ci_high", "bayes_avg", "guven"]],
            hide_index=True, width="stretch",
            column_config={
                "ulke": T("Ülke", "Country"),
                "n": st.column_config.NumberColumn(T("Değerlendirme", "Ratings"), format="%d"),
                "avg_rating": st.column_config.NumberColumn(T("Ortalama", "Average"), format="%.2f"),
                "ci_low": st.column_config.NumberColumn(T("Aralık (alt)", "Range (low)"), format="%.2f"),
                "ci_high": st.column_config.NumberColumn(T("Aralık (üst)", "Range (high)"), format="%.2f"),
                "bayes_avg": st.column_config.NumberColumn(
                    T("Düzeltilmiş ort.", "Adjusted avg."), format="%.2f",
                    help=T("Az değerlendirmeli ülkelerin ortalaması mağaza ortalamasına doğru çekilir; "
                           "sıralamayı adil yapar.",
                           "Countries with few ratings are pulled towards the store average, which keeps the "
                           "ranking fair.")),
                "guven": T("Güven", "Confidence"),
            })

C.section(T("App Store mu, Google Play mi?", "App Store or Google Play?"),
          T("Her satır bir ülke: mavi daire App Store, yeşil elmas Google Play ortalaması. Çizgi uzadıkça "
            "iki mağazanın oyuncuları daha farklı düşünüyor. Google Play'in değeri, Google Play web "
            "sitesinin o ülke için gösterdiği ortalamadır; kaç oya dayandığını Google yayınlamıyor.",
            "Each row is a country: blue circle is the App Store average, green diamond the Google Play "
            "average. The longer the line, the more the two stores' players disagree. The Google Play value "
            "is the average its website shows for that country; Google does not publish how many votes it "
            "rests on."),
          icon="📱", color=t["purple"],
          source=T(f"App Store ülke ortalamaları (değerlendirme sayısıyla) + Google Play web sitesindeki "
                   f"{fmt.num(len(gp))} ülkenin ortalaması (sayısız)",
                   f"App Store country averages (with rating counts) + Google Play website averages for "
                   f"{fmt.num(len(gp))} countries (no counts)"))
C.store_legend()
g = gap[gap["as_n"] >= min_n]
if g.empty:
    C.empty_state(T("Bu eşikte ortak ülke yok", "No shared countries at this threshold"),
                  T("Eşiği düşürmeyi deneyin.", "Try a lower threshold."))
else:
    charts.show(charts.platform_dumbbell(g), key="dumbbell")
    C.takeaways(insights.platform_takeaways(gap, max(min_n, M.DIRECTIONAL_N)))
C.note(T("Eşik yalnızca App Store sayısına uygulanır.", "The threshold applies to the App Store count only."))

with st.expander(T("Google Play ülke ortalamaları", "Google Play country averages")):
    gtab = gp.assign(ulke=gp["country"].map(fmt.country)).sort_values("avg_rating")
    st.dataframe(
        gtab[["ulke", "avg_rating", "low_share", "share_5"]], hide_index=True, width="stretch",
        column_config={
            "ulke": T("Ülke", "Country"),
            "avg_rating": st.column_config.NumberColumn(T("Ortalama", "Average"), format="%.2f"),
            "low_share": st.column_config.ProgressColumn(
                T("1–2★ oranı", "1–2★ share"), format="percent", min_value=0.0,
                max_value=float(max(0.25, gtab["low_share"].max()))),
            "share_5": st.column_config.NumberColumn(T("5★ oranı", "5★ share"), format="percent"),
        })
    glob = R[(R["store"] == "google_play") & (R["scope"] == "global")].iloc[0]
    C.note(T("Google Play web sitesi ülke ortalamasını gösterir; Google Play Games (PC) uygulaması "
             f"ise dünya geneli ortalamayı ({fmt.num(glob['avg_rating'], 2)}, {fmt.num(glob['rating_count'])} "
             "değerlendirme) tek ondalıkla gösterir. İkisi de bu veriyle uyumludur.",
             "The Google Play website shows the country average; the Google Play Games (PC) app shows the "
             f"worldwide average ({fmt.num(glob['avg_rating'], 2)}, {fmt.num(glob['rating_count'])} ratings) "
             "to one decimal. Both match this data."))
