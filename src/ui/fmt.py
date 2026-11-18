"""Turkish labels and number formatting (4.466 · 4,70 · %7,1)."""
from __future__ import annotations

import math

COUNTRY = {
    "ae": "BAE", "ar": "Arjantin", "at": "Avusturya", "au": "Avustralya", "be": "Belçika",
    "br": "Brezilya", "ca": "Kanada", "ch": "İsviçre", "cl": "Şili", "co": "Kolombiya",
    "cr": "Kosta Rika", "cz": "Çekya", "de": "Almanya", "dk": "Danimarka", "ec": "Ekvador",
    "es": "İspanya", "fi": "Finlandiya", "fr": "Fransa", "gb": "Birleşik Krallık",
    "gr": "Yunanistan", "hk": "Hong Kong", "hu": "Macaristan", "id": "Endonezya",
    "ie": "İrlanda", "il": "İsrail", "in": "Hindistan", "it": "İtalya", "jp": "Japonya",
    "kr": "Güney Kore", "kw": "Kuveyt", "lu": "Lüksemburg", "mo": "Makao", "mt": "Malta",
    "mx": "Meksika", "my": "Malezya", "nl": "Hollanda", "no": "Norveç", "nz": "Yeni Zelanda",
    "pe": "Peru", "ph": "Filipinler", "pl": "Polonya", "pt": "Portekiz", "qa": "Katar",
    "ro": "Romanya", "ru": "Rusya", "sa": "Suudi Arabistan", "se": "İsveç", "sg": "Singapur",
    "sk": "Slovakya", "th": "Tayland", "tr": "Türkiye", "tw": "Tayvan", "ua": "Ukrayna",
    "us": "ABD", "vn": "Vietnam", "za": "Güney Afrika",
}

ISO3 = {
    "ae": "ARE", "ar": "ARG", "at": "AUT", "au": "AUS", "be": "BEL", "br": "BRA", "ca": "CAN",
    "ch": "CHE", "cl": "CHL", "co": "COL", "cr": "CRI", "cz": "CZE", "de": "DEU", "dk": "DNK",
    "ec": "ECU", "es": "ESP", "fi": "FIN", "fr": "FRA", "gb": "GBR", "gr": "GRC", "hk": "HKG",
    "hu": "HUN", "id": "IDN", "ie": "IRL", "il": "ISR", "in": "IND", "it": "ITA", "jp": "JPN",
    "kr": "KOR", "kw": "KWT", "lu": "LUX", "mo": "MAC", "mt": "MLT", "mx": "MEX", "my": "MYS",
    "nl": "NLD", "no": "NOR", "nz": "NZL", "pe": "PER", "ph": "PHL", "pl": "POL", "pt": "PRT",
    "qa": "QAT", "ro": "ROU", "ru": "RUS", "sa": "SAU", "se": "SWE", "sg": "SGP", "sk": "SVK",
    "th": "THA", "tr": "TUR", "tw": "TWN", "ua": "UKR", "us": "USA", "vn": "VNM", "za": "ZAF",
}

LANG = {
    "en": "İngilizce", "tr": "Türkçe", "pt": "Portekizce", "de": "Almanca", "es": "İspanyolca",
    "fr": "Fransızca", "it": "İtalyanca", "nl": "Felemenkçe", "ja": "Japonca", "ko": "Korece",
}

# Ablative case for "translated from …" labels.
LANG_FROM = {
    "tr": "Türkçeden", "pt": "Portekizceden", "de": "Almancadan", "es": "İspanyolcadan",
    "fr": "Fransızcadan", "it": "İtalyancadan", "nl": "Felemenkçeden", "ja": "Japoncadan",
    "ko": "Koreceden", "ru": "Rusçadan", "pl": "Lehçeden", "ar": "Arapçadan", "zh": "Çinceden",
    "sv": "İsveççeden", "da": "Danimarkacadan", "id": "Endonezcadan", "th": "Taycadan",
    "tl": "Tagalogcadan",
}
LANG.update({"ru": "Rusça", "pl": "Lehçe", "ar": "Arapça", "zh": "Çince", "sv": "İsveççe",
             "da": "Danimarkaca", "id": "Endonezce", "th": "Tayca", "tl": "Tagalogca", "und": "Belirsiz"})


def lang_from(code: str | None) -> str:
    return LANG_FROM.get(code or "", f"{(code or '?').upper()} dilinden")


STORE = {"app_store": "App Store", "google_play": "Google Play"}

TOPIC = {
    "ads": "Reklamlar", "difficulty": "Zorluk & seviye tasarımı", "boosters": "Boosterlar",
    "purchases": "Satın alma & fiyat", "bugs_performance": "Hata & performans",
    "events": "Etkinlikler", "mechanics": "Oyun mekaniği", "visuals_audio": "Görsel & ses",
    "praise": "Genel övgü",
}
MONETIZATION = {"ads": "Reklam", "no_ads_pack": "Reklamsız paket", "purchase": "Satın alma"}


def topic(code: str) -> str:
    return TOPIC.get(code, code)

BUCKET = {"negative": "Olumsuz (1–2★)", "neutral": "Nötr (3★)", "positive": "Olumlu (4–5★)"}
BUCKET_STARS = {"negative": "1–2★", "neutral": "3★", "positive": "4–5★"}

# Plain-language trust levels shown instead of statistical jargon.
TRUST = {
    "strong": ("hi", "Güvenilir"),
    "directional": ("mid", "Fikir verir"),
    "anecdotal": ("lo", "Az veri"),
}

MONTHS = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
MONTHS_LONG = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
               "Eylül", "Ekim", "Kasım", "Aralık"]


def _nan(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def country(code: str | None) -> str:
    if _nan(code) or not code:
        return "—"
    return COUNTRY.get(code, code.upper())


def lang(code: str | None) -> str:
    return LANG.get(code or "", (code or "—").upper())


def num(x, decimals: int = 0) -> str:
    """4466 -> '4.466' · 4.712 -> '4,71'."""
    if _nan(x):
        return "—"
    s = f"{x:,.{decimals}f}"
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def pct(x, decimals: int = 1) -> str:
    if _nan(x):
        return "—"
    return f"%{num(x * 100, decimals)}"


def month_label(ym: str) -> str:
    y, m = ym.split("-")
    return f"{MONTHS[int(m) - 1]} {y[2:]}"


def date_long(ts) -> str:
    return f"{ts.day} {MONTHS_LONG[ts.month - 1]} {ts.year}"


def stars(r: int) -> str:
    r = int(r)
    return "★" * r + "☆" * (5 - r)
