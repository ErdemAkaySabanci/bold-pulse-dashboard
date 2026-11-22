"""Sektörle Kıyas: Appfigures industry benchmark next to Market Match's own store data.

Rules: every industry figure comes from data/industry_benchmark.csv (typed in verbatim, with the
report's printed page number); industry data is drawn in neutral grey and labelled "Sektör verisi",
Market Match data in brand red and labelled "Market Match".
"""
import streamlit as st

from src import insights
from src import metrics as M
from src.data import load
from src.ui import charts, components as C, fmt

B = load.benchmark()
R = load.ratings()
rv = load.reviews()
countries = M.app_store_countries(R).set_index("country")
store_avg = float(countries["prior"].iloc[0])
SRC = "Appfigures, <i>Mobile Games in 2025</i>"


def fig(section: str, item: str) -> tuple[float, int]:
    """(value, printed page) of one industry figure; fails loudly if it is not in the CSV."""
    row = B[(B["section"] == section) & (B["item"] == item)].iloc[0]
    return float(row["value"]), int(row["page"])


def pct(v: float) -> str:
    """Industry percentages are whole numbers in the report: 70 -> '%70', 16.3 -> '%16,3'."""
    return fmt.pct(v / 100, 0 if float(v).is_integer() else 1)


def chg(v: float) -> str:
    """Signed change: 47.1 -> '+%47,1', -6.1 -> '−%6,1'."""
    return ("+" if v > 0 else "−" if v < 0 else "") + f"%{fmt.num(abs(v), 1)}"


C.hero(
    "Sektörle Kıyas",
    "Market Match sektöre göre nerede duruyor?",
    "Appfigures'ın <b>Mobile Games in 2025</b> raporundan (2024 verisi) seçilmiş rakamlar, Market Match'in "
    "kendi App Store ve Google Play puan ve yorumlarının yanında. Grafiklerde <b>gri</b> her zaman "
    "<b>sektör verisi</b>, <b>kırmızı</b> her zaman <b>Market Match</b> demek.",
)
puzzle, p_puzzle = fig("genre_share", "Puzzle")
C.note(f"<b>Dikkatle okuyun.</b> Sektör verisi 2024'ün en çok kazanan 500 ve 1.000 oyununu kapsıyor; bunlar "
       f"çoğunlukla büyük ve olgun oyunlar. Gelir rakamları uygulama içi satın almalardan gelen brüt harcama, "
       f"reklam geliri dahil değil ({SRC}, s. 41). Market Match ise 2026'da çıkmış yeni bir oyun ve buradaki "
       f"verisi mağaza puanları ve yazılı yorumlar: oyuncuların ne söylediği, ne yaptığı değil. Bağlam için: "
       f"Puzzle, en çok kazanan 1.000 oyunun {pct(puzzle)}'ü ve Mid-Core ile yarışabilen tek Casual tür "
       f"({SRC}, s. {p_puzzle}, 35).")

# ---------------------------------------------------------------- monetization
# Market Match column: my play-through to level 84 and the store reviews ("Gözlenmedi" is not "yok").
STATUS = {
    "Consumables/Currency via IAP": "present",       # boosters and coins sold in the Shop
    "Limited-Time Events/Offers": "present",         # "Limited Deal" (80% off) and live events
    "IAP Bundles/Packages": "present",               # Starter Bag and a larger booster bundle
    "In-Game Advertising": "present",                # end-of-level ads reported in reviews
    "Ad-Free Paid Version": "present",               # ad-free play is part of the Starter Bag
    "Rewarded Video Ads": "present",                 # "Clear 3 items" when the tray is full, "+1 Life"
}
# Turkish display names; the report's own wording stays in the hover and in the data table.
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
mon["label"] = mon["item"].map(TR).fillna(mon["item"])
status = {i: STATUS.get(i, "not_observed") for i in mon["item"]}

C.section("Para kazanma: en çok kazananlar ne kullanıyor, Market Match'te ne var?",
          "Gri çubuklar, en çok kazanan 500 oyunun yüzde kaçında o yöntemin bulunduğunu gösteriyor. Sağdaki "
          "sütun, aynı yöntemin Market Match'te görülüp görülmediğini söylüyor.",
          source=(f"Sektör verisi: en çok kazanan 500 oyun, 2024 · {SRC}, s. {int(mon['page'].iloc[0])} · "
                  "Market Match: 84. seviyeye kadar kendi oyun deneyimim ve mağaza yorumları"))
charts.show(charts.monetization_benchmark(mon, status), key="monetization")

n_crit = int(rv["rating_bucket"].isin(["negative", "neutral"]).sum())
n_ads = len(insights.ad_mentions(rv))
cons, p30 = fig("monetization", "Consumables/Currency via IAP")
lto, _ = fig("monetization", "Limited-Time Events/Offers")
rewarded, _ = fig("monetization", "Rewarded Video Ads")
ingame, _ = fig("monetization", "In-Game Advertising")
cosm, _ = fig("monetization", "Unlocks/Cosmetics via IAP")
C.takeaways([
    f"Olmazsa olmazlar yerinde: tüketilebilir ürün satışı ({pct(cons)}) ve sınırlı süreli teklifler "
    f"({pct(lto)}) en çok kazanan 500 oyunun {'hepsinde' if min(cons, lto) == 100 else 'neredeyse hepsinde'} var "
    f"(s. {p30}); Market Match'te de ikisi var "
    "(booster ve coin satışı, %80 indirimli Limited Deal).",
    f"Ödüllü video reklam en çok kazananların {pct(rewarded)}'ında, oyun içi reklam {pct(ingame)}'unda var "
    f"(s. {p30}). Market Match ikisini de kullanıyor: tepsi dolunca “Clear 3 items” ve “+1 Life” için ödüllü "
    f"video, bölüm sonlarında ise reklam. Reklam yine de en sık şikâyet: 1–3★ veren <b>{n_crit} oyuncunun "
    f"{n_ads}</b>'sı reklamdan bahsediyor.",
    f"Kilit açma ve kozmetik satışı en çok kazananların {pct(cosm)}'inde var (s. {p30}), Market Match'te "
    "görülmedi; coin sadece can ve ekstra şans için harcanıyor. En net boşluk bu ve 5. önerideki sepet "
    "özelleştirme fikrini destekliyor.",
    "Sınırlar: rapor “oyun içi reklam”ı tanımlamıyor; bu karşılaştırma gelir etkisini değil, sadece var/yok "
    "durumunu gösteriyor. “Gözlenmedi”, oynadığım kısımda görmediğim anlamına geliyor, kesin yok demek değil.",
])

# ---------------------------------------------------------------- markets
yoy = B[B["section"] == "spend_yoy"].set_index("item")
both = [c for c in yoy.index if c in countries.index and countries.loc[c, "n"] >= M.DIRECTIONAL_N]
pts = countries.loc[both, ["n", "avg_rating"]].assign(
    spend_yoy=yoy.loc[both, "value"].values, page=yoy.loc[both, "page"].values,
    name=[fmt.country(c) for c in both]).reset_index()

C.section("Ülkeler: harcama nerede büyüyor, Market Match orada ne kadar seviliyor?",
          "Her nokta bir ülke. <b>Soldan sağa:</b> o ülkede mobil oyunlara yapılan harcama 2024'te ne kadar "
          "değişti (sağa gittikçe pazar daha hızlı büyüyor). <b>Aşağıdan yukarıya:</b> Market Match'in o "
          "ülkedeki App Store puanı (kesikli çizginin üstü, oyunun genel ortalamasından iyi). <b>Nokta "
          "büyüklüğü:</b> o ülkeden gelen Market Match puanı sayısı. Renkli bölgeler, noktanın düştüğü yerin ne "
          "anlama geldiğini söylüyor.",
          source=(f"Sektör verisi: tüketici harcamasındaki değişim, 2024'e karşı 2023 · {SRC}, s. 7, 23, 24 · "
                  f"Market Match: App Store puanları, hem raporda hem bizde {M.DIRECTIONAL_N}+ puanı olan "
                  f"{len(pts)} ülke"))
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
C.takeaways([
    f"<b>ABD (en büyük nokta, sıfır çizgisinin üstünde: harcama {chg(yoy.loc['us', 'value']) if abs(yoy.loc['us', 'value']) >= 0.1 else '+%' + fmt.num(yoy.loc['us', 'value'], 2)} ile yerinde sayıyor).</b> "
    f"Market Match'in App Store puanlarının "
    f"{fmt.pct(us_n / countries['n'].sum())}'i ABD'den geliyor ve ortalama {fmt.num(us_avg, 2)} ★; büyük "
    f"pazarlar arasında en yüksek. ABD harcamada da 1. sırada ({fmt.num(us_spend, 1)} milyar $, s. {p_us}) ve "
    f"indirme başına {fmt.num(spd_us, 2)} $ harcıyor; dünya ortalaması {fmt.num(spd_world, 2)} $ "
    f"(s. {p_w}–{p_u}). ABD deneyimi korunmalı, A/B testleri önce burada okunmalı.",
    f"<b>Japonya (sol alt, “dikkat” bölgesi).</b> Harcamada 3. büyük pazar ({fmt.num(jp_spend, 1)} milyar $, "
    f"s. {p_jp}) ama 2024'te {chg(yoy.loc['jp', 'value'])} küçüldü (s. {int(yoy.loc['jp', 'page'])}). Market "
    f"Match'in de en düşük puanlı büyük pazarı ({fmt.num(jp_avg, 2)} ★, {jp_n} puan). Sadece {written_jp} yazılı "
    "yorum var ve ikisi de 5★, yani nedeni bilinmiyor. Buraya reklam bütçesi ayırmadan önce çeviri, zorluk ve "
    "seviye ilerlemesine bakılmalı.",
    f"<b>Meksika (sağ üst, “fırsat” bölgesi) ve Türkiye (tam ortalama çizgisinde).</b> En hızlı büyüyen "
    "pazarlar arasındalar "
    f"(Meksika {chg(yoy.loc['mx', 'value'])}, Türkiye {chg(yoy.loc['tr', 'value'])}, s. "
    f"{int(yoy.loc['mx', 'page'])}). Meksika Market Match'e ortalamanın üstünde, Türkiye ortalamaya çok yakın "
    "puan veriyor "
    f"(Meksika {fmt.num(mx_avg, 2)} ★ / {mx_n} puan, Türkiye {fmt.num(tr_avg, 2)} ★ / {tr_n} puan). Brezilya da "
    f"hızlı büyüyor ({chg(yoy.loc['br', 'value'])}) ve puanı yüksek, ama sadece {br_n} puan olduğu için grafikte "
    "yok. Küçük, yerel test kampanyaları için aday pazarlar; henüz kesin sonuç değil.",
    f"<b>Almanya ve Hollanda (sağ alt).</b> Pazar büyüyor ama Market Match buralarda ortalamanın altında "
    f"({fmt.num(mm('de')[1], 2)} ★ ve {fmt.num(mm('nl')[1], 2)} ★); nedeni araştırılmaya değer.",
    "Sınırlar: puan sayısı indirme sayısı değil ve ülke bazında puan sayısını sadece App Store yayınlıyor.",
])

with st.expander("Bu sayfada kullanılan bütün sektör rakamları"):
    st.dataframe(B.rename(columns={"section": "Bölüm", "item": "Kalem (rapordaki adı)", "value": "Değer",
                                   "unit": "Birim", "page": "Rapor sayfası", "pdf_page": "PDF sayfası",
                                   "year": "Yıl", "cohort": "Kapsanan oyunlar"}),
                 hide_index=True, width="stretch")
    st.caption(f"Kaynak: {load.BENCHMARK_SOURCE}. Rakamlar rapordan birebir aktarıldı; grafikler kopyalanmadı, "
               "yeniden çizildi.")
