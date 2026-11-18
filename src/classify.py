"""Stage 3b: label every review with topics, level mentions, churn and monetization signals.

Run:  python -m src.classify
Input:  data/reviews_clean.csv + data/translations.csv (English text)
Output: data/classified.csv  (review_id + label columns; merged in src/data/load.py)

Same free-tier discipline as translate.py: small batches, cache by review_id,
failed batches are skipped and retried on the next run.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from typing import Literal

import pandas as pd
from pydantic import BaseModel

from src import config, llm

TOPICS = ["ads", "difficulty", "boosters", "purchases", "bugs_performance",
          "events", "mechanics", "visuals_audio", "praise"]
MONETIZATION = ["ads", "no_ads_pack", "purchase"]
COLUMNS = ["review_id", "topics", "level_mentions", "churn_signal", "monetization",
           "is_request", "request_text", "model", "classified_at"]

PROMPT = f"""You label mobile-game store reviews for a player-research team.
Game: "Market Match!", a casual item-sorting / matching game with levels, boosters,
ads, in-app purchases and live events (e.g. Weekly Contest, Pool Party).

For EACH review (English text given) return:
- topics: every topic the review actually talks about, from this list only:
  ads = advertising frequency/placement/misleading ads;
  difficulty = difficulty, level design, timers/time limits, being stuck;
  boosters = boosters/power-ups;
  purchases = in-app purchases, prices, paid packs;
  bugs_performance = bugs, crashes, battery, heat, lag;
  events = live events, contests, seasonal modes;
  mechanics = core gameplay mechanics, sorting/matching rules, controls, originality;
  visuals_audio = graphics, art, animation, sound;
  praise = general praise or enjoyment without a more specific topic.
  A short review like "great game" -> ["praise"]. Use [] only if the text has no content.
- level_mentions: level numbers the player explicitly mentions (e.g. "level 47" -> [47]); else [].
- churn_signal: true only if the player says they uninstalled, deleted, quit or will quit.
- monetization: subset of {MONETIZATION}: "ads" if ads are mentioned, "no_ads_pack" if a
  remove-ads / no-ads purchase is mentioned, "purchase" if other spending/prices are mentioned.
- is_request: true if the player asks for a feature or change; request_text: that request in
  a few English words (else "").
Be literal: label only what the text says. Return one object per input review, same review_id."""


class Item(BaseModel):
    review_id: str
    topics: list[Literal[tuple(TOPICS)]]  # type: ignore[valid-type]
    level_mentions: list[int]
    churn_signal: bool
    monetization: list[Literal[tuple(MONETIZATION)]]  # type: ignore[valid-type]
    is_request: bool
    request_text: str


def main() -> None:
    reviews = pd.read_csv(config.CLEAN_CSV, dtype={"review_id": "string"})
    if config.TRANSLATIONS_CSV.exists():
        tr = pd.read_csv(config.TRANSLATIONS_CSV, dtype={"review_id": "string"}, keep_default_na=False)
        reviews = reviews.merge(tr[["review_id", "text_en"]], on="review_id", how="left")
    else:
        reviews["text_en"] = ""
    reviews["text_for_model"] = [en if isinstance(en, str) and en.strip() else t
                                 for en, t in zip(reviews["text_en"], reviews["text"])]

    done = (pd.read_csv(config.CLASSIFIED_CSV, dtype={"review_id": "string"}, keep_default_na=False)
            if config.CLASSIFIED_CSV.exists() else pd.DataFrame(columns=COLUMNS))
    todo = reviews[~reviews["review_id"].isin(done["review_id"])]
    print(f"[CL] {len(reviews)} reviews · {len(done)} cached · {len(todo)} to classify", flush=True)
    if todo.empty:
        return

    cl = llm.client()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows: list[dict] = []
    items = [{"review_id": r.review_id, "rating": int(r.rating), "text": r.text_for_model}
             for r in todo.itertuples()]
    step = config.GEMINI_BATCH
    for i in range(0, len(items), step):
        batch = items[i:i + step]
        try:
            out, model = llm.call_json(cl, PROMPT, batch, list[Item], tag="CL")
        except RuntimeError as exc:
            print(f"[CL] batch {i // step + 1} skipped: {exc}", flush=True)
            continue
        for o in out:
            if o.review_id not in {b["review_id"] for b in batch}:
                continue
            rows.append({
                "review_id": o.review_id,
                "topics": ";".join(dict.fromkeys(o.topics)),
                "level_mentions": ";".join(str(n) for n in dict.fromkeys(o.level_mentions)),
                "churn_signal": o.churn_signal,
                "monetization": ";".join(dict.fromkeys(o.monetization)),
                "is_request": o.is_request,
                "request_text": o.request_text.strip() if o.is_request else "",
                "model": model, "classified_at": now,
            })
        print(f"[CL] batch {i // step + 1}: {len(out)} via {model}", flush=True)
        pd.concat([done, pd.DataFrame(rows, columns=COLUMNS)]).to_csv(
            config.CLASSIFIED_CSV, index=False, encoding="utf-8")
        time.sleep(config.GEMINI_PAUSE_S)

    final = pd.read_csv(config.CLASSIFIED_CSV, dtype={"review_id": "string"}, keep_default_na=False)
    missing = len(reviews) - final["review_id"].nunique()
    print(f"[CL] done: {len(final)} classified · {missing} still missing (re-run to retry)")


if __name__ == "__main__":
    sys.exit(main())
