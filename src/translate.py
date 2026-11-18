"""Stage 3a: detect each review's real language and translate non-English reviews to English.

Run:  python -m src.translate
Input:  data/reviews_clean.csv
Output: data/translations.csv  (review_id, source_lang, text_en, model, translated_at, reviewed)

Free tier only: a handful of batched requests, pauses between them, gentle backoff on
429s, no grounding, no paid models. Reviews already in translations.csv are never
sent again, so re-running costs nothing and only new reviews are translated.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

from src import config

load_dotenv(config.ROOT / ".env")

# reviewed = read against the original by a human; edited = translation was corrected by hand.
COLUMNS = ["review_id", "source_lang", "text_en", "model", "translated_at", "reviewed", "edited"]

PROMPT = """You translate mobile-game store reviews for a player-research team.
The game is "Market Match!", a casual matching game.

For EACH review in the input JSON list:
1. Detect the language the review text is actually written in (ISO 639-1 code, e.g. "de").
   Ignore the store country; only the text matters. Emoji-only or numeric text -> "und".
2. If the language is English (or "und"), return text_en as an empty string.
3. Otherwise translate it into natural English that preserves the player's meaning, tone,
   intensity, slang, sarcasm, typos-as-intent and emojis exactly.
   - Keep game terms players use as-is when they are English loanwords (level, ads, booster).
   - Do NOT summarise, soften, correct, explain or add anything.
   - Keep line breaks and punctuation style.

Return one object per input review, same review_id, same order."""


class Item(BaseModel):
    review_id: str
    source_lang: str
    text_en: str


def _client() -> genai.Client:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY is missing in .env")
    # Hard timeout so a stuck request can never hang the run.
    return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=120_000))


def _call(client: genai.Client, model: str, batch: list[dict]) -> list[Item]:
    resp = client.models.generate_content(
        model=model,
        contents=[PROMPT, json.dumps(batch, ensure_ascii=False)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=list[Item],
            temperature=0.2,
        ),
    )
    return list(resp.parsed or [])


def translate_batch(client: genai.Client, batch: list[dict]) -> tuple[list[Item], str]:
    """Primary model with gentle backoff; falls back to Flash-Lite if the primary is
    unavailable on the free tier. Never more than a few attempts."""
    for model in (config.GEMINI_MODEL, config.GEMINI_FALLBACK_MODEL):
        for attempt in range(4):
            try:
                return _call(client, model, batch), model
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                rate = "429" in msg or "RESOURCE_EXHAUSTED" in msg
                busy = "503" in msg or "UNAVAILABLE" in msg or "timed out" in msg.lower()
                print(f"[TR] {model} attempt {attempt + 1} failed: {msg[:160]}", flush=True)
                if busy and attempt == 3:
                    break  # still overloaded -> fallback model
                if "404" in msg or "NOT_FOUND" in msg or "PERMISSION_DENIED" in msg or (
                        rate and "limit: 0" in msg):
                    break  # model not available to this free-tier key -> try fallback
                time.sleep(15 * (attempt + 1) if (rate or busy) else 3)
    raise RuntimeError("Translation failed on both models; nothing was written for this batch.")


def main() -> None:
    reviews = pd.read_csv(config.CLEAN_CSV, dtype={"review_id": "string"})
    if config.TRANSLATIONS_CSV.exists():
        done = pd.read_csv(config.TRANSLATIONS_CSV, dtype={"review_id": "string"})
    else:
        done = pd.DataFrame(columns=COLUMNS)
    todo = reviews[~reviews["review_id"].isin(done["review_id"])]
    print(f"[TR] {len(reviews)} reviews · {len(done)} cached · {len(todo)} to translate", flush=True)
    if todo.empty:
        return

    client = _client()
    rows: list[dict] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    items = [{"review_id": r.review_id, "text": r.text} for r in todo.itertuples()]
    for i in range(0, len(items), config.GEMINI_BATCH):
        batch = items[i:i + config.GEMINI_BATCH]
        try:
            out, model = translate_batch(client, batch)
        except RuntimeError as exc:
            # Skip this batch; it stays uncached and is retried on the next run.
            print(f"[TR] batch {i // config.GEMINI_BATCH + 1} skipped: {exc}", flush=True)
            continue
        got = {o.review_id: o for o in out}
        missing = [b["review_id"] for b in batch if b["review_id"] not in got]
        if missing:
            print(f"[TR] model skipped {len(missing)} reviews; they stay untranslated for the next run")
        for b in batch:
            o = got.get(b["review_id"])
            if o is None:
                continue
            rows.append({"review_id": o.review_id, "source_lang": o.source_lang.lower().strip(),
                         "text_en": o.text_en.strip(), "model": model,
                         "translated_at": now, "reviewed": False, "edited": False})
        print(f"[TR] batch {i // config.GEMINI_BATCH + 1}: {len(out)} returned via {model}", flush=True)
        # Save after every batch so a later failure never loses finished work.
        pd.concat([done, pd.DataFrame(rows, columns=COLUMNS)]).to_csv(
            config.TRANSLATIONS_CSV, index=False, encoding="utf-8")
        if i + config.GEMINI_BATCH < len(items):
            time.sleep(config.GEMINI_PAUSE_S)

    final = pd.read_csv(config.TRANSLATIONS_CSV, dtype={"review_id": "string"})
    translated = final[final["text_en"].fillna("").str.strip() != ""]
    print(f"[TR] done: {len(final)} rows · {len(translated)} translated · "
          f"languages {final['source_lang'].value_counts().to_dict()}")


if __name__ == "__main__":
    sys.exit(main())
