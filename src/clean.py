"""Stage 2: clean raw reviews and write a data-quality report.

Run:  python -m src.clean
Input:  data/reviews_raw.csv
Output: data/reviews_clean.csv, data/quality_report.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import pandas as pd

from src import config

# Reviews this short ("ok", "love it") carry a rating but almost never a topic.
SHORT_TEXT_CHARS = 20


def rating_bucket(rating: int) -> str:
    if rating <= 2:
        return "negative"
    if rating == 3:
        return "neutral"
    return "positive"


def to_utc(series: pd.Series) -> pd.Series:
    """Google Play dates are naive UTC; App Store dates carry an offset."""
    return pd.to_datetime(series, errors="coerce", utc=True, format="mixed")


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    steps: list[dict] = []
    df = raw.copy()

    def log(step: str, before: int) -> None:
        steps.append({"step": step, "removed": before - len(df), "remaining": len(df)})

    df["text"] = df["text"].fillna("").astype(str).str.strip()
    n = len(df)
    df = df[df["text"] != ""]
    log("drop empty text", n)

    n = len(df)
    df = df.drop_duplicates("review_id")
    log("drop duplicate review_id", n)

    # The same review can surface under two IDs when collected from two sources
    # (RSS + SerpAPI) or two locales.
    n = len(df)
    df = df.drop_duplicates(["store", "text", "rating", "date"])
    log("drop duplicate store+text+rating+date", n)

    df["date"] = to_utc(df["date"])
    df["reply_date"] = to_utc(df["reply_date"])
    n = len(df)
    df = df[df["date"].notna()]
    log("drop unparseable date", n)

    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").astype("Int64")
    n = len(df)
    df = df[df["rating"].between(1, 5)]
    log("drop missing/invalid rating", n)

    df["thumbs_up"] = pd.to_numeric(df["thumbs_up"], errors="coerce").fillna(0).astype(int)
    df["app_version"] = (
        df["app_version"].astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    )
    df["has_reply"] = df["developer_reply"].notna()

    df["text_len"] = df["text"].str.len()
    df["word_count"] = df["text"].str.split().str.len()
    df["is_short"] = df["text_len"] <= SHORT_TEXT_CHARS
    df["rating_bucket"] = df["rating"].astype(int).map(rating_bucket)
    df["month"] = df["date"].dt.strftime("%Y-%m")

    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df, {"steps": steps}


def quality_report(raw: pd.DataFrame, df: pd.DataFrame, steps: dict) -> dict:
    def counts(s: pd.Series) -> dict:
        return {str(k): int(v) for k, v in s.value_counts().sort_index().items()}

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "raw_rows": len(raw),
        "clean_rows": len(df),
        "cleaning_steps": steps["steps"],
        "by_store": counts(df["store"]),
        "by_source": counts(df["source"]),
        "by_lang": counts(df["lang"]),
        "by_rating": counts(df["rating"]),
        "by_rating_bucket": counts(df["rating_bucket"]),
        "by_month": counts(df["month"]),
        "date_range": {
            store: {"min": g["date"].min().isoformat(), "max": g["date"].max().isoformat()}
            for store, g in df.groupby("store")
        },
        "short_text": {
            "threshold_chars": SHORT_TEXT_CHARS,
            "count": int(df["is_short"].sum()),
        },
        "app_versions": {
            "distinct": int(df["app_version"].nunique()),
            "missing": int(df["app_version"].isna().sum()),
        },
        "developer_replies": int(df["has_reply"].sum()),
        "missing_by_column": {c: int(v) for c, v in df.isna().sum().items() if v},
        "known_limitations": [
            "Google Play does not expose the reviewer's country; only review language is known.",
            "No verified release dates exist for app versions.",
            "Written reviews are a small, self-selected subset of all star ratings.",
        ],
    }


def main() -> None:
    raw = pd.read_csv(config.RAW_CSV, dtype={"app_version": "string", "review_id": "string"})
    df, steps = clean(raw)
    report = quality_report(raw, df, steps)

    df.to_csv(config.CLEAN_CSV, index=False, encoding="utf-8")
    config.QUALITY_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                   encoding="utf-8")

    print("================ STAGE 2 SUMMARY ================")
    print(f"Raw rows: {report['raw_rows']}  ->  clean rows: {report['clean_rows']}")
    for s in report["cleaning_steps"]:
        print(f"  {s['step']:42s} removed {s['removed']:3d}  remaining {s['remaining']}")
    print(f"By store: {report['by_store']}")
    print(f"By rating bucket: {report['by_rating_bucket']}")
    print(f"Short texts (<= {SHORT_TEXT_CHARS} chars): {report['short_text']['count']}")
    print(f"-> {config.CLEAN_CSV.relative_to(config.ROOT)}, "
          f"{config.QUALITY_JSON.relative_to(config.ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
