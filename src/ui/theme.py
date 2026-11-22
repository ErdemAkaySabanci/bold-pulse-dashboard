"""Design tokens for PULSE. Chrome uses the Bold Games red (#FE0000, sampled from the
logo); data colours come from the Market Match! icon (cart red, sky blue, lettuce
green, sun yellow, carrot orange) plus a berry purple.

All chart colors were checked with the dataviz palette validator in both modes.
Roles:
  neg / neu / pos -> sentiment (red / amber / blue: red-blue survives colour-blindness)
  as / gp         -> store identity (App Store blue / Google Play green)
  brand           -> Bold red: hero, section chips, controls, links (chrome, not data)
"""
from __future__ import annotations

import streamlit as st

TOKENS: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#FFF9F1", "surface": "#FFFFFF", "surface_2": "#F3F0EA",
        "ink": "#12172B", "ink_2": "#3A4361", "muted": "#6B7490",
        "border": "#ECE4D8", "grid": "#EFEAE2", "shadow": "rgba(92, 64, 30, 0.10)",
        "sky": "#CFE8FF", "sky_2": "#EAF5FF", "side": "#FFF4E6", "cloud": "rgba(255, 255, 255, 0.85)",
        "neg": "#E5352B", "neu": "#DD9200", "pos": "#1E88E5",
        "as": "#0A84FF", "gp": "#22A45D",
        "red": "#E5352B", "blue": "#1E88E5", "purple": "#7C4DFF", "green": "#22A45D",
        "orange": "#EE6A0E", "yellow": "#FFC21A",
        "hero_a": "#FF4B2B", "hero_b": "#FE0000", "hero_c": "#A3001E",
        "brand": "#FE0000", "brand_soft": "#FFE8E6",
        "neg_bg": "#FDECEA", "pos_bg": "#E8F2FD", "neu_bg": "#FFF4DC",
        "bench": "#A9B0C0",  # industry benchmark (third-party data), never used for our own data
    },
    "dark": {
        "bg": "#0E1222", "surface": "#151A2E", "surface_2": "#1B2139",
        "ink": "#EEF1FA", "ink_2": "#C3C9DD", "muted": "#8C94B0",
        "border": "#232A44", "grid": "#1F2640", "shadow": "rgba(0, 0, 0, 0.35)",
        "sky": "#1A2A5C", "sky_2": "#121B3A", "side": "#111628", "cloud": "rgba(170, 190, 255, 0.10)",
        "neg": "#E0402F", "neu": "#D0960E", "pos": "#2E8BE0",
        "as": "#2F8FFF", "gp": "#22A060",
        "red": "#F0503F", "blue": "#2E8BE0", "purple": "#9271FF", "green": "#22A060",
        "orange": "#E2691C", "yellow": "#F2B51C",
        "hero_a": "#E8341F", "hero_b": "#D10000", "hero_c": "#6E0016",
        "brand": "#FF3B30", "brand_soft": "#3A1416",
        "neg_bg": "#3A1A1E", "pos_bg": "#13274A", "neu_bg": "#3A2C10",
        "bench": "#5E6784",
    },
}

SANS = "'Plus Jakarta Sans', Inter, system-ui, -apple-system, Segoe UI, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, Menlo, monospace"


def mode() -> str:
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:  # noqa: BLE001
        return "light"


def tok() -> dict[str, str]:
    return TOKENS[mode()]


def inject_css() -> None:
    t = tok()
    st.html(f"""
<style>
  @keyframes p-rise {{ from {{ opacity: 0; transform: translateY(14px); }}
                       to {{ opacity: 1; transform: none; }} }}
  @keyframes p-grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
  @keyframes p-drift {{ from {{ background-position: 0 0; }} to {{ background-position: 240px 0; }} }}
  @media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{ animation: none !important; transition: none !important; }}
  }}

  .block-container {{ max-width: 1240px; padding-top: 1.6rem; padding-bottom: 4rem; }}

  /* ---------- page background: "market sky" (sky wash + soft clouds -> warm cream) ---------- */
  .stApp {{ background: {t['bg']}; }}
  [data-testid="stMain"] {{ background-color: {t['bg']};
    background-image:
      radial-gradient(ellipse 300px 64px at 82% 96px, {t['cloud']}, transparent 70%),
      radial-gradient(ellipse 190px 46px at 90% 72px, {t['cloud']}, transparent 70%),
      radial-gradient(ellipse 260px 56px at 14% 168px, {t['cloud']}, transparent 70%),
      radial-gradient(ellipse 150px 36px at 22% 146px, {t['cloud']}, transparent 70%),
      linear-gradient(180deg, {t['sky']} 0px, {t['sky_2']} 260px, {t['bg']} 620px);
    background-repeat: no-repeat; background-attachment: local; }}
  [data-testid="stHeader"] {{ background: transparent; }}
  /* hide the toolbar's action buttons (Share / star / edit / GitHub / ⋮ menu). The toolbar itself
     stays: on mobile it holds the logo and the button that opens the sidebar. */
  [data-testid="stToolbarActions"], [data-testid="stToolbarActionButton"], [data-testid="stMainMenu"],
  [data-testid="stAppDeployButton"], [data-testid="stDecoration"] {{ display: none !important; }}
  [data-testid="stSidebar"] {{ background: {t['side']} !important; border-right: 1px solid {t['border']}; }}
  @media (max-width: 640px) {{ .block-container {{ padding-top: 3.6rem; }} }}

  /* ---------- browser surfaces wear the palette ---------- */
  ::selection {{ background: {t['brand_soft']}; color: {t['ink']}; }}
  :focus-visible {{ outline: 2px solid {t['brand']}; outline-offset: 2px; }}
  * {{ scrollbar-width: thin; scrollbar-color: {t['border']} transparent; }}
  .p-kpi .value, .p-hero-stat .v, .p-rtable, .p-take li b, .p-check b {{ font-variant-numeric: tabular-nums; }}

  /* ---------- data-source line under section titles ---------- */
  .p-src {{ display: inline-flex; flex-wrap: wrap; align-items: baseline; gap: .45rem; margin-top: .45rem;
    font-size: .8rem; line-height: 1.45; color: {t['ink_2']}; background: {t['surface']};
    border: 1px solid {t['border']}; border-radius: 10px; padding: .25rem .65rem; }}
  .p-src b {{ font-size: .66rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase;
    color: {t['brand']}; }}

  /* ---------- analyst read-out under every chart ---------- */
  .p-take {{ background: {t['surface']}; border: 1px solid {t['border']};
    border-radius: 14px; padding: .85rem 1.15rem .75rem; margin: .6rem 0 .4rem 0;
    box-shadow: 0 8px 22px -16px {t['shadow']}; }}
  .p-take .h {{ display: flex; align-items: center; gap: .45rem; font-size: .72rem; font-weight: 800;
    letter-spacing: .1em; text-transform: uppercase; color: {t['brand']}; margin-bottom: .4rem; }}
  .p-take ul {{ margin: 0; padding-left: 1.1rem; }}
  .p-take li {{ font-size: .92rem; line-height: 1.55; color: {t['ink_2']}; margin: .2rem 0; }}
  .p-take li::marker {{ color: {t['brand']}; }}
  .p-take li b {{ color: {t['ink']}; }}
  [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {{
    animation: p-rise .7s cubic-bezier(.2,.7,.2,1) both; }}

  /* ---------- hero ---------- */
  .p-hero {{ position: relative; overflow: hidden; border-radius: 24px; padding: 2rem 2.2rem 1.9rem;
    color: #fff; margin-bottom: 1.4rem;
    background: linear-gradient(120deg, {t['hero_a']} 0%, {t['hero_b']} 58%, {t['hero_c']} 100%);
    box-shadow: 0 20px 44px -20px {t['hero_b']}; animation: p-rise .6s ease both; }}
  .p-hero::before {{ content: ""; position: absolute; inset: 0; opacity: .16; pointer-events: none;
    background-image: repeating-linear-gradient(100deg, transparent 0 38px,
      rgba(255,255,255,.9) 38px 40px, transparent 40px 120px);
    animation: p-drift 9s linear infinite; }}
  .p-hero::after {{ content: ""; position: absolute; width: 360px; height: 360px; right: -90px; top: -140px;
    border-radius: 50%; background: radial-gradient(circle, rgba(255,194,26,.55), transparent 65%); }}
  .p-hero > * {{ position: relative; z-index: 1; }}
  .p-hero .logo {{ position: absolute; top: 1.7rem; right: 2rem; height: 26px; opacity: .95; z-index: 2; }}
  .p-hero .p-eyebrow {{ background: rgba(255,255,255,.2); }}
  [data-testid="stLogo"] {{ height: 2rem; }}
  .p-eyebrow {{ display: inline-block; font-size: .72rem; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; background: rgba(255,255,255,.18); padding: .3rem .7rem;
    border-radius: 999px; margin-bottom: .9rem; }}
  .p-hero h1 {{ font-size: 2.35rem; font-weight: 800; line-height: 1.12; margin: 0 0 .55rem 0;
    padding: 0; color: #fff; letter-spacing: -0.02em; }}
  .p-hero p {{ font-size: 1.06rem; line-height: 1.55; margin: 0; max-width: 64ch; color: rgba(255,255,255,.92); }}
  .p-hero p b {{ color: #fff; }}
  .p-hero-stats {{ display: flex; flex-wrap: wrap; gap: .7rem; margin-top: 1.3rem; }}
  .p-hero-stat {{ background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.22);
    border-radius: 16px; padding: .7rem 1rem; min-width: 150px; backdrop-filter: blur(6px); }}
  .p-hero-stat .v {{ font-size: 1.55rem; font-weight: 800; line-height: 1.1; }}
  .p-hero-stat .l {{ font-size: .78rem; opacity: .85; margin-top: .15rem; }}

  /* ---------- sections ---------- */
  .p-section {{ margin: 2.4rem 0 .7rem 0; display: flex; gap: .8rem; align-items: flex-start; }}
  .p-section .ico {{ flex: none; width: 38px; height: 38px; border-radius: 12px; display: grid;
    place-items: center; font-size: 1.1rem; color: #fff; }}
  .p-section h3 {{ font-weight: 800; font-size: 1.3rem; margin: 0 !important; padding: 0 !important;
    color: {t['ink']}; letter-spacing: -0.01em; }}
  .p-section p {{ color: {t['muted']}; margin: .2rem 0 0 0 !important; font-size: .92rem; max-width: 85ch; }}

  /* ---------- cards ---------- */
  .p-card {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 18px;
    padding: 1.15rem 1.25rem; box-shadow: 0 6px 20px -10px {t['shadow']};
    animation: p-rise .6s cubic-bezier(.2,.7,.2,1) both; transition: transform .2s ease, box-shadow .2s ease; }}
  .p-card:hover {{ transform: translateY(-2px); box-shadow: 0 14px 30px -14px {t['shadow']}; }}

  .p-kpi {{ min-height: 150px; position: relative; overflow: hidden; }}
  .p-kpi .chip {{ width: 36px; height: 36px; border-radius: 11px; display: grid; place-items: center;
    color: #fff; font-size: 1rem; margin-bottom: .7rem; }}
  .p-kpi .label {{ font-size: .84rem; color: {t['muted']}; font-weight: 600; }}
  .p-kpi .value {{ font-size: 2rem; font-weight: 800; color: {t['ink']}; line-height: 1.15;
    letter-spacing: -0.02em; }}
  .p-kpi .ctx {{ font-size: .8rem; color: {t['ink_2']}; margin-top: .3rem; line-height: 1.45; }}
  .p-kpi .bar {{ position: absolute; left: 0; bottom: 0; height: 4px; width: 100%;
    transform-origin: left; animation: p-grow 1s .2s cubic-bezier(.2,.7,.2,1) both; }}

  .p-kpi .chip.logo {{ background: transparent; width: 40px; height: 40px; }}
  .p-kpi .chip.logo img {{ width: 40px; height: 40px; }}
  .p-store-logo {{ vertical-align: -2px; display: inline-block; }}
  .p-pill .p-store-logo {{ vertical-align: -2px; margin-right: .15rem; }}
  .p-logo-legend {{ display: flex; flex-wrap: wrap; gap: .6rem 1.4rem; align-items: center;
    font-size: .86rem; color: {t['ink_2']}; margin: .2rem 0 .2rem 0; }}
  .p-logo-legend .item {{ display: inline-flex; align-items: center; gap: .45rem; }}
  .p-logo-legend .mark {{ display: inline-block; width: 12px; height: 12px; }}
  .p-logo-legend .mark.dot {{ border-radius: 50%; background: {t['as']}; }}
  .p-logo-legend .mark.diamond {{ background: {t['gp']}; transform: rotate(45deg) scale(.85); }}
  .p-logo-legend .sub {{ color: {t['muted']}; font-size: .8rem; }}
  .p-check {{ display: flex; flex-wrap: wrap; gap: .4rem 1.4rem; align-items: center; font-size: .84rem;
    color: {t['ink_2']}; background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 14px;
    padding: .6rem 1rem; margin: .9rem 0 0 0; }}
  .p-check .h {{ font-weight: 800; color: {t['green']}; }}
  .p-check b {{ color: {t['ink']}; }}
  /* ---------- product recommendation: one card = text column + screenshots column ---------- */
  [class*="st-key-rec-"] {{ background: {t['surface']}; border: 1px solid {t['border']};
    border-left: 6px solid {t['brand']}; border-radius: 22px; padding: 1.5rem 1.6rem 1.3rem;
    box-shadow: 0 10px 28px -16px {t['shadow']}; margin-bottom: 1.2rem;
    animation: p-rise .6s cubic-bezier(.2,.7,.2,1) both; }}
  .p-prec .top {{ display: flex; flex-wrap: wrap; align-items: center; gap: .45rem; }}
  .p-prec .k {{ font-size: .72rem; font-weight: 800; letter-spacing: .12em; color: {t['brand']};
    margin-right: auto; }}
  .p-prec .lvl {{ font-size: .72rem; font-weight: 700; border-radius: 999px; padding: .2rem .65rem;
    background: var(--bg); color: var(--c); }}
  .p-prec .lvl b {{ font-weight: 800; }}
  .p-prec .t {{ font-size: 1.45rem; font-weight: 800; line-height: 1.25; letter-spacing: -0.015em;
    color: {t['ink']}; margin: .55rem 0 1rem 0; }}
  .p-prec .row {{ display: grid; grid-template-columns: 118px 1fr; gap: .2rem 1rem; padding: .7rem 0;
    border-top: 1px solid {t['border']}; font-size: .94rem; line-height: 1.58; color: {t['ink_2']}; }}
  .p-prec .row .l {{ font-size: .7rem; font-weight: 800; letter-spacing: .07em; text-transform: uppercase;
    color: {t['muted']}; padding-top: .2rem; }}
  .p-prec .row b {{ color: {t['ink']}; }}
  .p-prec .row.action {{ background: {t['brand_soft']}; border-top: 0; border-radius: 12px;
    padding: .75rem .85rem; margin: .2rem -.85rem; }}
  .p-prec .row.action .l {{ color: {t['brand']}; }}
  .p-prec .row.action span:last-child {{ color: {t['ink']}; font-weight: 600; }}
  .p-prec .metrics {{ display: flex; flex-wrap: wrap; gap: .35rem; }}
  .p-prec .metrics span {{ font-size: .8rem; font-weight: 600; border-radius: 8px; padding: .2rem .55rem;
    background: {t['surface_2']}; color: {t['ink_2']}; }}
  .p-prec .src {{ display: inline-block; margin-top: .8rem; font-size: .72rem; font-weight: 700;
    color: {t['muted']}; }}
  .p-rtable {{ width: 100%; border-collapse: collapse; font-size: .88rem; }}
  .p-rtable th {{ text-align: left; font-size: .68rem; font-weight: 800; letter-spacing: .07em;
    text-transform: uppercase; color: {t['muted']}; padding: 0 .6rem .4rem 0; }}
  .p-rtable td {{ padding: .42rem .6rem .42rem 0; border-top: 1px solid {t['border']}; vertical-align: middle; }}
  .p-rtable, .p-rtable tr, .p-rtable th, .p-rtable td {{ border-left: 0 !important; border-right: 0 !important;
    background: transparent !important; }}
  .p-rtable thead tr, .p-rtable th {{ border-top: 0 !important; border-bottom: 0 !important; }}
  .p-rtable td.n {{ width: 1.6rem; font-weight: 800; color: {t['brand']}; }}
  .p-rtable .snd {{ font-weight: 600; color: {t['ink']}; }}
  .p-shot-tag {{ display: inline-block; font-size: .66rem; font-weight: 800; letter-spacing: .1em;
    border-radius: 6px; padding: .12rem .45rem; margin-bottom: .35rem;
    background: {t['surface_2']}; color: {t['ink_2']}; }}
  .p-shot-tag.concept {{ background: {t['brand']}; color: #fff; }}
  [class*="st-key-rec-"] [data-testid="stImage"] img {{ border-radius: 16px;
    box-shadow: 0 10px 24px -12px {t['shadow']}; }}
  [class*="st-key-rec-"] [data-testid="stImageCaption"] {{ font-size: .78rem; color: {t['muted']};
    text-align: center; line-height: 1.4; }}
  /* progression strip (stage -> stage): always one row, arrows centred between the screens */
  [class*="st-key-strip-"] {{ border-top: 1px solid {t['border']}; padding-top: 1rem; margin-top: .4rem; }}
  [class*="st-key-strip-"] [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: .6rem; }}
  [class*="st-key-strip-"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    min-width: 0 !important; width: auto !important; }}
  [class*="st-key-strip-"] [data-testid="stImage"] img {{ border-radius: 14px;
    box-shadow: 0 10px 24px -12px {t['shadow']}; }}
  [class*="st-key-strip-"] [data-testid="stImageCaption"] {{ font-size: .8rem; font-weight: 600;
    color: {t['ink_2']}; text-align: center; }}
  .p-step-arrow {{ display: grid; place-items: center; margin-bottom: 1.6em; }}
  [class*="st-key-strip-"] [data-testid="stColumn"]:has(.p-step-arrow) {{ align-self: center; }}
  .p-step-arrow span {{ display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%;
    background: {t['brand']}; color: #fff; font-size: 1.3rem; font-weight: 800;
    box-shadow: 0 8px 18px -8px {t['brand']}; }}
  @media (max-width: 640px) {{ .p-step-arrow span {{ width: 24px; height: 24px; font-size: .85rem; }}
    [class*="st-key-strip-"] [data-testid="stHorizontalBlock"] {{ gap: .3rem; }}
    [class*="st-key-strip-"] [data-testid="stImageCaption"] {{ font-size: .72rem; }} }}
  /* the two phone screenshots stay side by side even on narrow screens */
  [class*="st-key-rec-"] [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] {{
    flex-wrap: nowrap !important; gap: .75rem; }}
  [class*="st-key-rec-"] [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }}
  @media (max-width: 640px) {{ .p-prec .row {{ grid-template-columns: 1fr; }}
    [class*="st-key-rec-"] {{ padding: 1.1rem 1rem; }} }}
  .p-trust {{ display: inline-flex; align-items: center; gap: .3rem; font-size: .72rem; font-weight: 700;
    border-radius: 999px; padding: .18rem .6rem; margin-top: .6rem; }}
  .p-trust.hi {{ background: {t['pos_bg']}; color: {t['pos']}; }}
  .p-trust.mid {{ background: {t['neu_bg']}; color: {t['neu']}; }}
  .p-trust.lo {{ background: {t['neg_bg']}; color: {t['neg']}; }}

  .p-find {{ min-height: 250px; display: flex; flex-direction: column; border-top: 5px solid var(--c); }}
  .p-find .n {{ font-size: .72rem; font-weight: 800; letter-spacing: .1em; color: var(--c); }}
  .p-find .t {{ font-size: 1.12rem; font-weight: 800; line-height: 1.3; color: {t['ink']};
    margin: .35rem 0 .45rem 0; }}
  .p-find .b {{ font-size: .9rem; line-height: 1.55; color: {t['ink_2']}; margin-bottom: .7rem; }}
  .p-find .b b {{ color: {t['ink']}; }}
  .p-find .p-trust {{ margin-top: auto; align-self: flex-start; }}

  .p-quote {{ border-left: 5px solid var(--c); margin-bottom: .65rem; padding: .9rem 1.1rem; }}
  .p-quote .q {{ font-size: 1rem; line-height: 1.55; color: {t['ink']}; }}
  .p-quote .en {{ margin-top: .6rem; padding: .55rem .75rem; border-radius: 10px;
    background: {t['surface_2']}; }}
  .p-quote .en-h {{ font-size: .72rem; font-weight: 700; color: {t['muted']}; letter-spacing: .02em;
    margin-bottom: .2rem; }}
  .p-quote .en-t {{ font-size: .94rem; line-height: 1.5; color: {t['ink_2']}; }}
  .p-pill.date {{ background: {t['brand_soft']}; color: {t['brand']}; }}
  .p-quote .m {{ display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .6rem; align-items: center; }}
  .p-pill {{ font-size: .72rem; font-weight: 700; border-radius: 999px; padding: .15rem .55rem;
    background: {t['surface_2']}; color: {t['ink_2']}; }}
  .p-pill.stars {{ color: #fff; background: var(--c); letter-spacing: .05em; }}

  .p-empty {{ border: 2px dashed {t['border']}; border-radius: 18px; padding: 1.3rem 1.4rem; color: {t['muted']}; }}
  .p-empty b {{ color: {t['ink']}; }}
  .p-empty .why {{ font-size: .88rem; margin-top: .3rem; line-height: 1.55; }}

  .p-note {{ font-size: .83rem; color: {t['muted']}; line-height: 1.55; background: {t['surface_2']};
    border-radius: 12px; padding: .65rem .9rem; margin: .6rem 0 0 0; }}
  .p-note b {{ color: {t['ink_2']}; }}

  .p-seg {{ display: flex; gap: 3px; height: 34px; margin: .3rem 0 .7rem 0; }}
  .p-seg div {{ border-radius: 9px; display: flex; align-items: center; padding-left: .6rem; color: #fff;
    font-size: .8rem; font-weight: 800; white-space: nowrap; transform-origin: left;
    animation: p-grow .9s cubic-bezier(.2,.7,.2,1) both; }}
  .p-legend {{ display: flex; flex-wrap: wrap; gap: .5rem 1.1rem; font-size: .82rem; color: {t['ink_2']}; }}
  .p-legend span::before {{ content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 3px;
    margin-right: .4rem; vertical-align: -1px; background: var(--c); }}

  .p-side .brand {{ font-weight: 800; font-size: 1.35rem; letter-spacing: .04em; color: {t['brand']}; }}
  .p-side .rule {{ height: 4px; width: 42px; border-radius: 4px; background: {t['brand']}; margin: .4rem 0 .6rem; }}
  [data-testid="stSidebarNav"] [aria-current="page"] {{ background: {t['brand_soft']} !important; }}
  [data-testid="stSidebarNav"] [aria-current="page"] span {{ color: {t['brand']} !important; font-weight: 700; }}
  .p-hero-stat .v {{ letter-spacing: -0.01em; }}
  .p-side {{ font-size: .8rem; color: {t['muted']}; line-height: 1.6; }}
  .p-side .num {{ color: {t['ink']}; font-weight: 700; }}

  .p-steps {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(175px, 1fr)); gap: .7rem; }}
  .p-step {{ border-top: 4px solid var(--c); }}
  .p-step .k {{ font-size: .7rem; font-weight: 800; letter-spacing: .1em; color: var(--c); }}
  .p-step .t {{ font-weight: 800; font-size: .95rem; color: {t['ink']}; margin: .25rem 0; }}
  .p-step .d {{ font-size: .82rem; color: {t['muted']}; line-height: 1.5; }}

  @media (max-width: 640px) {{
    .p-hero {{ padding: 1.4rem 1.2rem; border-radius: 18px; }}
    .p-hero h1 {{ font-size: 1.65rem; }}
    .p-hero-stat {{ min-width: 0; flex: 1 1 40%; }}
    .p-kpi .value {{ font-size: 1.7rem; }}
  }}
</style>
""")
