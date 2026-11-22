"""Market Context (English): Appfigures industry benchmark next to Market Match's own store data.

Rules: every industry figure comes from data/industry_benchmark.csv (typed in verbatim, with the
report's printed page number); industry data is drawn in neutral grey and labelled "Industry
benchmark", Market Match data in brand red and labelled "Market Match reviews".
"""
import streamlit as st

from src import insights
from src import metrics as M
from src.data import load
from src.ui import charts, components as C

B = load.benchmark()
R = load.ratings()
rv = load.reviews()
countries = M.app_store_countries(R).set_index("country")
store_avg = float(countries["prior"].iloc[0])
SRC = "Appfigures, <i>Mobile Games in 2025</i>"


def fig(section: str, item: str) -> tuple[float, int]:
    """(value, printed page) of one industry figure; fails loudly if it is not in the CSV."""
    row = B[(B["section"] == section) & (B["item"] == item)].iloc[0]
    return float(row["value"]), int(row["page"])


def pct(v: float) -> str:
    return f"{v:g}%"


C.hero(
    "Market Context",
    "How Market Match compares with the industry",
    "Selected figures from Appfigures' <b>Mobile Games in 2025</b> report (2024 data), set next to Market "
    "Match's own App Store and Google Play ratings and reviews. Grey always means <b>Industry benchmark</b>; "
    "red always means <b>Market Match reviews</b>.",
)
puzzle, p_puzzle = fig("genre_share", "Puzzle")
C.note(f"<b>Read with care.</b> The industry benchmark covers the top 500 and top 1,000 earning games of 2024, "
       f"mostly large and mature titles; its revenue figures are gross in-app purchase spending and exclude "
       f"ad revenue ({SRC}, p. 41). Market Match launched in 2026, and its data here are store ratings and "
       f"written reviews: what players say, not what they do. For context, Puzzle is {pct(puzzle)} of the top "
       f"1,000 earning games, the only Casual genre to rival Mid-Core ({SRC}, p. {p_puzzle}, 35).")

# ---------------------------------------------------------------- monetization
# Market Match column: my play-through to level 84 and the store reviews ("Not observed" is not "absent").
STATUS = {
    "Consumables/Currency via IAP": "present",       # boosters and coins sold in the Shop
    "Limited-Time Events/Offers": "present",         # "Limited Deal" (80% off) and live events
    "IAP Bundles/Packages": "present",               # Starter Bag and a larger booster bundle
    "In-Game Advertising": "present",                # end-of-level ads reported in reviews
    "Ad-Free Paid Version": "present",               # ad-free play is part of the Starter Bag
    "Rewarded Video Ads": "unknown",                 # not observed in play, not mentioned in reviews
}
mon = B[B["section"] == "monetization"]
status = {i: STATUS.get(i, "not_observed") for i in mon["item"]}
cohort = mon["cohort"].iloc[0]

C.section("Monetization: what top earners use, and what Market Match has",
          "Bars show how many of the top 500 earning games use each monetization type. The right-hand "
          "column shows whether it was seen in Market Match.",
          source=(f"Industry benchmark: {cohort.lower()}, 2024 · {SRC}, p. {int(mon['page'].iloc[0])} · "
                  "Market Match: my play-through to level 84 and the store reviews"),
          source_label="Data")
charts.show(charts.monetization_benchmark(mon, status), key="monetization")

n_crit = int(rv["rating_bucket"].isin(["negative", "neutral"]).sum())
n_ads = len(insights.ad_mentions(rv))
cons, p30 = fig("monetization", "Consumables/Currency via IAP")
lto, _ = fig("monetization", "Limited-Time Events/Offers")
rewarded, _ = fig("monetization", "Rewarded Video Ads")
ingame, _ = fig("monetization", "In-Game Advertising")
cosm, _ = fig("monetization", "Unlocks/Cosmetics via IAP")
C.takeaways([
    (f"The must-haves are in place: consumables and limited-time offers are each used by {pct(cons)} of the "
     f"top 500 (p. {p30}), and Market Match has both (boosters and coins, the 80%-off Limited Deal)."
     if cons == lto else
     f"The must-haves are in place: consumables ({pct(cons)}) and limited-time offers ({pct(lto)}) are near "
     f"universal in the top 500 (p. {p30}), and Market Match has both."),
    f"Rewarded video ads are used by {pct(rewarded)} of the top 500, in-game advertising by {pct(ingame)} "
    f"(p. {p30}). In Market Match, ads are the most common complaint: <b>{n_ads} of {n_crit}</b> players who "
    "gave 1–3★ mention them. Moving part of the forced end-of-level ads to opt-in rewarded ads (a life or a "
    "booster for watching) is worth testing (Recommendation 4).",
    f"Unlocks/cosmetics are sold by {pct(cosm)} of the top 500 (p. {p30}) but were not seen in Market Match, "
    "and coins have no visible use in the first levels. This is the clearest gap, and the case for cart "
    "customization (Recommendation 5).",
    "Limits: the report does not define “In-Game Advertising”, and this is a presence check, not revenue "
    "impact. “Not observed” means not seen in my play-through, not proven absent.",
], title="What it says")

# ---------------------------------------------------------------- markets
EN = {"us": "United States", "jp": "Japan", "de": "Germany", "nl": "Netherlands", "mx": "Mexico",
      "tr": "Turkey", "au": "Australia", "tw": "Taiwan", "br": "Brazil"}
yoy = B[B["section"] == "spend_yoy"].set_index("item")
both = [c for c in yoy.index if c in countries.index and countries.loc[c, "n"] >= M.DIRECTIONAL_N]
pts = countries.loc[both, ["n", "avg_rating"]].assign(
    spend_yoy=yoy.loc[both, "value"].values, page=yoy.loc[both, "page"].values,
    name=[EN.get(c, c.upper()) for c in both]).reset_index()

C.section("Markets: where spending is growing, and how Market Match is rated there",
          "Each dot is a country. Left to right: how mobile game spending changed in 2024. Bottom to top: "
          "Market Match's App Store average. Bigger dot, more Market Match ratings. Only countries that "
          f"appear in the report and have {M.DIRECTIONAL_N}+ Market Match ratings are shown.",
          source=(f"Industry benchmark: change in consumer spending, 2024 vs 2023 · {SRC}, p. 7, 23, 24 · "
                  f"Market Match reviews: App Store ratings, {len(pts)} countries"),
          source_label="Data")
charts.show(charts.market_context_scatter(pts, store_avg), key="market_context")


def mm(code: str) -> tuple[int, float]:
    r = countries.loc[code]
    return int(r["n"]), float(r["avg_rating"])


us_n, us_avg = mm("us")
jp_n, jp_avg = mm("jp")
mx_n, mx_avg = mm("mx")
tr_n, tr_avg = mm("tr")
br_n, br_avg = mm("br") if "br" in countries.index else (0, float("nan"))
us_spend, p_us = fig("spend_total", "us")
jp_spend, p_jp = fig("spend_total", "jp")
spd_world, p_w = fig("spend_per_download", "world")
spd_us, p_u = fig("spend_per_download", "us")
written_jp = int(((rv["store"] == "app_store") & (rv["country"] == "jp")).sum())
C.takeaways([
    f"<b>United States.</b> {us_n / countries['n'].sum():.1%} of Market Match's App Store ratings come from the "
    f"US, at {us_avg:.2f} ★, the highest of the large markets. The US is also the largest market by spending "
    f"(${us_spend:g}B, p. {p_us}) and spends ${spd_us:.2f} per download against ${spd_world:.2f} worldwide "
    f"(p. {p_w}–{p_u}). Protect the US experience, and read A/B tests there first.",
    f"<b>Japan.</b> The #3 market by spending (${jp_spend:g}B, p. {p_jp}) shrank "
    f"{abs(yoy.loc['jp', 'value']):g}% in 2024 (p. {int(yoy.loc['jp', 'page'])}), and it is Market Match's "
    f"lowest-rated large market ({jp_avg:.2f} ★ from {jp_n} ratings). With only {written_jp} written reviews, "
    "both 5★, the reason is unknown: check translation, difficulty and level progress there before spending "
    "on user acquisition.",
    f"<b>Growth markets.</b> Mexico (+{yoy.loc['mx', 'value']:g}%) and Turkey (+{yoy.loc['tr', 'value']:g}%) are "
    f"among the fastest-growing markets (p. {int(yoy.loc['mx', 'page'])}), and both rate Market Match at or "
    f"near the store average of {store_avg:.2f} ★ ({mx_avg:.2f} ★ from {mx_n} and {tr_avg:.2f} ★ from {tr_n} "
    "ratings). Brazil "
    f"(+{yoy.loc['br', 'value']:g}%) also rates it highly, but with only {br_n} ratings. Candidates for small "
    "local test campaigns, not yet conclusions.",
    "Limits: ratings are not downloads, and only the App Store publishes per-country rating counts.",
], title="What it says")

with st.expander("All industry figures used on this page"):
    st.dataframe(B.rename(columns={"section": "Section", "item": "Item", "value": "Value", "unit": "Unit",
                                   "page": "Report page", "pdf_page": "PDF page", "year": "Year",
                                   "cohort": "Games covered"}),
                 hide_index=True, width="stretch")
    st.caption(f"Source: {load.BENCHMARK_SOURCE}. Figures typed in verbatim from the report; charts are "
               "redrawn, not copied.")
