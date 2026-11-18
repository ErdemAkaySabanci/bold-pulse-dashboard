"""Cached loaders. Every page reads data only through these functions."""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src import config


@st.cache_data(show_spinner=False)
def reviews() -> pd.DataFrame:
    """Clean Stage 2 reviews, joined with translations (3a) and labels (3b) when present."""
    df = pd.read_csv(config.CLEAN_CSV, dtype={"app_version": "string", "review_id": "string"})
    df["date"] = pd.to_datetime(df["date"], utc=True, format="mixed")
    df["rating"] = df["rating"].astype(int)
    for col in ("is_short", "has_reply"):
        if col in df:
            df[col] = df[col].astype(str).str.lower().eq("true")
    # English translations (Stage 3a). `source_lang` is the language the text is really
    # written in; it falls back to the store/locale language when no translation exists.
    df["text_en"] = ""
    df["source_lang"] = df["lang"]
    if config.TRANSLATIONS_CSV.exists():
        tr = pd.read_csv(config.TRANSLATIONS_CSV, dtype={"review_id": "string"},
                         keep_default_na=False)[["review_id", "source_lang", "text_en"]]
        df = df.drop(columns=["text_en", "source_lang"]).merge(tr, on="review_id", how="left")
        df["text_en"] = df["text_en"].fillna("")
        df["source_lang"] = df["source_lang"].replace({"": None}).fillna(df["lang"])
    if config.CLASSIFIED_CSV.exists():
        cl = pd.read_csv(config.CLASSIFIED_CSV, dtype={"review_id": "string"}, keep_default_na=False)
        cols = ["review_id", "topics", "level_mentions", "churn_signal", "monetization",
                "is_request", "request_text"]
        df = df.merge(cl[[c for c in cols if c in cl]], on="review_id", how="left")
        for c in ("topics", "level_mentions", "monetization", "request_text"):
            df[c] = df[c].fillna("")
        for c in ("churn_signal", "is_request"):
            df[c] = df[c].astype(str).str.lower().eq("true")
        df["is_classified"] = df["review_id"].isin(cl["review_id"])
        # Human-in-the-loop: blind hand labels (50-review sample) override Gemini;
        # raw Gemini labels stay in *_gemini for the agreement check.
        from src.metrics import apply_human_labels
        df = apply_human_labels(df, validation())
    return df


def has_translations() -> bool:
    return config.TRANSLATIONS_CSV.exists()


def is_classified() -> bool:
    return config.CLASSIFIED_CSV.exists()


@st.cache_data(show_spinner=False)
def ratings() -> pd.DataFrame:
    return pd.read_csv(config.RATINGS_CSV)


@st.cache_data(show_spinner=False)
def quality() -> dict:
    if not config.QUALITY_JSON.exists():
        return {}
    return json.loads(config.QUALITY_JSON.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def validation() -> pd.DataFrame | None:
    """Blind hand labels (views/labeling.py -> manual_sample.csv); only finished rows."""
    if not config.MANUAL_SAMPLE_CSV.exists():
        return None
    df = pd.read_csv(config.MANUAL_SAMPLE_CSV, dtype={"review_id": "string"}, keep_default_na=False)
    if "done" not in df:
        return None
    return df[df["done"].astype(str).str.lower().eq("true")]


def collected_at() -> pd.Timestamp | None:
    r = ratings()
    if "collected_at" not in r or r["collected_at"].isna().all():
        return None
    return pd.to_datetime(r["collected_at"].dropna().iloc[0], utc=True)


@st.cache_data(show_spinner=False)
def events() -> pd.DataFrame:
    """Dated release/event markers from data/events.csv (rows without a date are skipped)."""
    path = config.DATA_DIR / "events.csv"
    if not path.exists():
        return pd.DataFrame(columns=["date", "event", "version", "source"])
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df = df[df["date"].str.strip() != ""].copy()
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    return df.dropna(subset=["date"]).sort_values("date")
