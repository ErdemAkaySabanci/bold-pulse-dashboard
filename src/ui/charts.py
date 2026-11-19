"""Plotly chart factories (Turkish UI, Market Match! palette).

Every mark has a hover; values that matter are labelled directly; rating averages
share one colour scale everywhere (red = low, amber = middle, blue = high)."""
from __future__ import annotations

import math
import textwrap
from html import escape

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui import fmt
from src.ui.theme import MONO, SANS, tok

CONFIG = {"displayModeBar": False, "responsive": True, "scrollZoom": False}
# Map: always-visible zoom in / out / reset buttons (no scroll-zoom, so the page still scrolls).
MAP_CONFIG = {"displayModeBar": True, "displaylogo": False, "responsive": True, "scrollZoom": False,
              "modeBarButtons": [["zoomInGeo", "zoomOutGeo", "resetGeo"]]}
SCALE_MIN, SCALE_MAX = 4.0, 5.0


# Stepped (binned) rating scale: five clear classes, no muddy in-between hues.
RATING_BINS = [4.3, 4.5, 4.65, 4.8]  # class edges on the 4.0–5.0 domain


def rating_scale() -> list[list]:
    t = tok()
    colors = [t["neg"], t["orange"], t["neu"], "#4FB3F2", t["pos"]]
    edges = [0.0] + [(b - SCALE_MIN) / (SCALE_MAX - SCALE_MIN) for b in RATING_BINS] + [1.0]
    scale = []
    for i, c in enumerate(colors):
        scale += [[edges[i], c], [edges[i + 1], c]]
    return scale


def rating_color(avg: float) -> str:
    t = tok()
    colors = [t["neg"], t["orange"], t["neu"], "#4FB3F2", t["pos"]]
    return colors[sum(avg >= b for b in RATING_BINS)]


def _base(fig: go.Figure, height: int, left: int = 48, bottom: int = 32, top: int = 12) -> go.Figure:
    t = tok()
    # Keep tick fonts a chart already chose (e.g. category labels in ink).
    kept = {ax: getattr(fig.layout, ax).tickfont.to_plotly_json()
            for ax in ("xaxis", "yaxis") if getattr(fig.layout, ax).tickfont.family}
    fig.update_layout(
        height=height, margin=dict(l=left, r=24, t=top, b=bottom),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=SANS, size=12, color=t["ink_2"]),
        hoverlabel=dict(bgcolor=t["surface"], bordercolor=t["border"],
                        font=dict(family=SANS, size=13, color=t["ink"]), align="left"),
        showlegend=False, separators=",.", bargap=0.42,
    )
    axis = dict(gridcolor=t["grid"], gridwidth=1, zeroline=False, linecolor=t["border"],
                tickfont=dict(family=SANS, size=11, color=t["muted"]), ticks="")
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    for ax, font in kept.items():
        fig.update_layout({ax: {"tickfont": font}})
    return fig


def _legend(fig: go.Figure, top: int = 40) -> go.Figure:
    t = tok()
    fig.update_layout(showlegend=True, margin=dict(t=top), legend=dict(
        orientation="h", x=0, y=1.0, yanchor="bottom", bgcolor="rgba(0,0,0,0)",
        font=dict(family=SANS, size=12, color=t["ink_2"]), itemclick=False, itemdoubleclick=False))
    return fig


def show(fig: go.Figure, key: str | None = None, on_select: str = "ignore", config: dict | None = None):
    return st.plotly_chart(fig, theme=None, config=config or CONFIG, key=key, on_select=on_select,
                           selection_mode="points")


def _colorbar(title: str) -> dict:
    t = tok()
    return dict(title=dict(text=title, font=dict(size=11, color=t["muted"])), thickness=10, len=0.6,
                outlinewidth=0, tickfont=dict(size=10, color=t["muted"]), tickformat=".2f",
                tickvals=[SCALE_MIN] + RATING_BINS + [SCALE_MAX],
                x=1.0, xpad=6)


# --------------------------------------------------------------------------- #
def world_map(countries: pd.DataFrame) -> go.Figure:
    """Bubble map: size = number of ratings, colour = average rating."""
    t = tok()
    d = countries[countries["country"].isin(fmt.ISO3)].sort_values("n", ascending=False)
    size = 8 + 46 * np.sqrt(d["n"] / d["n"].max())
    fig = go.Figure(go.Scattergeo(
        locations=d["country"].map(fmt.ISO3), locationmode="ISO-3",
        marker=dict(size=size, color=d["avg_rating"], colorscale=rating_scale(),
                    cmin=SCALE_MIN, cmax=SCALE_MAX, opacity=0.88,
                    line=dict(color=t["surface"], width=1.5), colorbar=_colorbar("Ortalama")),
        customdata=np.stack([d["country"].map(fmt.country), d["n"], d["avg_rating"]], axis=-1),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[2]:.2f} ★ · %{customdata[1]:,} değerlendirme<extra></extra>",
    ))
    fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False,
                    showcountries=True, countrycolor=t["border"], countrywidth=0.6,
                    showland=True, landcolor=t["surface_2"], showocean=False, bgcolor="rgba(0,0,0,0)",
                    lataxis_range=[-50, 78], showlakes=False)
    fig = _base(fig, 430, left=0, bottom=0, top=0)
    fig.update_layout(dragmode="pan", modebar=dict(orientation="v", bgcolor=t["surface"],
                                                   color=t["ink_2"], activecolor=t["brand"]))
    return fig


def star_bars(shares: list[float], total: int) -> go.Figure:
    t = tok()
    stars = [5, 4, 3, 2, 1]
    vals = [shares[s - 1] for s in stars]
    colors = [t["pos"], "#4FB3F2", t["neu"], t["orange"], t["neg"]]
    fig = go.Figure(go.Bar(
        x=vals, y=[f"{s} ★" for s in stars], orientation="h", width=0.56,
        marker=dict(color=colors, cornerradius=8),
        text=[fmt.pct(v) for v in vals], textposition="outside", cliponaxis=False,
        textfont=dict(family=SANS, size=13, color=t["ink"]),
        customdata=[round(v * total) for v in vals],
        hovertemplate="%{y}: %{text} · yaklaşık %{customdata:,} değerlendirme<extra></extra>",
    ))
    fig.update_xaxes(visible=False, range=[0, max(vals) * 1.2])
    fig.update_yaxes(autorange="reversed", showgrid=False,
                     tickfont=dict(family=SANS, size=14, color=t["ink"]))
    return _base(fig, 250, left=44, bottom=4)


def _wrap(s: str, width: int = 60, max_lines: int = 5) -> str:
    lines = textwrap.wrap(escape(s), width) or [""]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] += " …"
    return "<br>".join(lines)


def review_timeline(rv: pd.DataFrame, events: pd.DataFrame | None = None) -> go.Figure:
    """Every review is a dot: x = date, y = stars (jittered), colour = sentiment,
    size = length of the text. Hover reads the review."""
    t = tok()
    rng = np.random.default_rng(7)
    fig = go.Figure()
    spec = [("positive", "Olumlu (4–5★)", t["pos"]), ("neutral", "Nötr (3★)", t["neu"]),
            ("negative", "Olumsuz (1–2★)", t["neg"])]
    for bucket, name, color in spec:
        d = rv[rv["rating_bucket"] == bucket]
        if d.empty:
            continue
        y = d["rating"] + rng.uniform(-0.28, 0.28, len(d))
        # Size = how many players marked the review helpful (👍).
        size = 9 + 7 * np.sqrt(d["thumbs_up"].clip(lower=0))
        src = d["source_lang"] if "source_lang" in d else d["lang"]
        en = d["text_en"] if "text_en" in d else pd.Series("", index=d.index)
        hover = [f"<b>{fmt.stars(r)}</b> · {fmt.STORE[s]} · {fmt.date_long(dt)}"
                 f"<br>👍 {tu} oyuncu faydalı buldu<br><br>{_wrap(tx)}"
                 + (f"<br><br><b>İngilizce çeviri · {fmt.lang_from(sl)} çevrildi</b><br>{_wrap(e)}"
                    if isinstance(e, str) and e.strip() and sl not in ("en", "und") else "")
                 for r, s, dt, tu, tx, sl, e in zip(d["rating"], d["store"], d["date"], d["thumbs_up"],
                                                    d["text"], src, en)]
        fig.add_trace(go.Scatter(
            x=d["date"], y=y, mode="markers", name=name,
            marker=dict(size=size, color=color, opacity=0.82, line=dict(color=t["surface"], width=1.5)),
            hovertext=hover, hovertemplate="%{hovertext}<extra></extra>"))
    fig.update_yaxes(range=[0.4, 5.6], tickvals=[1, 2, 3, 4, 5],
                     ticktext=["1 ★", "2 ★", "3 ★", "4 ★", "5 ★"], showgrid=True,
                     tickfont=dict(family=SANS, size=12, color=t["ink_2"]))
    months = pd.date_range(rv["date"].min().tz_convert(None).to_period("M").to_timestamp(),
                           rv["date"].max().tz_convert(None), freq="2MS")
    fig.update_xaxes(showgrid=False, tickvals=[m.tz_localize("UTC") for m in months],
                     ticktext=[f"{fmt.MONTHS[m.month - 1]} {str(m.year)[2:]}" for m in months],
                     tickfont=dict(family=SANS, size=11, color=t["muted"]))
    # Release / live-event markers (descriptive only: ~9 reviews a month cannot show impact).
    if events is not None and len(events):
        lo, hi = rv["date"].min(), rv["date"].max()
        for k, (_, e) in enumerate(events.iterrows()):
            if not (lo - pd.Timedelta(days=20) <= e["date"] <= hi + pd.Timedelta(days=20)):
                continue
            fig.add_vline(x=e["date"], line=dict(color=t["brand"], width=1.5, dash="dot"), opacity=0.7)
            fig.add_annotation(x=e["date"], y=5.55, text=e["event"], showarrow=False, textangle=0,
                               yshift=10 + 14 * (k % 2), xanchor="left",
                               font=dict(family=SANS, size=10, color=t["brand"]),
                               bgcolor=t["surface"], borderpad=2)
    fig = _base(fig, 420, left=44, bottom=64, top=56)
    fig = _legend(fig, top=56)
    fig.update_layout(legend=dict(y=-0.14, yanchor="top"))
    return fig


def market_treemap(countries: pd.DataFrame, min_n: int = 1) -> go.Figure:
    """Area = share of App Store ratings, colour = average."""
    t = tok()
    d = countries[countries["n"] >= min_n].copy()
    small = d[d["n"] < 10]
    d = d[d["n"] >= 10]
    labels = [fmt.country(c) for c in d["country"]]
    values = list(d["n"])
    colors = list(d["avg_rating"])
    custom = [[fmt.num(a, 2), fmt.num(n)] for a, n in zip(d["avg_rating"], d["n"])]
    if len(small):
        avg_small = float((small["n"] * small["avg_rating"]).sum() / small["n"].sum())
        labels.append(f"Diğer {len(small)} ülke")
        values.append(int(small["n"].sum()))
        colors.append(avg_small)
        custom.append([fmt.num(avg_small, 2), fmt.num(int(small["n"].sum()))])
    # Explicit root, painted in the page colour with no header, so the plot has no frame.
    root = "App Store"
    total = int(sum(values))
    tile_colors = [rating_color(c) for c in colors]
    fig = go.Figure(go.Treemap(
        ids=[root] + labels, labels=[root] + labels, parents=[""] + [root] * len(labels),
        values=[total] + values, branchvalues="total",
        marker=dict(colors=[t["bg"]] + tile_colors, line=dict(color=t["bg"], width=3),
                    cornerradius=10, pad=dict(t=0, l=0, r=0, b=0)),
        customdata=[["", fmt.num(total)]] + custom,
        texttemplate="<b>%{label}</b><br>%{customdata[0]} ★",
        textfont=dict(family=SANS, size=14, color="#FFFFFF"),
        hovertemplate="<b>%{label}</b><br>%{customdata[0]} ★ · %{customdata[1]} değerlendirme"
                      "<br>App Store değerlendirmelerinin %{percentRoot:.1%}'i<extra></extra>",
        tiling=dict(pad=3), pathbar=dict(visible=False), maxdepth=2,
    ))
    # Colour key, drawn as an invisible scatter so the treemap keeps its stepped scale legend.
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="markers", hoverinfo="skip", showlegend=False,
        marker=dict(colorscale=rating_scale(), cmin=SCALE_MIN, cmax=SCALE_MAX, color=[SCALE_MIN],
                    showscale=True, colorbar=_colorbar("Ortalama"))))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _base(fig, 420, left=0, bottom=0, top=0)


def market_ranking(view: pd.DataFrame, prior: float, below: set[str]) -> go.Figure:
    """Each market: a soft bar for the likely range, a dot for the average
    (coloured on the rating scale, sized by number of ratings)."""
    t = tok()
    d = view.sort_values("avg_rating", ascending=True)
    names = [fmt.country(c) for c in d["country"]]
    fig = go.Figure()
    for (_, r), name in zip(d.iterrows(), names):
        col = t["neg"] if r["country"] in below else t["muted"]
        fig.add_trace(go.Scatter(x=[r["ci_low"], r["ci_high"]], y=[name, name], mode="lines",
                                 line=dict(color=col, width=8), opacity=0.18, hoverinfo="skip"))
    size = 12 + 22 * np.sqrt(d["n"] / d["n"].max())
    fig.add_trace(go.Scatter(
        x=d["avg_rating"], y=names, mode="markers+text",
        marker=dict(size=size, color=d["avg_rating"], colorscale=rating_scale(),
                    cmin=SCALE_MIN, cmax=SCALE_MAX, line=dict(color=t["surface"], width=2)),
        text=[fmt.num(a, 2) for a in d["avg_rating"]], textposition="middle right",
        textfont=dict(family=SANS, size=12, color=t["ink"]),
        customdata=np.stack([d["n"], d["ci_low"], d["ci_high"]], axis=-1),
        hovertemplate=("<b>%{y}</b><br>Ortalama %{x:.2f} ★ · %{customdata[0]:,} değerlendirme"
                       "<br>Olası aralık %{customdata[1]:.2f} – %{customdata[2]:.2f}<extra></extra>"),
    ))
    fig.add_vline(x=prior, line=dict(color=t["ink_2"], width=1.5, dash="solid"))
    fig.add_annotation(x=prior, y=1.0, yref="paper", yanchor="bottom", showarrow=False,
                       text=f"App Store ortalaması {fmt.num(prior, 2)}",
                       font=dict(family=SANS, size=11, color=t["ink_2"]),
                       bgcolor=t["surface"], borderpad=3)
    lo = max(1.0, min(3.4, float(d["ci_low"].min()) - 0.05))
    fig.update_xaxes(range=[lo, 5.08], dtick=0.25, tickformat=".2f")
    fig.update_yaxes(showgrid=False, tickfont=dict(family=SANS, size=13, color=t["ink"]))
    return _base(fig, 90 + 34 * len(d), left=130, top=28)


def platform_dumbbell(df: pd.DataFrame) -> go.Figure:
    t = tok()
    d = df.sort_values("as_avg", ascending=True)
    names = [fmt.country(c) for c in d["country"]]
    fig = go.Figure()
    for (_, r), name in zip(d.iterrows(), names):
        col = t["gp"] if r["gap"] > 0 else t["as"]
        fig.add_trace(go.Scatter(x=[r["as_avg"], r["gp_avg"]], y=[name, name], mode="lines",
                                 line=dict(color=col, width=5), opacity=0.35,
                                 hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=d["as_avg"], y=names, mode="markers", name="App Store",
        marker=dict(size=15, color=t["as"], line=dict(color=t["surface"], width=2)),
        customdata=d[["as_n"]].values,
        hovertemplate="<b>%{y}</b><br>App Store %{x:.2f} ★ · %{customdata[0]:,} değerlendirme<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=d["gp_avg"], y=names, mode="markers", name="Google Play",
        marker=dict(size=15, color=t["gp"], symbol="diamond", line=dict(color=t["surface"], width=2)),
        customdata=d[["gap"]].values,
        hovertemplate=("<b>%{y}</b><br>Google Play %{x:.2f} ★"
                       "<br>Fark %{customdata[0]:+.2f}<extra></extra>")))
    lo = max(1.0, min(float(d["as_avg"].min()), float(d["gp_avg"].min())) - 0.1)
    fig.update_xaxes(range=[lo, 5.06], dtick=0.25, tickformat=".2f")
    fig.update_yaxes(showgrid=False, tickfont=dict(family=SANS, size=13, color=t["ink"]))
    # Draw App Store dots above Google Play diamonds so equal values (e.g. ABD) show both marks.
    fig.data = fig.data[:-2] + (fig.data[-1], fig.data[-2])
    # Legend lives in HTML above the chart (store logos), see components.store_legend.
    return _base(fig, 60 + 32 * len(d), left=130, top=12)


def topic_bars(matrix: pd.DataFrame) -> go.Figure:
    """Diverging counts per topic: negative mentions left, positive right."""
    t = tok()
    m = matrix.sort_values(["negative", "total"], ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=m.index, x=-m["negative"], orientation="h", name="Olumsuz (1–2★)",
                         width=0.55, marker=dict(color=t["neg"], cornerradius=6),
                         customdata=m["negative"], hovertemplate="%{y}: %{customdata} olumsuz<extra></extra>"))
    fig.add_trace(go.Bar(y=m.index, x=m["neutral"], orientation="h", name="Nötr (3★)", width=0.55,
                         marker=dict(color=t["neu"], cornerradius=6),
                         hovertemplate="%{y}: %{x} nötr<extra></extra>"))
    fig.add_trace(go.Bar(y=m.index, x=m["positive"], orientation="h", name="Olumlu (4–5★)", width=0.55,
                         marker=dict(color=t["pos"], cornerradius=6),
                         hovertemplate="%{y}: %{x} olumlu<extra></extra>"))
    lim = max(int(m["negative"].max()), int((m["neutral"] + m["positive"]).max()), 1)
    step = max(1, math.ceil(lim / 4))
    ticks = list(range(-step * math.ceil(lim / step), step * math.ceil(lim / step) + 1, step))
    fig.update_layout(barmode="relative")
    fig.update_xaxes(range=[-lim * 1.15, lim * 1.15], tickvals=ticks, ticktext=[str(abs(v)) for v in ticks])
    fig.update_yaxes(showgrid=False, tickfont=dict(family=SANS, size=13, color=t["ink"]))
    fig.add_vline(x=0, line=dict(color=t["ink_2"], width=1))
    fig = _base(fig, 100 + 34 * len(m), left=170)
    return _legend(fig)


def sankey(rv: pd.DataFrame) -> go.Figure:
    """Store -> sentiment -> topic flow (requires classified reviews)."""
    from src.metrics import split_labels
    t = tok()
    ex = rv.assign(_t=rv["topics"].map(split_labels)).explode("_t").dropna(subset=["_t"])
    stores = ["app_store", "google_play"]
    buckets = ["negative", "neutral", "positive"]
    topics = list(ex["_t"].value_counts().index)
    nodes = [fmt.STORE[s] for s in stores] + [fmt.BUCKET[b] for b in buckets] + topics
    ncol = [t["as"], t["gp"], t["neg"], t["neu"], t["pos"]] + [t["surface_2"]] * len(topics)
    idx = {k: i for i, k in enumerate(stores + buckets + topics)}
    src, dst, val, lcol = [], [], [], []
    alpha = {"negative": t["neg"], "neutral": t["neu"], "positive": t["pos"]}
    for (s, b), n in rv.groupby(["store", "rating_bucket"]).size().items():
        src.append(idx[s]); dst.append(idx[b]); val.append(int(n)); lcol.append(alpha[b])
    for (b, tp), n in ex.groupby(["rating_bucket", "_t"]).size().items():
        src.append(idx[b]); dst.append(idx[tp]); val.append(int(n)); lcol.append(alpha[b])
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=nodes, color=ncol, pad=14, thickness=16, line=dict(width=0)),
        link=dict(source=src, target=dst, value=val,
                  color=[c + "55" for c in lcol]),
        textfont=dict(family=SANS, size=12, color=t["ink"])))
    return _base(fig, 460, left=8, bottom=8)


def topic_scatter(summary: pd.DataFrame, overall: float, reliability: dict | None = None) -> go.Figure:
    """x = reviews mentioning the topic, y = their average stars, size = 1–3★ reviews.
    Answers: is the most-mentioned complaint also the lowest-rated topic?"""
    t = tok()
    d = summary.reset_index().rename(columns={"index": "topic", "_topic": "topic"})
    crit = d["negative"] + d["neutral"]
    size = 14 + 10 * np.sqrt(crit)
    names = [fmt.topic(x) for x in d["topic"]]
    rel = reliability or {}
    rel_txt = [(f"AI güvenilirliği: κ {rel[x][0]:.2f} · {fmt.TRUST[rel[x][1]][1]}".replace(".", ",")
                if x in rel and rel[x][0] == rel[x][0] else "AI güvenilirliği: ölçülemedi (çok nadir)")
               for x in d["topic"]]
    # Labels of bubbles that sit close together alternate above/below so they don't overprint.
    pos: list[str] = []
    for i in range(len(d)):
        near = [j for j in range(i) if abs(np.log10(d["n"].iloc[i]) - np.log10(d["n"].iloc[j])) < 0.15
                and abs(d["avg_rating"].iloc[i] - d["avg_rating"].iloc[j]) < 0.3]
        pos.append("bottom center" if any(pos[j] == "top center" for j in near) else "top center")
    fig = go.Figure(go.Scatter(
        x=d["n"], y=d["avg_rating"], mode="markers+text", text=names, textposition=pos,
        textfont=dict(family=SANS, size=12, color=t["ink"]),
        marker=dict(size=size, color=[rating_color(a) for a in d["avg_rating"]], opacity=0.9,
                    line=dict(color=t["surface"], width=2)),
        hovertext=[f"<b>{nm}</b><br>{fmt.num(n)} yorum · ortalama {fmt.num(a, 2)} ★<br>"
                   f"{fmt.num(c)} tanesi 1–3★<br>{rt}"
                   for nm, n, a, c, rt in zip(names, d["n"], d["avg_rating"], crit, rel_txt)],
        hovertemplate="%{hovertext}<extra></extra>",
    ))
    fig.add_hline(y=overall, line=dict(color=t["ink_2"], width=1))
    fig.add_annotation(x=1, xref="paper", y=overall, xanchor="right", yanchor="bottom", showarrow=False,
                       text=f"Tüm yorumların ortalaması {fmt.num(overall, 2)} ★",
                       font=dict(family=SANS, size=11, color=t["ink_2"]))
    ymin = max(1.0, float(d["avg_rating"].min()) - 0.4)
    fig.update_yaxes(range=[ymin, 5.25], title=dict(text="Ortalama yıldız", font=dict(size=11)))
    fig.update_xaxes(type="log", title=dict(text="Konudan bahseden yorum sayısı (log)", font=dict(size=11)))
    return _base(fig, 440, left=60, bottom=50, top=20)


def level_strip(rows: pd.DataFrame) -> go.Figure:
    """One marker per (review, level) mention on a log level axis; hover reads the review."""
    t = tok()
    fig = go.Figure()
    for bucket, color in (("positive", t["pos"]), ("neutral", t["neu"]), ("negative", t["neg"])):
        d = rows[rows["rating_bucket"] == bucket]
        if d.empty:
            continue
        hover = [f"<b>Seviye {lv}</b> · {fmt.stars(r)}<br><br>{_wrap(tx, 60, 4)}"
                 for lv, r, tx in zip(d["level"], d["rating"], d["text_show"])]
        fig.add_trace(go.Scatter(
            x=d["level"], y=[0] * len(d), mode="markers+text", name=fmt.BUCKET[bucket],
            text=[f"Sv. {lv}" for lv in d["level"]], textposition="top center",
            textfont=dict(family=SANS, size=12, color=t["ink"]),
            marker=dict(size=22, color=color, symbol="diamond", line=dict(color=t["surface"], width=2)),
            hovertext=hover, hovertemplate="%{hovertext}<extra></extra>"))
    fig.update_yaxes(visible=False, range=[-1, 1.2])
    fig.update_xaxes(type="log", title=dict(text="Seviye (log ölçek)", font=dict(size=11)),
                     showgrid=True)
    fig = _base(fig, 200, left=20, bottom=46, top=10)
    return _legend(fig, top=40)


def mini_bars(labels: list[str], values: list[float], colors: list[str], fmt_value=None,
              height: int = 150, xmax: float | None = None) -> go.Figure:
    """Small horizontal bar chart used inside recommendation cards."""
    t = tok()
    text = [fmt_value(v) if fmt_value else str(v) for v in values]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", width=0.55, marker=dict(color=colors, cornerradius=6),
                           text=text, textposition="outside", cliponaxis=False,
                           textfont=dict(family=SANS, size=12, color=t["ink"]),
                           hovertemplate="%{y}: %{text}<extra></extra>"))
    fig.update_xaxes(visible=False, range=[0, (xmax or max(values) or 1) * 1.25])
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(family=SANS, size=12, color=t["ink"]))
    return _base(fig, height, left=150, bottom=4, top=4)
