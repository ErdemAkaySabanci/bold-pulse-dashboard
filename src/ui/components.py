"""Reusable presentational components. Review text is user content: always escaped."""
from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from src.i18n import T
from src.metrics import confidence_tier
from src.ui import fmt
from src.ui.theme import tok


ASSETS = Path(__file__).resolve().parents[2] / "assets"


def _md(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)


@lru_cache(maxsize=8)
def _data_uri(name: str) -> str:
    mime = "image/svg+xml" if name.endswith(".svg") else "image/png"
    return f"data:{mime};base64," + base64.b64encode((ASSETS / name).read_bytes()).decode()


STORE_LOGO = {"app_store": "app-store.svg", "google_play": "google-play.svg"}


def store_logo(store: str, size: int = 16, cls: str = "") -> str:
    """Inline <img> of the store's logo (used only to identify the store)."""
    return (f'<img class="p-store-logo {cls}" src="{_data_uri(STORE_LOGO[store])}" '
            f'width="{size}" height="{size}" alt="{fmt.STORE[store]}">')


def hero(eyebrow: str, title: str, lede_html: str, stats: list[tuple[str, str]] | None = None) -> None:
    stats_html = ""
    if stats:
        stats_html = '<div class="p-hero-stats">' + "".join(
            f'<div class="p-hero-stat"><div class="v">{escape(v)}</div><div class="l">{escape(l)}</div></div>'
            for v, l in stats) + "</div>"
    logo = f'<img class="logo" src="{_data_uri("bold-wordmark-white.png")}" alt="Bold Games">'
    _md(f'<div class="p-hero">{logo}<span class="p-eyebrow">{escape(eyebrow)}</span>'
        f'<h1>{escape(title)}</h1><p>{lede_html}</p>{stats_html}</div>')


def _src_html(text: str, label: str | None = None) -> str:
    label = label or T("Veri", "Data")
    return f'<div class="p-src"><b>{escape(label)}</b><span>{text}</span></div>'


def section(title: str, sub: str | None = None, icon: str = "●", color: str | None = None,
            source: str | None = None, source_label: str | None = None) -> None:
    """`source` names the data behind the section (store, scope, counts) in one short line."""
    c = tok()["brand"]  # section chips always wear the Bold red; `color` kept for call sites
    sub_html = f"<p>{sub}</p>" if sub else ""
    src_html = _src_html(source, source_label) if source else ""
    _md(f'<div class="p-section"><div class="ico" style="background:{c}">{icon}</div>'
        f'<div><h3>{escape(title)}</h3>{sub_html}{src_html}</div></div>')


def data_source(text: str, label: str | None = None) -> None:
    """Stand-alone 'Veri' line for pages without a section header above their content."""
    _md(_src_html(text, label))


def reviews_source(reviews: pd.DataFrame, extra: str = "") -> str:
    """'112 yazılı yorum · App Store 25 + Google Play 87 · date range' (+ optional extra)."""
    n_as = int((reviews["store"] == "app_store").sum())
    n_gp = int((reviews["store"] == "google_play").sum())
    txt = (f"{fmt.num(len(reviews))} {T('yazılı yorum', 'written reviews')} · App Store {fmt.num(n_as)} + "
           f"Google Play {fmt.num(n_gp)} · "
           f"{fmt.date_long(reviews['date'].min())} – {fmt.date_long(reviews['date'].max())}")
    return txt + (f" · {extra}" if extra else "")


def app_store_source(countries: pd.DataFrame) -> str:
    return T(f"Yalnızca App Store · {fmt.num(len(countries))} ülke · "
             f"{fmt.num(int(countries['n'].sum()))} değerlendirme (yıldız puanı)",
             f"App Store only · {fmt.num(len(countries))} countries · "
             f"{fmt.num(int(countries['n'].sum()))} ratings (stars)")


def trust(tier: str | None, detail: str | None = None) -> str:
    cls, name = fmt.TRUST[tier or "anecdotal"]
    text = f"{name} · {detail}" if detail else name
    return f'<span class="p-trust {cls}">{escape(text)}</span>'


def trust_n(n: int | None, unit: str | None = None) -> str:
    unit = unit or T("veri", "data points")
    if n is None:
        return trust("directional", T("sayı yayınlanmıyor", "count not published"))
    return trust(confidence_tier(n), f"{fmt.num(n)} {unit}")


def kpi(label: str, value: str, ctx_html: str, icon: str, color: str, badge: str = "",
        delay: float = 0, icon_html: str | None = None) -> None:
    """`icon_html` (e.g. a store logo) replaces the coloured icon chip when given."""
    chip = (f'<div class="chip logo">{icon_html}</div>' if icon_html
            else f'<div class="chip" style="background:{color}">{icon}</div>')
    _md(f'<div class="p-card p-kpi" style="animation-delay:{delay}s">{chip}'
        f'<div class="label">{escape(label)}</div><div class="value">{escape(value)}</div>'
        f'<div class="ctx">{ctx_html}</div>{badge}'
        f'<div class="bar" style="background:{color}"></div></div>')


def store_legend() -> None:
    """Legend for App Store vs Google Play charts: logo + the marker each store uses."""
    _md('<div class="p-logo-legend">'
        f'<span class="item">{store_logo("app_store", 22)}<b>App Store</b>'
        f'<span class="mark dot"></span><span class="sub">{T("daire · ülke ortalaması, kaç değerlendirmeye dayandığı biliniyor", "circle · country average, rating count known")}</span></span>'
        f'<span class="item">{store_logo("google_play", 22)}<b>Google Play</b>'
        f'<span class="mark diamond"></span><span class="sub">{T("elmas · ülke ortalaması, kaç değerlendirmeye dayandığı bilinmiyor", "diamond · country average, rating count unknown")}</span></span></div>')


def finding(n: int, title: str, body_html: str, color: str, badge: str = "", delay: float = 0) -> None:
    _md(f'<div class="p-card p-find" style="--c:{color};animation-delay:{delay}s">'
        f'<div class="n">{T("BULGU", "FINDING")} {n}</div><div class="t">{escape(title)}</div>'
        f'<div class="b">{body_html}</div>{badge}</div>')


def sentiment_color(rating: int) -> str:
    t = tok()
    return t["neg"] if rating <= 2 else t["neu"] if rating == 3 else t["pos"]


def quote(row: pd.Series) -> None:
    c = sentiment_color(int(row["rating"]))
    text = escape(str(row["text"]))
    src = row.get("source_lang") or row.get("lang")
    en = row.get("text_en")
    tr_html = ""
    if isinstance(en, str) and en.strip() and src not in ("en", "und"):
        tr_html = (f'<div class="en"><div class="en-h">🇬🇧 {T("İngilizce çeviri", "English translation")} · {escape(fmt.lang_from(src))}'
                   f'</div><div class="en-t">{escape(en)}</div></div>')
    pills = [f'<span class="p-pill date">📅 {fmt.date_long(row["date"])}</span>',
             f'<span class="p-pill stars" style="--c:{c}">{int(row["rating"])} ★</span>',
             f'<span class="p-pill">{store_logo(row["store"], 13)} {fmt.STORE[row["store"]]}</span>']
    if row["store"] == "app_store":
        pills.append(f'<span class="p-pill">{escape(fmt.country(row.get("country")))}</span>')
    pills.append(f'<span class="p-pill">{escape(fmt.lang(src))}</span>')
    version = row.get("app_version")
    if version is not None and not pd.isna(version) and str(version).strip():
        pills.append(f'<span class="p-pill">v{escape(str(version))}</span>')
    if int(row.get("thumbs_up", 0) or 0) > 0:
        pills.append(f'<span class="p-pill">👍 {int(row["thumbs_up"])}</span>')
    _md(f'<div class="p-card p-quote" style="--c:{c}"><div class="q">“{text}”</div>{tr_html}'
        f'<div class="m">{"".join(pills)}</div></div>')


def empty_state(title: str, why: str) -> None:
    _md(f'<div class="p-empty"><b>{escape(title)}</b><div class="why">{why}</div></div>')


def note(html: str) -> None:
    _md(f'<div class="p-note">{html}</div>')


def segmented_bar(parts: list[tuple[str, int, str]], total: int) -> None:
    """One whole split into parts; share printed inside only where it fits."""
    blocks, legend = [], []
    delay = 0.0
    for label, count, color in parts:
        if count <= 0:
            continue
        share = count / total
        text = fmt.pct(share, 0) if share >= 0.08 else ""
        blocks.append(f'<div style="flex:{count};background:{color};animation-delay:{delay}s" '
                      f'title="{escape(label)}: {count} / {total} ({fmt.pct(share)})">{text}</div>')
        legend.append(f'<span style="--c:{color}">{escape(label)} · <b>{count}</b></span>')
        delay += 0.15
    _md(f'<div class="p-seg" role="img" aria-label="{T(f"{total} yorumun dağılımı", f"split of {total} reviews")}">{"".join(blocks)}</div>'
        f'<div class="p-legend">{"".join(legend)}</div>')


def sidebar_footer(n_reviews: int, n_ratings: int, collected) -> None:
    when = fmt.date_long(collected) if collected is not None else "—"
    with st.sidebar:
        st.space("medium")
        _md(f"""<div class="p-side"><div class="brand">PULSE</div><div class="rule"></div>
<div>{T("Oyuncu Analitiği", "Player Analytics")} · <i>Market Match!</i></div><br>
<div>{T("Veri tarihi", "Data as of")} <span class="num">{when}</span></div>
<div><span class="num">{fmt.num(n_ratings)}</span> {T("değerlendirme", "ratings")}</div>
<div><span class="num">{fmt.num(n_reviews)}</span> {T("yazılı yorum", "written reviews")}</div><br>
<div>{T("Bold Games Data Analyst başvurusu için herkese açık mağaza verisiyle hazırlanmış bağımsız bir "
        "portfolyo çalışmasıdır; resmi bir Bold Games ürünü değildir.",
        "An independent portfolio project built from public store data for a Bold Games Data Analyst "
        "application; not an official Bold Games product.")}</div></div>""")


def official_check(rows: list[dict]) -> None:
    """Strip that compares our numbers with what the store pages display.
    rows: label, ours_avg, ours_n, shown_avg, shown_count_text, ok."""
    t = tok()
    items = []
    for r in rows:
        mark = "✓" if r["ok"] else "≠"
        col = t["green"] if r["ok"] else t["neg"]
        items.append(
            f'<span class="item"><b style="color:{col}">{mark}</b> {escape(r["label"])}: '
            f'bizde <b>{fmt.num(r["ours_avg"], 2)} ★ · {fmt.num(r["ours_n"])}</b> → '
            f'sayfada <b>{fmt.num(r["shown_avg"], 1)} ★ · {escape(r["shown_count_text"])}</b></span>')
    allok = all(r["ok"] for r in rows)
    head = "Resmi rakamlarla uyumlu" if allok else "Resmi rakamlarla fark var"
    _md(f'<div class="p-check"><span class="h">{"✓" if allok else "!"} {head}</span>{"".join(items)}</div>')


ACTION_LABELS = ("Öneri", "Recommendation")   # the highlighted row of a recommendation card


def product_rec(n: int, title: str, rows: list[tuple[str, str]], metrics: list[str]) -> None:
    """Text side of a product recommendation card. `rows` are (label, html); a row labelled
    'Öneri' / 'Recommendation' is highlighted."""

    body = "".join(
        f'<div class="row{" action" if label in ACTION_LABELS else ""}"><span class="l">{escape(label)}</span>'
        f'<span>{html}</span></div>' for label, html in rows)
    chips = "".join(f"<span>{escape(m)}</span>" for m in metrics)
    body += (f'<div class="row"><span class="l">{T("Nasıl ölçülür", "How to measure")}</span>'
             f'<span class="metrics">{chips}</span></div>')
    _md(f'<div class="p-prec"><div class="top"><span class="k">{T("ÖNERİ", "RECOMMENDATION")} {n}</span></div>'
        f'<div class="t">{escape(title)}</div>{body}</div>')


def shot_tag(text: str, concept: bool = False) -> None:
    """Small label above a screenshot: KONSEPT (our mockup) vs ŞU AN (the live game)."""
    _md(f'<span class="p-shot-tag{" concept" if concept else ""}">{escape(text)}</span>')


def step_arrow() -> None:
    """Arrow between two stages of a progression strip."""
    _md('<div class="p-step-arrow" aria-hidden="true"><span>→</span></div>')


def takeaways(bullets: list[str], title: str | None = None) -> None:
    """Short analyst read-out under a chart: 2–3 bullets, numbers computed in src.insights."""
    if not bullets:
        return
    title = title or T("Ne söylüyor?", "What it says")
    items = "".join(f"<li>{b}</li>" for b in bullets)
    _md(f'<div class="p-take"><div class="h">{escape(title)}</div><ul>{items}</ul></div>')
