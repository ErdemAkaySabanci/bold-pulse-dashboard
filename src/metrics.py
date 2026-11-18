"""Pure, testable metric functions used by the dashboard.

Nothing here touches Streamlit or the filesystem, so every number shown in the
UI can be reproduced (and unit-tested) from the CSVs alone.
"""
from __future__ import annotations

import math
from typing import Iterable

import pandas as pd

# Confidence tiers shown next to every metric.
STRONG_N = 50
DIRECTIONAL_N = 20

# Bayesian shrinkage strength: a country's average is pulled toward the global
# average as if it had this many extra ratings at the global mean.
DEFAULT_PRIOR_WEIGHT = 20

BUCKET_ORDER = ["negative", "neutral", "positive"]


def confidence_tier(n: int | float | None) -> str:
    """'strong' (n >= 50), 'directional' (20-49) or 'anecdotal' (< 20 or unknown)."""
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "anecdotal"
    if n >= STRONG_N:
        return "strong"
    if n >= DIRECTIONAL_N:
        return "directional"
    return "anecdotal"


def bayes_avg(mean: float, n: int, prior_mean: float, m: float = DEFAULT_PRIOR_WEIGHT) -> float:
    """Shrink a small-sample average toward `prior_mean` (Bayesian average)."""
    if n <= 0:
        return prior_mean
    return (n * mean + m * prior_mean) / (n + m)


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a proportion k/n. Returns (0, 1) when n == 0."""
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def max_rating_sd(mean: float, lo: float = 1.0, hi: float = 5.0) -> float:
    """Upper bound on the SD of ratings in [lo, hi] with this mean
    (Bhatia-Davis: var <= (hi - mean)(mean - lo)). Lets us build a conservative
    CI when only the mean and count are published (App Store)."""
    return math.sqrt(max(0.0, (hi - mean) * (mean - lo)))


def mean_ci(mean: float, n: int, sd: float, z: float = 1.96,
            lo: float = 1.0, hi: float = 5.0) -> tuple[float, float]:
    """Normal-approximation CI for a mean, clipped to the rating scale."""
    if n <= 0:
        return lo, hi
    half = z * sd / math.sqrt(n)
    return max(lo, mean - half), min(hi, mean + half)


def hist_stats(hist: Iterable[float]) -> tuple[float, float]:
    """Mean and SD of a 1-5 star histogram given as counts or shares."""
    h = [float(x or 0) for x in hist]
    total = sum(h)
    if total == 0:
        return math.nan, math.nan
    mean = sum((i + 1) * x for i, x in enumerate(h)) / total
    var = sum(((i + 1) - mean) ** 2 * x for i, x in enumerate(h)) / total
    return mean, math.sqrt(var)


# --------------------------------------------------------------------------- #
# Ratings (data/ratings_by_country.csv)
# --------------------------------------------------------------------------- #
def store_summary(ratings: pd.DataFrame) -> pd.DataFrame:
    """One row per store: total rating count and count-weighted average.
    App Store sums its per-storefront counts; Google Play uses its global row."""
    out = []
    a = ratings[(ratings["store"] == "app_store") & (ratings["scope"] == "local")]
    if len(a):
        n = a["rating_count"].sum()
        out.append({"store": "app_store", "rating_count": int(n),
                    "avg_rating": float((a["rating_count"] * a["avg_rating"]).sum() / n),
                    "countries": int(len(a))})
    g = ratings[(ratings["store"] == "google_play") & (ratings["scope"] == "global")]
    if len(g):
        out.append({"store": "google_play", "rating_count": int(g["rating_count"].iloc[0]),
                    "avg_rating": float(g["avg_rating"].iloc[0]),
                    "countries": int((ratings["store"].eq("google_play")
                                      & ratings["scope"].eq("local")).sum())})
    return pd.DataFrame(out)


def overall_avg(summary: pd.DataFrame) -> float:
    """Count-weighted average across stores."""
    n = summary["rating_count"].sum()
    return float((summary["rating_count"] * summary["avg_rating"]).sum() / n) if n else math.nan


def app_store_countries(ratings: pd.DataFrame, m: float = DEFAULT_PRIOR_WEIGHT) -> pd.DataFrame:
    """Per-storefront App Store table with Bayesian average, conservative CI and tier.
    The prior is the App Store's own count-weighted average."""
    a = ratings[(ratings["store"] == "app_store") & (ratings["scope"] == "local")].copy()
    if a.empty:
        return a
    prior = float((a["rating_count"] * a["avg_rating"]).sum() / a["rating_count"].sum())
    a["n"] = a["rating_count"].astype(int)
    a["bayes_avg"] = [bayes_avg(r.avg_rating, r.n, prior, m) for r in a.itertuples()]
    cis = [mean_ci(r.avg_rating, r.n, max_rating_sd(r.avg_rating)) for r in a.itertuples()]
    a["ci_low"] = [c[0] for c in cis]
    a["ci_high"] = [c[1] for c in cis]
    a["tier"] = a["n"].map(confidence_tier)
    a["prior"] = prior
    cols = ["country", "n", "avg_rating", "bayes_avg", "ci_low", "ci_high", "tier", "prior"]
    return a[cols].sort_values("n", ascending=False).reset_index(drop=True)


def gp_local(ratings: pd.DataFrame) -> pd.DataFrame:
    """Google Play countries with a local score, plus their local 1-2 star share.
    Local rating counts are not published, so there is no n and no tier."""
    g = ratings[(ratings["store"] == "google_play") & (ratings["scope"] == "local")].copy()
    g["low_share"] = g["share_1"].fillna(0) + g["share_2"].fillna(0)
    return g[["country", "avg_rating", "low_share",
              "share_1", "share_2", "share_3", "share_4", "share_5"]].reset_index(drop=True)


def platform_gap(ratings: pd.DataFrame) -> pd.DataFrame:
    """Countries where both stores publish a local average.
    gap = Google Play avg - App Store avg (positive means Android rates higher)."""
    a = app_store_countries(ratings)[["country", "n", "avg_rating", "tier"]].rename(
        columns={"n": "as_n", "avg_rating": "as_avg", "tier": "as_tier"})
    g = gp_local(ratings)[["country", "avg_rating"]].rename(columns={"avg_rating": "gp_avg"})
    out = a.merge(g, on="country", how="inner")
    out["gap"] = out["gp_avg"] - out["as_avg"]
    return out.sort_values("as_n", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Reviews (data/reviews_clean.csv, data/classified.csv)
# --------------------------------------------------------------------------- #
def bucket_counts(reviews: pd.DataFrame) -> pd.DataFrame:
    """Count, share and Wilson CI for each rating bucket."""
    n = len(reviews)
    rows = []
    for b in BUCKET_ORDER:
        k = int((reviews["rating_bucket"] == b).sum())
        lo, hi = wilson_ci(k, n)
        rows.append({"bucket": b, "count": k, "n": n,
                     "share": k / n if n else math.nan, "ci_low": lo, "ci_high": hi})
    return pd.DataFrame(rows)


def split_labels(value) -> list[str]:
    """Topic cells hold one or more labels separated by ';'."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [p.strip() for p in str(value).split(";") if p.strip()]


def topic_matrix(reviews: pd.DataFrame, topic_col: str = "topics") -> pd.DataFrame:
    """Topic x rating-bucket review counts (a review can carry several topics).
    Counts, not shares: with single-digit negatives a share would mislead."""
    exploded = reviews.assign(_topic=reviews[topic_col].map(split_labels)).explode("_topic")
    exploded = exploded[exploded["_topic"].notna()]
    m = pd.crosstab(exploded["_topic"], exploded["rating_bucket"])
    m = m.reindex(columns=BUCKET_ORDER, fill_value=0)
    m["total"] = m.sum(axis=1)
    return m.sort_values(["negative", "total"], ascending=False)


def topic_summary(reviews: pd.DataFrame, topic_col: str = "topics") -> pd.DataFrame:
    """Per topic: number of reviews mentioning it, their average stars and the
    negative/neutral/positive split. Answers "is the most-mentioned complaint also
    the lowest-rated topic?"."""
    ex = reviews.assign(_topic=reviews[topic_col].map(split_labels)).explode("_topic")
    ex = ex[ex["_topic"].notna() & (ex["_topic"] != "")]
    if ex.empty:
        return pd.DataFrame(columns=["n", "avg_rating", *BUCKET_ORDER])
    g = ex.groupby("_topic")
    out = pd.DataFrame({"n": g.size(), "avg_rating": g["rating"].mean()})
    split = pd.crosstab(ex["_topic"], ex["rating_bucket"]).reindex(columns=BUCKET_ORDER, fill_value=0)
    return out.join(split).sort_values("n", ascending=False)


def cohen_kappa(a: Iterable[bool], b: Iterable[bool]) -> float:
    """Cohen's kappa for two binary raters. NaN when agreement by chance is total."""
    a, b = [bool(x) for x in a], [bool(x) for x in b]
    n = len(a)
    if n == 0 or n != len(b):
        return math.nan
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return math.nan if pe == 1 else (po - pe) / (1 - pe)


def label_agreement(human: pd.DataFrame, model: pd.DataFrame, topics: list[str],
                    col: str = "topics") -> tuple[pd.DataFrame, float]:
    """Per-topic agreement between hand labels and model labels on the same reviews.
    Returns (table with n, agreement, kappa, human_yes, model_yes) and the share of
    reviews whose full topic set matches exactly."""
    m = human[["review_id", col]].merge(model[["review_id", col]], on="review_id",
                                        suffixes=("_h", "_m"))
    hs = m[f"{col}_h"].map(lambda v: set(split_labels(v)))
    ms = m[f"{col}_m"].map(lambda v: set(split_labels(v)))
    rows = []
    for t in topics:
        h = [t in s for s in hs]
        mm = [t in s for s in ms]
        rows.append({"topic": t, "n": len(m),
                     "agreement": (sum(x == y for x, y in zip(h, mm)) / len(m)) if len(m) else math.nan,
                     "kappa": cohen_kappa(h, mm), "human_yes": sum(h), "model_yes": sum(mm)})
    exact = float((hs == ms).mean()) if len(m) else math.nan
    return pd.DataFrame(rows), exact


def matches_display(avg: float, count: int, shown_avg: float, shown_count: int) -> bool:
    """True if our exact numbers round to what the store page displays
    (one decimal for the average, nearest hundred for a count shown as '1,9 B')."""
    return round(avg + 1e-9, 1) == shown_avg and round(count, -2) == shown_count


# level_mentions is not overridden: it is plain number extraction and the hand-label sheet left it
# blank on all 50 rows, so a human "empty" there means "not filled", not "no level".
LABEL_FIELDS = ("topics", "churn_signal", "monetization")


def apply_human_labels(reviews: pd.DataFrame, human: pd.DataFrame | None,
                       fields: Iterable[str] = LABEL_FIELDS) -> pd.DataFrame:
    """Human-in-the-loop final labels: where a finished hand label exists it wins,
    otherwise the model label is kept. The raw model labels stay in `<field>_gemini`
    so agreement can still be measured against them; `label_source` says which won."""
    out = reviews.copy()
    for f in fields:
        if f in out:
            out[f"{f}_gemini"] = out[f]
    out["label_source"] = "gemini"
    if human is None or human.empty:
        return out
    h = human.set_index("review_id")
    mask = out["review_id"].isin(h.index)
    for f in fields:
        if f not in out or f not in h:
            continue
        vals = out.loc[mask, "review_id"].map(h[f])
        if f == "churn_signal":
            vals = vals.astype(str).str.lower().eq("true")
        out.loc[mask, f] = vals.values
    out.loc[mask, "label_source"] = "insan"
    return out


def topic_reliability(kappa: float) -> str:
    """Trust tier for an AI label from its agreement with hand labels."""
    if kappa is None or (isinstance(kappa, float) and math.isnan(kappa)):
        return "anecdotal"
    if kappa >= 0.7:
        return "strong"
    if kappa >= 0.4:
        return "directional"
    return "anecdotal"
