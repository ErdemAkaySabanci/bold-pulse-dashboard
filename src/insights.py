"""Templated, evidence-backed findings in plain language (TR / EN). No LLM text: every
sentence is filled from numbers computed in src.metrics. Each sentence is written twice,
T(turkish, english), so neither language is a word-for-word translation of the other."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src import metrics as M
from src.i18n import T
from src.ui import fmt


@dataclass
class Finding:
    title: str
    body_html: str
    tier: str
    badge_detail: str
    color_key: str
    target: str


def _b(x, d=2) -> str:
    return f"<b>{fmt.num(x, d)}</b>"


def below_average_markets(countries: pd.DataFrame, min_n: int = M.STRONG_N) -> pd.DataFrame:
    """App Store markets with n >= min_n whose whole likely range sits below the store average."""
    c = countries[countries["n"] >= min_n]
    return c[c["ci_high"] < c["prior"]].sort_values("avg_rating")


def market_finding(countries: pd.DataFrame, gp: pd.DataFrame) -> Finding | None:
    below = below_average_markets(countries)
    if below.empty:
        return None
    r = below.iloc[0]
    name = fmt.country(r["country"])
    gp_row = gp[gp["country"] == r["country"]]
    gp_txt = ""
    if len(gp_row):
        gp_txt = T(f" Google Play'de de durum aynı: {_b(gp_row['avg_rating'].iloc[0])} ★.",
                   f" Google Play tells the same story: {_b(gp_row['avg_rating'].iloc[0])} ★.")
    return Finding(
        title=T(f"{name} oyunu en az beğenen büyük pazar", f"{name} likes the game least of the large markets"),
        body_html=T(f"App Store'da {_b(r['n'], 0)} oyuncu ortalama {_b(r['avg_rating'])} ★ vermiş. "
                    f"Mağaza ortalaması {_b(r['prior'])} ★. Fark tesadüf olamayacak kadar net.{gp_txt}",
                    f"{_b(r['n'], 0)} App Store players gave an average of {_b(r['avg_rating'])} ★, against a "
                    f"store average of {_b(r['prior'])} ★. The gap is too clear to be chance.{gp_txt}"),
        tier=M.confidence_tier(r["n"]), badge_detail=f"{fmt.num(r['n'])} {T('değerlendirme', 'ratings')}",
        color_key="neg", target="views/markets.py",
    )


def platform_finding(gap: pd.DataFrame, min_n: int = M.STRONG_N) -> Finding | None:
    g = gap[gap["as_n"] >= min_n]
    if g.empty:
        return None
    r = g.loc[g["gap"].abs().idxmax()]
    higher = "Google Play" if r["gap"] > 0 else "App Store"
    return Finding(
        title=T(f"{fmt.country(r['country'])}'da iki mağaza ayrışıyor",
                f"The two stores disagree in {fmt.country(r['country'])}"),
        body_html=T(f"{higher} oyuncuları {_b(abs(r['gap']))} yıldız daha yüksek veriyor "
                    f"(App Store {_b(r['as_avg'])}, Google Play {_b(r['gp_avg'])}). "
                    "Kesin sonuç değil, incelenmesi gereken bir ipucu.",
                    f"{higher} players rate it {_b(abs(r['gap']))} stars higher "
                    f"(App Store {_b(r['as_avg'])}, Google Play {_b(r['gp_avg'])}). "
                    "Not a conclusion, a lead worth checking."),
        tier="directional", badge_detail=T("Google Play sayısı bilinmiyor", "Google Play count unknown"),
        color_key="purple", target="views/markets.py",
    )


# Multilingual keyword match for advertising, used until Stage 3 topic labels exist.
AD_PATTERN = r"\b(?:ads?|advert\w*|reklam\w*|werbung|publicit\w*|pub|anúncio\w*|anuncio\w*|propaganda)\b"


def ad_mentions(reviews: pd.DataFrame) -> pd.DataFrame:
    """Negative or neutral reviews that mention advertising (keyword match)."""
    crit = reviews[reviews["rating_bucket"].isin(["negative", "neutral"])]
    return crit[crit["text"].str.lower().str.contains(AD_PATTERN, regex=True)]


def ads_finding(reviews: pd.DataFrame) -> Finding | None:
    """The most frequent complaint in 1–3★ reviews, backed by the reviews themselves."""
    crit = int(reviews["rating_bucket"].isin(["negative", "neutral"]).sum())
    ads = ad_mentions(reviews)
    if crit == 0 or ads.empty:
        return None
    return Finding(
        title=T("En sık şikâyet: reklamlar", "Top complaint: ads"),
        body_html=T(f"1–3 yıldız veren {_b(crit, 0)} oyuncunun {_b(len(ads), 0)}'sı reklamlardan "
                    "şikâyet ediyor: bölüm sonu reklamları, reklamsız paket alındığı hâlde çıkan "
                    "reklamlar ve oyunla uyuşmayan tanıtımlar.",
                    f"{_b(len(ads), 0)} of the {_b(crit, 0)} players who gave 1–3 stars complain about ads: "
                    "end-of-level ads, ads that still appear after buying the no-ads pack, and promo videos "
                    "that don't match the game."),
        tier=M.confidence_tier(len(ads)),
        badge_detail=T(f"{len(ads)} yorum, hepsi okundu", f"{len(ads)} reviews, all read"),
        color_key="orange", target="views/voice.py",
    )


def satisfaction_finding(ratings: pd.DataFrame, reviews: pd.DataFrame) -> Finding | None:
    """Overall satisfaction from Google Play's global star mix (the only published distribution)."""
    g = ratings[(ratings["store"] == "google_play") & (ratings["scope"] == "global")]
    if g.empty:
        return None
    g = g.iloc[0]
    top = float(g["share_4"] + g["share_5"])
    low = float(g["share_1"] + g["share_2"])
    pos = int((reviews["rating_bucket"] == "positive").sum())
    return Finding(
        title=T("Oyuncuların büyük çoğunluğu memnun", "Most players are happy"),
        body_html=T(f"Google Play'deki {_b(g['rating_count'], 0)} değerlendirmenin "
                    f"<b>{fmt.pct(top, 0)}</b>'si 4–5 yıldız, yalnızca <b>{fmt.pct(low, 0)}</b>'ü "
                    f"1–2 yıldız. Yazılı {_b(len(reviews), 0)} yorumun {_b(pos, 0)}'u olumlu (4–5★).",
                    f"<b>{fmt.pct(top, 0)}</b> of the {_b(g['rating_count'], 0)} Google Play ratings are 4–5 "
                    f"stars and only <b>{fmt.pct(low, 0)}</b> are 1–2 stars. {_b(pos, 0)} of the "
                    f"{_b(len(reviews), 0)} written reviews are positive (4–5★)."),
        tier=M.confidence_tier(int(g["rating_count"])),
        badge_detail=f"{fmt.num(g['rating_count'])} {T('değerlendirme', 'ratings')}",
        color_key="pos", target="views/explorer.py",
    )


def feedback_finding(reviews: pd.DataFrame, matrix: pd.DataFrame | None) -> Finding:
    n = len(reviews)
    neg = int((reviews["rating_bucket"] == "negative").sum())
    crit = int(reviews["rating_bucket"].isin(["negative", "neutral"]).sum())
    ads = len(ad_mentions(reviews))
    body = T(f"{_b(n, 0)} yazılı yorumun sadece {_b(neg, 0)} tanesi 1–2 yıldızlı. "
             f"Olumsuz ve nötr (1–3★) {_b(crit, 0)} yorumun {_b(ads, 0)} tanesi reklamlardan bahsediyor.",
             f"Only {_b(neg, 0)} of {_b(n, 0)} written reviews are 1–2 stars. {_b(ads, 0)} of the "
             f"{_b(crit, 0)} negative and neutral (1–3★) reviews mention ads.")
    title = T("Oyuncular çoğunlukla memnun", "Players are mostly happy")
    if matrix is not None and len(matrix) and matrix["negative"].max() > 0:
        top_name = matrix.sort_values("negative", ascending=False).index[0]
        top = int(matrix.loc[top_name, "negative"])
        title = T(f"En sık şikâyet: {top_name}", f"Top complaint: {top_name}")
        body = T(f"{_b(n, 0)} yazılı yorumun {_b(neg, 0)} tanesi olumsuz (1–2★); bunların {_b(top, 0)} "
                 f"tanesi “{top_name}” konusundan bahsediyor.",
                 f"{_b(neg, 0)} of {_b(n, 0)} written reviews are negative (1–2★); {_b(top, 0)} of them "
                 f"are about “{top_name}”.")
    return Finding(title=title, body_html=body, tier=M.confidence_tier(neg),
                   badge_detail=T(f"{neg} olumsuz (1–2★)", f"{neg} negative (1–2★)"),
                   color_key="pos", target="views/voice.py")


# ---------------------------------------------------------------------------------------------
# Chart takeaways: 2–3 short bullets under every chart ("what we see" -> "what it means").
# Every number is computed here from the same frames the chart draws; nothing is hand-typed.
# Country names are followed by a colon or parenthesis, never a Turkish suffix, so any
# country reads correctly.
# ---------------------------------------------------------------------------------------------

def _c(code: str) -> str:
    return f"<b>{fmt.country(code)}</b>"


def map_takeaways(countries: pd.DataFrame) -> list[str]:
    """World map of App Store ratings by country."""
    if countries.empty:
        return []
    c = countries.sort_values("n", ascending=False)
    total = int(c["n"].sum())
    top3 = c.head(3)
    top1_share = fmt.pct(c['n'].iloc[0] / total, 0)
    top3_names = ", ".join(fmt.country(x) for x in top3["country"])
    top3_share = fmt.pct(top3['n'].sum() / total, 0)
    out = [T(f"Değerlendirmelerin <b>{top1_share}</b>'i tek ülkeden geliyor ({_c(c['country'].iloc[0])}); "
             f"ilk 3 ülke ({top3_names}) toplamın <b>{top3_share}</b>'ü.",
             f"<b>{top1_share}</b> of the ratings come from one country ({_c(c['country'].iloc[0])}); the top 3 "
             f"({top3_names}) make up <b>{top3_share}</b> of the total.")]
    if c["n"].iloc[0] / total >= 0.5:
        top_avg = fmt.num(c['avg_rating'].iloc[0], 2)
        out.append(T(f"Bu yüzden genel ortalamayı büyük ölçüde tek pazar belirliyor ({_c(c['country'].iloc[0])}: "
                     f"{top_avg} ★); diğer pazarların sesi ortalamada az duyuluyor.",
                     f"So a single market largely sets the overall average ({_c(c['country'].iloc[0])}: "
                     f"{top_avg} ★); other markets barely move it."))
    few = c[c["n"] < 10]
    if len(few):
        out.append(T(f"{len(c)} ülkenin <b>{len(few)}</b>'inde 10'dan az değerlendirme var; bu ülkelerin "
                     "rengi birkaç oyla oluşuyor, tek başına yorumlanmamalı.",
                     f"<b>{len(few)}</b> of the {len(c)} countries have fewer than 10 ratings; their colour rests "
                     "on a handful of votes and should not be read on its own."))
    return out


def stars_takeaways(ratings: pd.DataFrame) -> list[str]:
    """Google Play global star distribution."""
    g = ratings[(ratings["store"] == "google_play") & (ratings["scope"] == "global")]
    if g.empty:
        return []
    g = g.iloc[0]
    five = fmt.pct(float(g["share_5"]), 0)
    mid = fmt.pct(float(g["share_3"] + g["share_4"]), 0)
    low = fmt.pct(float(g["share_1"] + g["share_2"]), 0)
    return [
        T(f"Değerlendirmelerin <b>{five}</b>'i 5 yıldız; 1–2 yıldızın toplamı yalnızca <b>{low}</b>.",
          f"<b>{five}</b> of the ratings are 5 stars; 1–2 stars add up to only <b>{low}</b>."),
        T(f"Kötü puan azınlıkta. Asıl fırsat 3–4 yıldız veren <b>{mid}</b>'lik kesim: "
          "küçük dertleri çözülürse ortalamayı en hızlı onlar yükseltir.",
          f"Bad ratings are rare. The real opportunity is the <b>{mid}</b> who give 3–4 stars: fixing their "
          "small issues would lift the average fastest."),
    ]


def tone_takeaways(reviews: pd.DataFrame) -> list[str]:
    """Positive / neutral / negative split of written reviews."""
    n = len(reviews)
    if n == 0:
        return []
    pos = int((reviews["rating_bucket"] == "positive").sum())
    neg = int((reviews["rating_bucket"] == "negative").sum())
    crit = int(reviews["rating_bucket"].isin(["negative", "neutral"]).sum())
    ads = len(ad_mentions(reviews))
    short = int(reviews["is_short"].sum()) if "is_short" in reviews else 0
    out = [T(f"{fmt.num(n)} yazılı yorumun <b>{pos}</b>'i olumlu ({fmt.pct(pos / n, 0)}); olumsuz yalnızca "
             f"<b>{neg}</b>.",
             f"<b>{pos}</b> of {fmt.num(n)} written reviews are positive ({fmt.pct(pos / n, 0)}); only "
             f"<b>{neg}</b> are negative.")]
    if crit and ads:
        out.append(T(f"1–3★ veren {crit} oyuncunun <b>{ads}</b>'sı reklamdan bahsediyor: şikâyetlerin en sık "
                     "nedeni reklam akışı.",
                     f"<b>{ads}</b> of the {crit} players who gave 1–3★ mention ads: the ad flow is the most "
                     "common reason for complaints."))
    if short:
        out.append(T(f"{short} yorum 20 karakterden kısa (“süper”, “love it”); memnuniyeti gösterir ama "
                     "nedenini anlatmaz.",
                     f"{short} reviews are shorter than 20 characters (“super”, “love it”): they show "
                     "satisfaction but not the reason for it."))
    return out


def timeline_takeaways(reviews: pd.DataFrame, events: pd.DataFrame | None = None) -> list[str]:
    """Every written review over time, sized by thumbs-up."""
    if reviews.empty:
        return []
    per = reviews["date"].dt.strftime("%Y-%m").value_counts()
    span = max(1, len(per))
    peak, peak_n, avg = fmt.month_label(per.idxmax()), int(per.max()), fmt.num(len(reviews) / span)
    out = [T(f"En yoğun ay <b>{peak}</b> ({peak_n} yorum); genelde ayda ortalama <b>{avg}</b> yorum geliyor.",
             f"The busiest month was <b>{peak}</b> ({peak_n} reviews); on average about <b>{avg}</b> reviews "
             "arrive per month.")]
    gp = reviews.loc[reviews["store"] == "google_play", "date"]
    if len(gp) and gp.max() < reviews["date"].max():
        out.append(T(f"Google Play'den son yorum <b>{fmt.date_long(gp.max())}</b> tarihli; sonrasında yalnızca "
                     "App Store yorumları var.",
                     f"The last Google Play review is dated <b>{fmt.date_long(gp.max())}</b>; after that there "
                     "are only App Store reviews."))
    if events is not None and len(events):
        out.append(T("Ayda bu kadar az yorumla bir sürümün ya da etkinliğin puanı değiştirdiği söylenemez; "
                     "kırmızı çizgiler yalnızca bağlam verir.",
                     "With this few reviews per month, no release or event can be said to have moved the "
                     "rating; the red lines only give context."))
    return out


def concentration_takeaways(countries: pd.DataFrame) -> list[str]:
    """Treemap: how concentrated the market is."""
    if len(countries) <= 5:
        return []
    c = countries.sort_values("n", ascending=False)
    top5 = float(c["n"].head(5).sum() / c["n"].sum())
    return [
        T(f"İlk 5 ülke değerlendirmelerin <b>{fmt.pct(top5, 0)}</b>'i; kalan <b>{len(c) - 5}</b> ülkenin "
          f"toplam payı {fmt.pct(1 - top5, 0)}.",
          f"The top 5 countries hold <b>{fmt.pct(top5, 0)}</b> of the ratings; the remaining "
          f"<b>{len(c) - 5}</b> countries share {fmt.pct(1 - top5, 0)}."),
        T(f"Veri büyük ölçüde tek pazara dayanıyor ({_c(c['country'].iloc[0])}). Başka bir pazarda büyüme "
          "hedefleniyorsa o pazarın verisi henüz ince; karar öncesi o ülkeye özel veri toplanmalı.",
          f"The data leans heavily on one market ({_c(c['country'].iloc[0])}). If growth elsewhere is the goal, "
          "that market's data is still thin; collect country-specific data before deciding."),
    ]


def ranking_takeaways(countries: pd.DataFrame, min_n: int = M.STRONG_N) -> list[str]:
    """Country ranking with likely ranges vs the store average."""
    s = countries[countries["n"] >= min_n].sort_values("avg_rating")
    if len(s) < 2:
        return []
    prior = float(countries["prior"].iloc[0])
    best, worst = s.iloc[-1], s.iloc[0]
    b_avg, w_avg = fmt.num(best['avg_rating'], 2), fmt.num(worst['avg_rating'], 2)
    out = [T(f"{min_n}+ değerlendirmesi olan <b>{len(s)}</b> ülkede en yüksek {_c(best['country'])} "
             f"({b_avg} ★), en düşük {_c(worst['country'])} ({w_avg} ★).",
             f"Among the <b>{len(s)}</b> countries with {min_n}+ ratings, the highest is "
             f"{_c(best['country'])} ({b_avg} ★) and the lowest {_c(worst['country'])} ({w_avg} ★).")]
    below = below_average_markets(countries, min_n)
    if len(below) == 1:
        out.append(T(f"Olası aralığının tamamı mağaza ortalamasının ({fmt.num(prior, 2)} ★) altında kalan tek "
                     f"ülke {_c(below['country'].iloc[0])}: fark tesadüf değil; yerelleştirme ve zorluk "
                     "açısından incelenmeye değer.",
                     f"{_c(below['country'].iloc[0])} is the only country whose whole likely range sits below "
                     f"the store average ({fmt.num(prior, 2)} ★): the gap is not chance, and localisation and "
                     "difficulty are worth checking."))
    elif len(below) > 1:
        names = ", ".join(fmt.country(x) for x in below["country"])
        out.append(T(f"Olası aralığının tamamı mağaza ortalamasının altında kalan <b>{len(below)}</b> ülke var "
                     f"({names}); fark tesadüf değil.",
                     f"<b>{len(below)}</b> countries have their whole likely range below the store average "
                     f"({names}); the gap is not chance."))
    top = countries.sort_values("n", ascending=False).iloc[0]
    others = s[s["country"] != top["country"]]
    if len(others) and bool((others["avg_rating"] < prior).all()):
        out.append(T(f"En büyük pazar ({_c(top['country'])}) dışındaki büyük pazarların hepsi mağaza "
                     "ortalamasının altında: ortalamayı en büyük pazar yukarı çekiyor.",
                     f"Every large market other than the biggest one ({_c(top['country'])}) is below the store "
                     "average: the biggest market pulls the average up."))
    return out


def platform_takeaways(gap: pd.DataFrame, min_n: int = M.DIRECTIONAL_N) -> list[str]:
    """App Store vs Google Play average in the same country."""
    g = gap[gap["as_n"] >= min_n]
    if g.empty:
        return []
    close = int((g["gap"].abs() < 0.2).sum())
    out = [T(f"{min_n}+ App Store değerlendirmesi olan <b>{len(g)}</b> ülkenin <b>{close}</b>'inde iki "
             "mağazanın ortalaması birbirine yakın (fark 0,2 yıldızdan az).",
             f"In <b>{close}</b> of the <b>{len(g)}</b> countries with {min_n}+ App Store ratings, the two "
             "stores' averages are close (less than 0.2 stars apart).")]
    big = g[g["as_n"] >= M.STRONG_N]
    if len(big):
        r = big.loc[big["gap"].abs().idxmax()]
        higher = "Google Play" if r["gap"] > 0 else "App Store"
        diff = fmt.num(abs(r['gap']), 2)
        out.append(T(f"Büyük pazarlarda en belirgin fark {_c(r['country'])}: {higher} oyuncuları "
                     f"<b>{diff}</b> yıldız daha yüksek veriyor.",
                     f"Among large markets the clearest gap is {_c(r['country'])}: {higher} players rate it "
                     f"<b>{diff}</b> stars higher."))
    extreme = g[g["gp_avg"] >= 4.95]
    ex_val = fmt.num(extreme['gp_avg'].iloc[0], 2) if len(extreme) else ""
    example_tr = f" (örneğin {_c(extreme['country'].iloc[0])}: {ex_val} ★)" if len(extreme) else ""
    example_en = f" (for example {_c(extreme['country'].iloc[0])}: {ex_val} ★)" if len(extreme) else ""
    out.append(T("Google Play her ülkenin yıldız ortalamasını gösteriyor ama bu ortalamanın kaç oya dayandığını "
                 f"göstermiyor. Uç değerler{example_tr} birkaç oydan gelebilir; bu yüzden farklar yön gösterir, "
                 "kesin değildir.",
                 "Google Play shows each country's average but not how many votes it rests on. Extreme values"
                 f"{example_en} may come from a few votes, so these gaps are a direction, not a conclusion."))
    return out


def label_takeaways(tbl: pd.DataFrame, churn_gemini: int, churn_human: int) -> list[str]:
    """AI-vs-human label agreement table (Methodology, Turkish-only page)."""
    if tbl.empty:
        return []
    strong = [fmt.topic(r.topic) for r in tbl.itertuples() if M.topic_reliability(r.kappa) == "strong"]
    mid = [fmt.topic(r.topic) for r in tbl.itertuples() if M.topic_reliability(r.kappa) == "directional"]
    out = [f"Konu bazında ortalama uyum <b>{fmt.pct(float(tbl['agreement'].mean()), 0)}</b>"
           + (f"; <b>{', '.join(strong)}</b> etiketleri güvenilir (κ ≥ 0,7)." if strong else ".")]
    if mid:
        out.append(f"{', '.join(mid)} etiketleri orta düzeyde; bu konulardaki sayılar temkinli okunmalı.")
    if churn_gemini > churn_human:
        out.append(f"Oyunu bırakma sinyalinde Gemini {churn_gemini}, insan {churn_human} yorum işaretledi; "
                   "bu yüzden örneklemdeki yorumlarda dashboard insan etiketini kullanıyor.")
    return out
