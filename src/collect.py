"""Stage 1: collect Market Match! store reviews from Google Play and the App Store.

Run:  python -m src.collect
Output: data/reviews_raw.csv
"""
from __future__ import annotations

import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone

import pandas as pd
import requests
from dotenv import load_dotenv
from google_play_scraper import Sort, reviews, search
from google_play_scraper import app as gp_app

from src import config

load_dotenv(config.ROOT / ".env")

UA = {"User-Agent": "Mozilla/5.0 (review-analysis portfolio project)"}


# --------------------------------------------------------------------------- #
# Google Play
# --------------------------------------------------------------------------- #
def find_gp_package() -> str | None:
    """Locate the Market Match! package on Google Play and verify the developer."""
    if config.GP_PACKAGE_OVERRIDE:
        print(f"[GP] Using override package: {config.GP_PACKAGE_OVERRIDE}")
        return config.GP_PACKAGE_OVERRIDE

    queries = ["Market Match!", "Market Match", "Bold Games", "market match bold"]
    seen: dict[str, dict] = {}
    for q in queries:
        try:
            hits = search(q, lang="en", country="us", n_hits=30)
        except Exception as exc:  # noqa: BLE001
            print(f"[GP] search('{q}') failed: {exc}")
            continue
        for h in hits:
            if h.get("appId"):
                seen.setdefault(h["appId"], h)
        time.sleep(0.5)

    for app_id, h in seen.items():
        dev = (h.get("developer") or "").lower()
        title = (h.get("title") or "").lower()
        if any(a in dev for a in config.DEVELOPER_ALIASES) and "market match" in title:
            print(
                f"[GP] Matched package: {app_id} | title={h.get('title')!r} | "
                f"developer={h.get('developer')!r} | score={h.get('score')} | "
                f"installs={h.get('installs')}"
            )
            return app_id

    print("[GP] No Bold Games 'Market Match' hit found. Top results seen:")
    for app_id, h in list(seen.items())[:15]:
        print(f"      {app_id:50s} {h.get('title')!r:40s} by {h.get('developer')!r}")
    return None


def fetch_gp_reviews(package: str) -> list[dict]:
    """Fetch reviews for every Play language. Play does not expose the reviewer's
    country, so `country` is left empty for Google Play rows."""
    rows: list[dict] = []
    seen: set[str] = set()
    country = config.GP_REVIEW_COUNTRY
    per_lang: dict[str, int] = {}
    for lang in config.GP_REVIEW_LANGS:
        token = None
        n_locale = 0
        while True:
            batch = None
            for attempt in range(3):
                try:
                    batch, token = reviews(
                        package, lang=lang, country=country,
                        sort=Sort.NEWEST, count=200, continuation_token=token,
                    )
                    break
                except Exception as exc:  # noqa: BLE001
                    wait = 2 ** attempt
                    print(f"[GP] {lang} error ({exc}); retry in {wait}s")
                    time.sleep(wait)
            if not batch:
                break
            for r in batch:
                if r.get("reviewId") in seen:
                    continue
                seen.add(r.get("reviewId"))
                n_locale += 1
                rows.append({
                    "review_id": r.get("reviewId"),
                    "store": "google_play",
                    "source": "gp_scraper",
                    "country": None,
                    "lang": lang,
                    "rating": r.get("score"),
                    "text": r.get("content"),
                    "title": None,
                    "date": r.get("at"),
                    "app_version": r.get("reviewCreatedVersion"),
                    "thumbs_up": r.get("thumbsUpCount"),
                    "developer_reply": r.get("replyContent"),
                    "reply_date": r.get("repliedAt"),
                })
            if token is None or getattr(token, "token", None) is None:
                break
            time.sleep(0.5)
        if n_locale:
            per_lang[lang] = n_locale
        time.sleep(0.3)
    print(f"[GP] {len(config.GP_REVIEW_LANGS)} languages scanned; "
          f"reviews per language: {per_lang} (total {len(rows)})")
    return rows


# --------------------------------------------------------------------------- #
# App Store (public RSS JSON feed)
# --------------------------------------------------------------------------- #
def _label(entry: dict, key: str):
    val = entry.get(key)
    return val.get("label") if isinstance(val, dict) else None


def _rss_urls(cc: str):
    """Yield (group, url) RSS variants. The feed is inconsistent: for some
    countries the documented page=N/sortby=mostrecent form returns nothing while
    the un-paged form returns reviews, so we take the union and dedupe by id."""
    base = f"https://itunes.apple.com/{cc}/rss/customerreviews"
    aid = config.APP_STORE_ID
    yield "unpaged", f"{base}/id={aid}/sortby=mostrecent/json"
    for sort in ("mostrecent", "mosthelpful"):
        for page in range(1, config.APP_STORE_MAX_PAGES + 1):
            yield sort, f"{base}/page={page}/id={aid}/sortby={sort}/json"


def fetch_app_store_reviews(countries: list[str]) -> list[dict]:
    """Collect App Store reviews from RSS. Once a page in a sort order returns no
    reviews, the remaining pages of that sort are skipped, which keeps the
    request count low and avoids Apple's 429 rate limit."""
    rows: list[dict] = []
    per_country: dict[str, int] = {}
    for cc in countries:
        lang = config.APP_STORE_LANG.get(cc, "en")
        seen_ids: set[str] = set()
        exhausted: set[str] = set()
        for group, url in _rss_urls(cc):
            if group in exhausted:
                continue
            data = None
            for attempt in range(3):
                try:
                    resp = requests.get(url, headers=UA, timeout=20)
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except Exception as exc:  # noqa: BLE001
                    wait = 2 ** attempt
                    print(f"[AS] {cc} error ({exc}); retry in {wait}s")
                    time.sleep(wait)
            if data is None:
                exhausted.add(group)
                continue

            entries = data.get("feed", {}).get("entry", [])
            if isinstance(entries, dict):
                entries = [entries]
            entries = [e for e in entries if "im:rating" in e]
            time.sleep(1.0)
            if not entries:
                exhausted.add(group)
                continue
            entries = [e for e in entries if _label(e, "id") not in seen_ids]
            if not entries:
                continue

            for e in entries:
                seen_ids.add(_label(e, "id"))
                title = _label(e, "title") or ""
                content = _label(e, "content") or ""
                text = f"{title}. {content}".strip(". ").strip() if title else content
                rows.append({
                    "review_id": _label(e, "id"),
                    "store": "app_store",
                    "source": "rss",
                    "country": cc,
                    "lang": lang,
                    "rating": _label(e, "im:rating"),
                    "text": text,
                    "title": title,
                    "date": _label(e, "updated"),
                    "app_version": _label(e, "im:version"),
                    "thumbs_up": _label(e, "im:voteCount"),
                    "developer_reply": None,
                    "reply_date": None,
                })
        if seen_ids:
            per_country[cc] = len(seen_ids)
    print(f"[AS] {len(countries)} storefronts scanned; "
          f"reviews per country: {per_country} (total {len(rows)})")
    return rows


def fetch_serpapi_reviews(known_ids: set[str]) -> list[dict]:
    """Optional App Store source via SerpAPI (engine=apple_reviews)."""
    key = os.getenv("SERPAPI_API_KEY")
    if not key:
        print("[SERP] SERPAPI_API_KEY not set; skipping.")
        return []
    rows: list[dict] = []
    credits = 0
    for cc in config.SERPAPI_COUNTRIES:
        lang = config.APP_STORE_LANG.get(cc, "en")
        n_new = n_seen = 0
        for page in range(1, config.SERPAPI_MAX_PAGES + 1):
            params = {
                "engine": "apple_reviews", "product_id": config.APP_STORE_ID,
                "country": cc, "sort": "mostrecent", "page": page, "api_key": key,
            }
            try:
                resp = requests.get("https://serpapi.com/search.json",
                                    params=params, timeout=60)
                credits += 1
                data = resp.json()
            except Exception as exc:  # noqa: BLE001
                print(f"[SERP] {cc} p{page} error: {exc}")
                break
            if "error" in data:
                print(f"[SERP] {cc} p{page}: {data['error']}")
                break
            batch = data.get("reviews") or []
            if not batch:
                break
            for r in batch:
                rid = str(r.get("id") or "")
                n_seen += 1
                if not rid or rid in known_ids:
                    continue
                known_ids.add(rid)
                n_new += 1
                title = r.get("title") or ""
                body = r.get("text") or ""
                helpful = r.get("helpfulness_vote_information") or {}
                rows.append({
                    "review_id": rid,
                    "store": "app_store",
                    "source": "serpapi",
                    "country": cc,
                    "lang": lang,
                    "rating": r.get("rating"),
                    "text": f"{title}. {body}" if title else body,
                    "title": title,
                    "date": r.get("review_date"),
                    "app_version": r.get("reviewed_version"),
                    "thumbs_up": helpful.get("helpful_count") if isinstance(helpful, dict) else None,
                    "developer_reply": (r.get("developer_response") or {}).get("text")
                    if isinstance(r.get("developer_response"), dict) else None,
                    "reply_date": (r.get("developer_response") or {}).get("date")
                    if isinstance(r.get("developer_response"), dict) else None,
                })
            if not (data.get("serpapi_pagination") or {}).get("next"):
                break
        print(f"[SERP] {cc}: {n_seen} returned, {n_new} new (not in RSS)")
    print(f"[SERP] search credits used: {credits}")
    return rows


# --------------------------------------------------------------------------- #
# Per-country ratings (star ratings, with or without review text)
# --------------------------------------------------------------------------- #
def fetch_app_store_ratings(collected_at: str) -> list[dict]:
    """Real per-storefront rating count and average from the iTunes Lookup API.
    Storefronts where the app is not sold are omitted."""
    rows: list[dict] = []
    for cc in config.STOREFRONTS:
        results = None
        for attempt in range(3):
            try:
                resp = requests.get(
                    "https://itunes.apple.com/lookup",
                    params={"id": config.APP_STORE_ID, "country": cc},
                    headers=UA, timeout=15,
                )
                if resp.status_code == 429:
                    time.sleep(3 * (attempt + 1))
                    continue
                results = resp.json().get("results", [])
                break
            except Exception as exc:  # noqa: BLE001
                print(f"[AS-R] {cc} error ({exc}); retrying")
                time.sleep(2 ** attempt)
        time.sleep(0.3)
        if not results:
            continue
        n = results[0].get("userRatingCount") or 0
        rows.append({
            "store": "app_store", "country": cc, "rating_count": n,
            "avg_rating": results[0].get("averageUserRating") if n else None,
            "scope": "local" if n else "none", "collected_at": collected_at,
        })
    rated = sum(1 for r in rows if r["rating_count"])
    print(f"[AS-R] app sold in {len(rows)} storefronts, {rated} with ratings, "
          f"{sum(r['rating_count'] for r in rows)} ratings in total")
    return rows


def fetch_gp_ratings(package: str, collected_at: str) -> list[dict]:
    """Per-country Google Play rating. Play only exposes the *global* rating count;
    its per-country histogram is the local star mix scaled to that global count,
    so we store it as shares (local mix) and leave rating_count empty.
    Countries without enough local ratings show the global average/histogram;
    those are flagged scope="global_fallback". One extra row (country="global")
    holds the global count and mix."""
    raw: list[tuple[str, dict]] = []
    for cc in config.STOREFRONTS:
        # Play intermittently serves a page without rating data (seen for tr/zw
        # on 2026-11-18), so an empty score is retried like an error.
        last: dict | None = None
        for attempt in range(3):
            try:
                last = gp_app(package, lang="en", country=cc)
                if last.get("score") is not None:
                    break
            except Exception as exc:  # noqa: BLE001
                if attempt == 2:
                    print(f"[GP-R] {cc} failed ({type(exc).__name__})")
            time.sleep(2 ** attempt)
        if last is not None:
            raw.append((cc, last))
        time.sleep(0.3)

    def key(d: dict) -> tuple:
        return (d.get("score"), tuple(d.get("histogram") or []))

    with_score = [(cc, d) for cc, d in raw if d.get("score") is not None]
    if not with_score:
        print("[GP-R] no country returned a score")
        return []
    # The global fallback is the score/histogram shared by most countries.
    global_key = Counter(key(d) for _, d in with_score).most_common(1)[0][0]

    def row(cc: str, d: dict | None, scope: str, count=None) -> dict:
        hist = (d or {}).get("histogram") or []
        total = sum(h or 0 for h in hist)
        shares = ({f"share_{i + 1}": round((h or 0) / total, 4) for i, h in enumerate(hist)}
                  if total else {})
        return {"store": "google_play", "country": cc, "rating_count": count,
                "avg_rating": (d or {}).get("score"), **shares,
                "scope": scope, "collected_at": collected_at}

    g = next(d for _, d in with_score if key(d) == global_key)
    rows = [row("global", g, "global", count=g.get("ratings"))]
    for cc, d in raw:
        if d.get("score") is None:
            rows.append(row(cc, None, "none"))
        elif key(d) == global_key:
            rows.append(row(cc, None, "global_fallback"))
        else:
            rows.append(row(cc, d, "local"))
    n_local = sum(1 for r in rows if r["scope"] == "local")
    print(f"[GP-R] {len(raw)} countries queried: {n_local} with a local score, "
          f"global = {g.get('score'):.3f} from {g.get('ratings')} ratings")
    return rows


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    config.DATA_DIR.mkdir(exist_ok=True)
    collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    gp_rows: list[dict] = []
    gp_ratings: list[dict] = []
    package = find_gp_package()
    if package:
        gp_rows = fetch_gp_reviews(package)
        gp_ratings = fetch_gp_ratings(package, collected_at)
    else:
        print("[GP] Skipping Google Play; continuing with App Store only.")

    as_ratings = fetch_app_store_ratings(collected_at)
    ratings = pd.DataFrame(gp_ratings + as_ratings, columns=config.RATINGS_COLUMNS)
    ratings.to_csv(config.RATINGS_CSV, index=False, encoding="utf-8")

    # Only storefronts with at least one rating can have written reviews.
    rated_countries = [r["country"] for r in as_ratings if r["rating_count"]]
    as_rows = fetch_app_store_reviews(rated_countries)
    serp_rows = fetch_serpapi_reviews({r["review_id"] for r in as_rows})

    df = pd.DataFrame(gp_rows + as_rows + serp_rows, columns=config.COLUMNS)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").astype("Int64")
    df["thumbs_up"] = pd.to_numeric(df["thumbs_up"], errors="coerce").astype("Int64")
    df.to_csv(config.RAW_CSV, index=False, encoding="utf-8")

    print("\n================ STAGE 1 SUMMARY ================")
    print(f"Total rows: {len(df)}  ->  {config.RAW_CSV.relative_to(config.ROOT)}")
    if df.empty:
        print("No reviews collected.")
        return
    print("\nRows per store:")
    print(df["store"].value_counts().to_string())
    print("\nRows per store x lang (Google Play has no reviewer country):")
    print(df.groupby(["store", "lang"]).size().unstack(fill_value=0).to_string())
    print("\nApp Store rows per country:")
    print(df[df["store"] == "app_store"]["country"].value_counts().to_dict())
    dates = pd.to_datetime(df["date"], errors="coerce", utc=True, format="mixed")
    print("\nDate range per store:")
    rng = dates.groupby(df["store"]).agg(["min", "max"])
    print(rng.to_string())
    print(f"\nUnique review_ids: {df['review_id'].nunique()}")

    print(f"\nRatings: {len(ratings)} rows -> "
          f"{config.RATINGS_CSV.relative_to(config.ROOT)}")
    print(ratings.groupby(["store", "scope"]).size().to_string())


if __name__ == "__main__":
    sys.exit(main())
