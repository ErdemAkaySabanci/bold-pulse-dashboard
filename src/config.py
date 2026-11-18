"""Central configuration for the Market Match! review analysis pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

RAW_CSV = DATA_DIR / "reviews_raw.csv"
CLEAN_CSV = DATA_DIR / "reviews_clean.csv"
QUALITY_JSON = DATA_DIR / "quality_report.json"
CLASSIFIED_CSV = DATA_DIR / "classified.csv"
MANUAL_SAMPLE_CSV = DATA_DIR / "manual_sample.csv"
TRANSLATIONS_CSV = DATA_DIR / "translations.csv"

# Gemini free tier only (billing disabled on the project). No grounding, no paid models.
# 2.5 models return 404 for new users; 3.8 Flash was overloaded (503) on 2026-11-18,
# so Flash-Lite is primary and 3.8 Flash the fallback. Both are free-tier models.
GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_FALLBACK_MODEL = "gemini-3.8-flash"
GEMINI_BATCH = 5             # reviews per request (small = fewer 503s)
GEMINI_PAUSE_S = 6           # pause between requests (free-tier rate limits)

APP_NAME = "Market Match"
DEVELOPER = "Bold Games"
# Google Play lists the legal entity name ("Bold Oyun Yazilim ve Pazarlama A.S."),
# which matches the App Store seller name, so both aliases count as verified.
DEVELOPER_ALIASES = ["bold games", "bold oyun"]
APP_STORE_ID = "6754193919"
APP_STORE_OFFICIAL_RATING = 4.8

# Google Play search sometimes returns the top hit with appId=None, so the
# package (verified: developer "Bold Oyun Yazilim ve Pazarlama A.S.") is pinned.
GP_PACKAGE_OVERRIDE: str | None = "com.boldgames.marketmatch"

# Google Play returns reviews per *language*, not per country: the same language
# gives identical reviews in every country (verified for en/es/pt/fr), and the
# reviewer's country is not exposed. So we iterate every Play language once with
# a fixed country. Probed 2026-11-18: only en, de, es, fr, it, nl, pt, tr had reviews.
GP_REVIEW_COUNTRY = "us"
GP_REVIEW_LANGS = (
    "af am ar az be bg bn bs ca cs da de el en es et eu fa fi fil fr gl gu hi hr hu "
    "hy id is it iw ja ka kk km kn ko ky lo lt lv mk ml mn mr ms my ne nl no pa pl pt "
    "ro ru si sk sl sq sr sv sw ta te th tr uk ur uz vi zh-CN zh-TW zh-HK zu"
).split()

# Store country codes scanned for per-country ratings (both stores). Codes a
# store does not serve simply come back empty.
STOREFRONTS = (
    "ae ag ai al am ao ar at au az ba bb bd be bf bg bh bj bm bn bo br bs bt bw by "
    "bz ca cd cg ch ci cl cm cn co cr cv cy cz de dk dm do dz ec ee eg es fi fj fm "
    "fr ga gb gd ge gh gm gr gt gw gy hk hn hr hu id ie il in iq is it jm jo jp ke "
    "kg kh kn kr kw ky kz la lb lc lk lr lt lu lv ly ma md me mg mk ml mm mn mo mr "
    "ms mt mu mv mw mx my mz na ne ng ni nl no np nr nz om pa pe pg ph pk pl pt pw "
    "py qa ro rs ru rw sa sb sc se sg si sk sl sn sr st sv sz tc td th tj tm tn to "
    "tr tt tw tz ua ug us uy uz vc ve vg vn vu xk ye za zm zw"
).split()

# App Store reviews are fetched from every storefront that has >= 1 rating in the
# ratings scan. This maps those countries to a review language; others default to "en".
APP_STORE_LANG = {
    "de": "de", "at": "de", "ch": "de", "fr": "fr", "be": "fr", "lu": "fr",
    "es": "es", "mx": "es", "ar": "es", "co": "es", "cl": "es", "pe": "es",
    "cr": "es", "ec": "es", "br": "pt", "pt": "pt", "it": "it", "nl": "nl",
    "jp": "ja", "kr": "ko", "tw": "zh", "hk": "zh", "mo": "zh", "th": "th",
    "tr": "tr", "ru": "ru", "ua": "uk", "pl": "pl", "cz": "cs", "sk": "sk",
    "hu": "hu", "ro": "ro", "gr": "el", "se": "sv", "dk": "da", "no": "no",
    "fi": "fi", "il": "he", "sa": "ar", "ae": "ar", "kw": "ar", "qa": "ar",
    "id": "id", "my": "ms", "vn": "vi",
}
APP_STORE_MAX_PAGES = 10

# Optional: SerpAPI Apple Reviews (engine=apple_reviews). Runs only when
# SERPAPI_API_KEY is set in .env. Each page = 1 search credit, so pages are capped.
SERPAPI_COUNTRIES = ["us", "gb", "tr", "de", "fr", "au"]
SERPAPI_MAX_PAGES = 15

RATINGS_CSV = DATA_DIR / "ratings_by_country.csv"
RATINGS_COLUMNS = [
    "store", "country", "rating_count", "avg_rating",
    "share_1", "share_2", "share_3", "share_4", "share_5",
    "scope", "collected_at",
]

COLUMNS = [
    "review_id", "store", "source", "country", "lang", "rating", "text", "title",
    "date", "app_version", "thumbs_up", "developer_reply", "reply_date",
]

# What the store pages displayed on 2026-11-18 (App Store US product page; Google Play
# Games PC client, which shows the global value). Used only to cross-check our numbers.
OFFICIAL_DISPLAY = {
    "app_store_us": {"label": "App Store (ABD sayfası)", "avg": 4.8, "count": 1900, "count_text": "1,9 B"},
    "google_play": {"label": "Google Play (dünya geneli)", "avg": 4.7, "count": 1300, "count_text": "1,3 B"},
}
