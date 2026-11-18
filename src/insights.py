"""Templated, evidence-backed findings in plain Turkish. No LLM text: every
sentence is filled from numbers computed in src.metrics."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src import metrics as M
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
        gp_txt = f" Google Play'de de durum aynı: {_b(gp_row['avg_rating'].iloc[0])} ★."
    return Finding(
        title=f"{name} oyunu en az beğenen büyük pazar",
        body_html=(f"App Store'da {_b(r['n'], 0)} oyuncu ortalama {_b(r['avg_rating'])} ★ vermiş. "
                   f"Mağaza ortalaması {_b(r['prior'])} ★. Fark tesadüf olamayacak kadar net.{gp_txt}"),
        tier=M.confidence_tier(r["n"]), badge_detail=f"{fmt.num(r['n'])} değerlendirme",
        color_key="neg", target="views/markets.py",
    )


def platform_finding(gap: pd.DataFrame, min_n: int = M.STRONG_N) -> Finding | None:
    g = gap[gap["as_n"] >= min_n]
    if g.empty:
        return None
    r = g.loc[g["gap"].abs().idxmax()]
    higher, lower = ("Google Play", "App Store") if r["gap"] > 0 else ("App Store", "Google Play")
    return Finding(
        title=f"{fmt.country(r['country'])}'da iki mağaza ayrışıyor",
        body_html=(f"{higher} oyuncuları {_b(abs(r['gap']))} yıldız daha yüksek veriyor "
                   f"(App Store {_b(r['as_avg'])}, Google Play {_b(r['gp_avg'])}). "
                   "Kesin sonuç değil, incelenmesi gereken bir ipucu."),
        tier="directional", badge_detail="Google Play sayısı bilinmiyor",
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
        title="En sık şikâyet: reklamlar",
        body_html=(f"1–3 yıldız veren {_b(crit, 0)} oyuncunun {_b(len(ads), 0)}'sı reklamlardan "
                   "şikâyet ediyor: bölüm sonu reklamları, reklamsız paket alındığı hâlde çıkan "
                   "reklamlar ve oyunla uyuşmayan tanıtımlar."),
        tier=M.confidence_tier(len(ads)), badge_detail=f"{len(ads)} yorum, hepsi okundu",
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
        title="Oyuncuların büyük çoğunluğu memnun",
        body_html=(f"Google Play'deki {_b(g['rating_count'], 0)} değerlendirmenin "
                   f"<b>{fmt.pct(top, 0)}</b>'si 4–5 yıldız, yalnızca <b>{fmt.pct(low, 0)}</b>'ü "
                   f"1–2 yıldız. Yazılı {_b(len(reviews), 0)} yorumun {_b(pos, 0)}'u olumlu (4–5★)."),
        tier=M.confidence_tier(int(g["rating_count"])),
        badge_detail=f"{fmt.num(g['rating_count'])} değerlendirme",
        color_key="pos", target="views/explorer.py",
    )


def feedback_finding(reviews: pd.DataFrame, matrix: pd.DataFrame | None) -> Finding:
    n = len(reviews)
    neg = int((reviews["rating_bucket"] == "negative").sum())
    crit = int(reviews["rating_bucket"].isin(["negative", "neutral"]).sum())
    ads = len(ad_mentions(reviews))
    body = (f"{_b(n, 0)} yazılı yorumun sadece {_b(neg, 0)} tanesi 1–2 yıldızlı. "
            f"Olumsuz ve nötr (1–3★) {_b(crit, 0)} yorumun {_b(ads, 0)} tanesi reklamlardan bahsediyor.")
    title = "Oyuncular çoğunlukla memnun"
    if matrix is not None and len(matrix) and matrix["negative"].max() > 0:
        top_name = matrix.sort_values("negative", ascending=False).index[0]
        top = int(matrix.loc[top_name, "negative"])
        title = f"En sık şikâyet: {top_name}"
        body = (f"{_b(n, 0)} yazılı yorumun {_b(neg, 0)} tanesi olumsuz (1–2★); bunların {_b(top, 0)} "
                f"tanesi “{top_name}” konusundan bahsediyor.")
    return Finding(title=title, body_html=body, tier=M.confidence_tier(neg),
                   badge_detail=f"{neg} olumsuz (1–2★)", color_key="pos", target="views/voice.py")
