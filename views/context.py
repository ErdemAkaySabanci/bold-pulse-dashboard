"""Sektörle Kıyas / Industry Benchmark: Appfigures industry benchmark next to Market Match's own data.

Rules: every industry figure comes from data/industry_benchmark.csv (typed in verbatim, with the
report's printed page number); industry data is drawn in neutral grey ("Sektör verisi" / "Industry
data"), Market Match data in brand red ("Market Match"). Every text is T(turkish, english).
"""
import streamlit as st

from src import insights
from src import metrics as M
from src.data import load
from src.i18n import T, is_en
from src.ui import charts, components as C, fmt

B = load.benchmark()
R = load.ratings()
rv = load.reviews()
countries = M.app_store_countries(R).set_index("country")
store_avg = float(countries["prior"].iloc[0])
SRC = "Appfigures, <i>Mobile Games in 2025</i>"
P = T("s.", "p.")   # page abbreviation


def fig(section: str, item: str) -> tuple[float, int]:
    """(value, printed page) of one industry figure; fails loudly if it is not in the CSV."""
    row = B[(B["section"] == section) & (B["item"] == item)].iloc[0]
    return float(row["value"]), int(row["page"])


def pct(v: float) -> str:
    """Industry percentages: 70 -> '%70' / '70%', 16.3 -> '%16,3' / '16.3%'."""
    return fmt.pct(v / 100, 0 if float(v).is_integer() else 1)


def chg(v: float, d: int = 1) -> str:
    """Signed change: 47.1 -> '+%47,1' / '+47.1%', -6.1 -> '−%6,1' / '−6.1%'."""
    sign = "+" if v > 0 else "−" if v < 0 else ""
    return f"{sign}{fmt.num(abs(v), d)}%" if is_en() else f"{sign}%{fmt.num(abs(v), d)}"


C.hero(
    T("Sektörle Kıyas", "Industry Benchmark"),
    T("Market Match sektöre göre nerede duruyor?", "Where does Market Match stand against the industry?"),
    T("Appfigures'ın <b>Mobile Games in 2025</b> raporundan (2024 verisi) seçilmiş rakamlar, Market Match'in "
      "kendi App Store ve Google Play puan ve yorumlarının yanında.",
      "Selected figures from Appfigures' <b>Mobile Games in 2025</b> report (2024 data), set next to Market "
      "Match's own App Store and Google Play ratings and reviews."),
)
puzzle, p_puzzle = fig("genre_share", "Puzzle")
C.note(T(f"<b>Dikkatle okuyun.</b> Sektör verisi 2024'ün en çok kazanan 500 ve 1.000 oyununu kapsıyor; bunlar "
         f"çoğunlukla büyük ve olgun oyunlar. Gelir rakamları uygulama içi satın almalardan gelen brüt harcama, "
         f"reklam geliri dahil değil ({SRC}, s. 41). Market Match ise 2026'da çıkmış yeni bir oyun ve buradaki "
         f"verisi mağaza puanları ve yazılı yorumlar: oyuncuların ne söylediği, ne yaptığı değil. Bağlam için: "
         f"Puzzle, en çok kazanan 1.000 oyunun {pct(puzzle)}'ü ve Mid-Core ile yarışabilen tek Casual tür "
         f"({SRC}, s. {p_puzzle}, 35).",
         f"<b>Read with care.</b> The industry data covers the top 500 and top 1,000 earning games of 2024, "
         f"mostly large and mature titles; its revenue figures are gross in-app purchase spending and exclude ad "
         f"revenue ({SRC}, p. 41). Market Match launched in 2026, and its data here are store ratings and written "
         f"reviews: what players say, not what they do. For context, Puzzle is {pct(puzzle)} of the top 1,000 "
         f"earning games, the only Casual genre to rival Mid-Core ({SRC}, p. {p_puzzle}, 35)."))

# ---------------------------------------------------------------- monetization
# Market Match column: my play-through to level 84 and the store reviews ("not observed" is not "absent").
STATUS = {
    "Consumables/Currency via IAP": "present",       # boosters and coins sold in the Shop
    "Limited-Time Events/Offers": "present",         # "Limited Deal" (80% off) and live events
    "IAP Bundles/Packages": "present",               # Starter Bag and a larger booster bundle
    "In-Game Advertising": "present",                # end-of-level ads reported in reviews
    "Ad-Free Paid Version": "present",               # ad-free play is part of the Starter Bag
    "Rewarded Video Ads": "present",                 # "Clear 3 items" when the tray is full, "+1 Life"
}
# Turkish display names; in English the report's own wording is used.
TR = {
    "Consumables/Currency via IAP": "Tüketilebilir ürün ve para satışı",
    "Limited-Time Events/Offers": "Sınırlı süreli etkinlik ve teklifler",
    "Premium Currency via IAP": "Premium para birimi satışı",
    "IAP Bundles/Packages": "Paket satışları",
    "Unlocks/Cosmetics via IAP": "Kilit açma ve kozmetik satışı",
    "Rewarded Video Ads": "Ödüllü video reklam",
    "Battle/Season Passes": "Sezon kartı (battle pass)",
    "Gacha/Loot Box Mechanics": "Gacha / sandık mekaniği",
    "In-Game Advertising": "Oyun içi reklam",
    "Subscriptions/VIP Membership": "Abonelik / VIP üyelik",
    "Brand Sponsorships": "Marka sponsorlukları",
    "Ad-Free Paid Version": "Ücretli reklamsız sürüm",
    "Player Trading/Marketplace": "Oyuncular arası ticaret",
    "Other (Merch, etc.)": "Diğer (ürün satışı vb.)",
}
mon = B[B["section"] == "monetization"].copy()
mon["label"] = mon["item"] if is_en() else mon["item"].map(TR).fillna(mon["item"])
status = {i: STATUS.get(i, "not_observed") for i in mon["item"]}

C.section(T("Para kazanma: en çok kazananlar ne kullanıyor, Market Match'te ne var?",
            "Monetization: what top earners use, and what Market Match has"),
          T("Gri çubuklar, en çok kazanan 500 oyunun yüzde kaçında o yöntemin bulunduğunu gösteriyor. Sağdaki "
            "sütun, aynı yöntemin Market Match'te görülüp görülmediğini söylüyor.",
            "Grey bars show the share of the top 500 earning games that use each method. The right-hand "
            "column says whether the same method was seen in Market Match."),
          source=T(f"Sektör verisi: en çok kazanan 500 oyun, 2024 · {SRC}, s. {int(mon['page'].iloc[0])} · "
                   "Market Match: 84. seviyeye kadar kendi oyun deneyimim ve mağaza yorumları",
                   f"Industry data: top 500 earning games, 2024 · {SRC}, p. {int(mon['page'].iloc[0])} · "
                   "Market Match: my own play-through to level 84 and the store reviews"))
charts.show(charts.monetization_benchmark(mon, status), key="monetization")

n_crit = int(rv["rating_bucket"].isin(["negative", "neutral"]).sum())
n_ads = len(insights.ad_mentions(rv))
cons, p30 = fig("monetization", "Consumables/Currency via IAP")
lto, _ = fig("monetization", "Limited-Time Events/Offers")
rewarded, _ = fig("monetization", "Rewarded Video Ads")
ingame, _ = fig("monetization", "In-Game Advertising")
cosm, _ = fig("monetization", "Unlocks/Cosmetics via IAP")
all_tr = "hepsinde" if min(cons, lto) == 100 else "neredeyse hepsinde"
all_en = "all" if min(cons, lto) == 100 else "almost all"
C.takeaways([
    T(f"Olmazsa olmazlar yerinde: tüketilebilir ürün satışı ({pct(cons)}) ve sınırlı süreli teklifler "
      f"({pct(lto)}) en çok kazanan 500 oyunun {all_tr} var (s. {p30}); Market Match'te de ikisi var "
      "(booster ve coin satışı, %80 indirimli Limited Deal).",
      f"The must-haves are in place: consumable sales ({pct(cons)}) and limited-time offers ({pct(lto)}) are "
      f"in {all_en} of the top 500 earning games (p. {p30}), and Market Match has both (booster and coin "
      "sales, the 80%-off Limited Deal)."),
    T(f"Ödüllü video reklam en çok kazananların {pct(rewarded)}'ında, oyun içi reklam {pct(ingame)}'unda var "
      f"(s. {p30}). Market Match ikisini de kullanıyor: tepsi dolunca “Clear 3 items” ve “+1 Life” için ödüllü "
      f"video, bölüm sonlarında ise reklam. Reklam yine de en sık şikâyet: 1–3★ veren <b>{n_crit} oyuncunun "
      f"{n_ads}</b>'sı reklamdan bahsediyor.",
      f"Rewarded video ads are used by {pct(rewarded)} of the top earners, in-game advertising by {pct(ingame)} "
      f"(p. {p30}). Market Match uses both: rewarded videos for “Clear 3 items” when the tray is full and for "
      f"“+1 Life”, and ads at the end of levels. Ads are still the most common complaint: <b>{n_ads} of the "
      f"{n_crit}</b> players who gave 1–3★ mention them."),
    T(f"Kilit açma ve kozmetik satışı en çok kazananların {pct(cosm)}'inde var (s. {p30}), Market Match'te "
      "görülmedi; coin sadece can ve ekstra şans için harcanıyor. En net boşluk bu ve 5. önerideki sepet "
      "özelleştirme fikrini destekliyor.",
      f"Unlocks and cosmetics are sold by {pct(cosm)} of the top earners (p. {p30}) but were not seen in Market "
      "Match, where coins only go to lives and extra chances. This is the clearest gap, and it supports the "
      "cart-customization idea in Recommendation 5."),
    T("Sınırlar: rapor “oyun içi reklam”ı tanımlamıyor; bu karşılaştırma gelir etkisini değil, sadece var/yok "
      "durumunu gösteriyor. “Gözlenmedi”, oynadığım kısımda görmediğim anlamına geliyor, kesin yok demek değil.",
      "Limits: the report does not define “In-Game Advertising”, and this comparison shows presence only, not "
      "revenue impact. “Not observed” means I did not see it in my play-through, not that it is proven absent."),
])

# ---------------------------------------------------------------- markets
yoy = B[B["section"] == "spend_yoy"].set_index("item")
both = [c for c in yoy.index if c in countries.index and countries.loc[c, "n"] >= M.DIRECTIONAL_N]
pts = countries.loc[both, ["n", "avg_rating"]].assign(
    spend_yoy=yoy.loc[both, "value"].values, page=yoy.loc[both, "page"].values,
    name=[fmt.country(c) for c in both]).reset_index()

C.section(T("Ülkeler: harcama nerede büyüyor, Market Match orada ne kadar seviliyor?",
            "Countries: where is spending growing, and how well is Market Match liked there?"),
          T("Her nokta bir ülke. <b>Soldan sağa:</b> o ülkede mobil oyunlara yapılan harcama 2024'te ne kadar "
            "değişti (sağa gittikçe pazar daha hızlı büyüyor). <b>Aşağıdan yukarıya:</b> Market Match'in o "
            "ülkedeki App Store puanı (kesikli çizginin üstü, oyunun genel ortalamasından iyi). <b>Nokta "
            "büyüklüğü:</b> o ülkeden gelen Market Match puanı sayısı. Renkli bölgeler, noktanın düştüğü yerin ne "
            "anlama geldiğini söylüyor.",
            "Each dot is a country. <b>Left to right:</b> how much mobile game spending changed there in 2024 "
            "(further right, faster growth). <b>Bottom to top:</b> Market Match's App Store rating in that "
            "country (above the dashed line is better than the game's overall average). <b>Dot size:</b> the "
            "number of Market Match ratings from that country. The coloured regions say what each position "
            "means."),
          source=T(f"Sektör verisi: tüketici harcamasındaki değişim, 2024'e karşı 2023 · {SRC}, s. 7, 23, 24 · "
                   f"Market Match: App Store puanları, hem raporda hem bizde {M.DIRECTIONAL_N}+ puanı olan "
                   f"{len(pts)} ülke",
                   f"Industry data: change in consumer spending, 2024 vs 2023 · {SRC}, p. 7, 23, 24 · "
                   f"Market Match: App Store ratings, the {len(pts)} countries that are in the report and have "
                   f"{M.DIRECTIONAL_N}+ ratings"))
charts.show(charts.market_context_scatter(pts, store_avg), key="market_context")


def mm(code: str) -> tuple[int, float]:
    r = countries.loc[code]
    return int(r["n"]), float(r["avg_rating"])


us_n, us_avg = mm("us")
jp_n, jp_avg = mm("jp")
mx_n, mx_avg = mm("mx")
tr_n, tr_avg = mm("tr")
br_n, br_avg = mm("br") if "br" in countries.index else (0, float("nan"))
us_spend, p_us = fig("spend_total", "us")
jp_spend, p_jp = fig("spend_total", "jp")
spd_world, p_w = fig("spend_per_download", "world")
spd_us, p_u = fig("spend_per_download", "us")
written_jp = int(((rv["store"] == "app_store") & (rv["country"] == "jp")).sum())
us_yoy = float(yoy.loc["us", "value"])
us_chg = chg(us_yoy, 2 if abs(us_yoy) < 0.1 else 1)
us_share = fmt.pct(us_n / countries["n"].sum())
C.takeaways([
    T(f"<b>ABD (en büyük nokta, sıfır çizgisinin üstünde: harcama {us_chg} ile yerinde sayıyor).</b> "
      f"Market Match'in App Store puanlarının {us_share}'i ABD'den geliyor ve ortalama {fmt.num(us_avg, 2)} ★; "
      f"büyük pazarlar arasında en yüksek. ABD harcamada da 1. sırada ({fmt.num(us_spend, 1)} milyar $, "
      f"s. {p_us}) ve indirme başına {fmt.num(spd_us, 2)} $ harcıyor; dünya ortalaması {fmt.num(spd_world, 2)} $ "
      f"(s. {p_w}–{p_u}). ABD deneyimi korunmalı, A/B testleri önce burada okunmalı.",
      f"<b>USA (the biggest dot, on the zero line: spending flat at {us_chg}).</b> {us_share} of "
      f"Market Match's App Store ratings come from the US, averaging {fmt.num(us_avg, 2)} ★, the highest of the "
      f"large markets. The US is also #1 by spending (${fmt.num(us_spend, 1)}B, p. {p_us}) and spends "
      f"${fmt.num(spd_us, 2)} per download against ${fmt.num(spd_world, 2)} worldwide (p. {p_w}–{p_u}). Protect "
      "the US experience, and read A/B tests there first."),
    T(f"<b>Japonya (sol alt, “dikkat” bölgesi).</b> Harcamada 3. büyük pazar ({fmt.num(jp_spend, 1)} milyar $, "
      f"s. {p_jp}) ama 2024'te {chg(yoy.loc['jp', 'value'])} küçüldü (s. {int(yoy.loc['jp', 'page'])}). Market "
      f"Match'in de en düşük puanlı büyük pazarı ({fmt.num(jp_avg, 2)} ★, {jp_n} puan). Sadece {written_jp} yazılı "
      "yorum var ve ikisi de 5★, yani nedeni bilinmiyor. Buraya reklam bütçesi ayırmadan önce çeviri, zorluk ve "
      "seviye ilerlemesine bakılmalı.",
      f"<b>Japan (bottom left, “caution” region).</b> The #3 market by spending (${fmt.num(jp_spend, 1)}B, "
      f"p. {p_jp}) shrank {chg(yoy.loc['jp', 'value'])} in 2024 (p. {int(yoy.loc['jp', 'page'])}), and it is "
      f"Market Match's lowest-rated large market ({fmt.num(jp_avg, 2)} ★ from {jp_n} ratings). There are only "
      f"{written_jp} written reviews, both 5★, so the reason is unknown. Check translation, difficulty and level "
      "progress before spending ad budget there."),
    T(f"<b>Meksika (sağ üst, “fırsat” bölgesi) ve Türkiye (tam ortalama çizgisinde).</b> En hızlı büyüyen "
      f"pazarlar arasındalar (Meksika {chg(yoy.loc['mx', 'value'])}, Türkiye {chg(yoy.loc['tr', 'value'])}, s. "
      f"{int(yoy.loc['mx', 'page'])}). Meksika Market Match'e ortalamanın üstünde, Türkiye ortalamaya çok yakın "
      f"puan veriyor (Meksika {fmt.num(mx_avg, 2)} ★ / {mx_n} puan, Türkiye {fmt.num(tr_avg, 2)} ★ / {tr_n} puan). "
      f"Brezilya da hızlı büyüyor ({chg(yoy.loc['br', 'value'])}) ve puanı yüksek, ama sadece {br_n} puan olduğu "
      "için grafikte yok. Küçük, yerel test kampanyaları için aday pazarlar; henüz kesin sonuç değil.",
      f"<b>Mexico (top right, “opportunity” region) and Turkey (right on the average line).</b> Both are among "
      f"the fastest-growing markets (Mexico {chg(yoy.loc['mx', 'value'])}, Turkey {chg(yoy.loc['tr', 'value'])}, "
      f"p. {int(yoy.loc['mx', 'page'])}). Mexico rates Market Match above average and Turkey very close to it "
      f"(Mexico {fmt.num(mx_avg, 2)} ★ / {mx_n} ratings, Turkey {fmt.num(tr_avg, 2)} ★ / {tr_n} ratings). Brazil "
      f"is also growing fast ({chg(yoy.loc['br', 'value'])}) and rates it highly, but with only {br_n} ratings it "
      "is not on the chart. Candidates for small local test campaigns, not yet conclusions."),
    T(f"<b>Almanya ve Hollanda (sağ alt).</b> Pazar büyüyor ama Market Match buralarda ortalamanın altında "
      f"({fmt.num(mm('de')[1], 2)} ★ ve {fmt.num(mm('nl')[1], 2)} ★); nedeni araştırılmaya değer.",
      f"<b>Germany and the Netherlands (bottom right).</b> The market is growing but Market Match is below "
      f"average there ({fmt.num(mm('de')[1], 2)} ★ and {fmt.num(mm('nl')[1], 2)} ★); worth finding out why."),
    T("Sınırlar: puan sayısı indirme sayısı değil ve ülke bazında puan sayısını sadece App Store yayınlıyor.",
      "Limits: ratings are not downloads, and only the App Store publishes rating counts per country."),
])

with st.expander(T("Bu sayfada kullanılan bütün sektör rakamları", "All industry figures used on this page")):
    st.dataframe(B.rename(columns={
        "section": T("Bölüm", "Section"), "item": T("Kalem (rapordaki adı)", "Item (report wording)"),
        "value": T("Değer", "Value"), "unit": T("Birim", "Unit"), "page": T("Rapor sayfası", "Report page"),
        "pdf_page": T("PDF sayfası", "PDF page"), "year": T("Yıl", "Year"),
        "cohort": T("Kapsanan oyunlar", "Games covered")}),
        hide_index=True, width="stretch")
    st.caption(T(f"Kaynak: {load.BENCHMARK_SOURCE}. Rakamlar rapordan birebir aktarıldı; grafikler kopyalanmadı, "
                 "yeniden çizildi.",
                 f"Source: {load.BENCHMARK_SOURCE}. Figures were transcribed verbatim from the report; the charts "
                 "are redrawn, not copied."))
