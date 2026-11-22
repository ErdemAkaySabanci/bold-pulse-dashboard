import math

import pandas as pd
import pytest

from src import metrics as M


def test_confidence_tier_thresholds():
    assert M.confidence_tier(50) == "strong"
    assert M.confidence_tier(49) == "directional"
    assert M.confidence_tier(20) == "directional"
    assert M.confidence_tier(19) == "anecdotal"
    assert M.confidence_tier(None) == "anecdotal"
    assert M.confidence_tier(float("nan")) == "anecdotal"


def test_bayes_avg_shrinks_small_samples():
    # 4 ratings averaging 2.0 with a 4.7 prior and m=20 -> (8 + 94) / 24
    assert M.bayes_avg(2.0, 4, 4.7, 20) == pytest.approx(4.25)
    # Large n barely moves.
    assert M.bayes_avg(4.79, 1885, 4.7, 20) == pytest.approx(4.789, abs=1e-3)
    assert M.bayes_avg(3.0, 0, 4.7) == 4.7


def test_wilson_ci_known_values():
    lo, hi = M.wilson_ci(8, 112)
    assert lo == pytest.approx(0.0366, abs=1e-3)
    assert hi == pytest.approx(0.1347, abs=1e-3)
    assert M.wilson_ci(0, 0) == (0.0, 1.0)
    lo, hi = M.wilson_ci(0, 10)
    assert lo == 0.0 and hi > 0


def test_max_rating_sd_bounds():
    assert M.max_rating_sd(5.0) == 0.0
    assert M.max_rating_sd(1.0) == 0.0
    assert M.max_rating_sd(3.0) == pytest.approx(2.0)


def test_mean_ci_is_clipped_to_scale():
    lo, hi = M.mean_ci(4.9, 3, M.max_rating_sd(4.9))
    assert lo >= 1.0 and hi <= 5.0
    assert M.mean_ci(4.0, 0, 1.0) == (1.0, 5.0)


def test_hist_stats():
    mean, sd = M.hist_stats([0, 0, 0, 0, 10])
    assert mean == 5.0 and sd == 0.0
    mean, sd = M.hist_stats([1, 0, 0, 0, 1])
    assert mean == 3.0 and sd == pytest.approx(2.0)
    assert all(math.isnan(x) for x in M.hist_stats([0, 0, 0, 0, 0]))


@pytest.fixture
def ratings():
    return pd.DataFrame([
        {"store": "app_store", "country": "us", "rating_count": 100, "avg_rating": 4.8,
         "scope": "local"},
        {"store": "app_store", "country": "jp", "rating_count": 50, "avg_rating": 4.2,
         "scope": "local"},
        {"store": "app_store", "country": "sa", "rating_count": 4, "avg_rating": 2.0,
         "scope": "local"},
        {"store": "app_store", "country": "eg", "rating_count": 0, "avg_rating": None,
         "scope": "none"},
        {"store": "google_play", "country": "global", "rating_count": 1000, "avg_rating": 4.6,
         "share_1": .02, "share_2": .02, "share_3": .05, "share_4": .11, "share_5": .80,
         "scope": "global"},
        {"store": "google_play", "country": "us", "rating_count": None, "avg_rating": 4.9,
         "share_1": 0, "share_2": 0, "share_3": .05, "share_4": .05, "share_5": .9,
         "scope": "local"},
        {"store": "google_play", "country": "jp", "rating_count": None, "avg_rating": 4.1,
         "share_1": .05, "share_2": .1, "share_3": .1, "share_4": .15, "share_5": .6,
         "scope": "local"},
        {"store": "google_play", "country": "fi", "rating_count": None, "avg_rating": None,
         "scope": "global_fallback"},
    ])


def test_store_summary(ratings):
    s = M.store_summary(ratings).set_index("store")
    assert s.loc["app_store", "rating_count"] == 154
    assert s.loc["app_store", "avg_rating"] == pytest.approx((480 + 210 + 8) / 154)
    assert s.loc["app_store", "countries"] == 3
    assert s.loc["google_play", "rating_count"] == 1000
    assert s.loc["google_play", "countries"] == 2
    assert M.overall_avg(s.reset_index()) == pytest.approx((698 + 4600) / 1154)


def test_app_store_countries(ratings):
    t = M.app_store_countries(ratings).set_index("country")
    assert list(t.index) == ["us", "jp", "sa"]
    assert t.loc["sa", "tier"] == "anecdotal"
    assert t.loc["us", "tier"] == "strong"
    # Shrinkage pulls the tiny 2.0 sample far toward the prior.
    assert t.loc["sa", "bayes_avg"] > 3.5
    assert (t["ci_low"] <= t["avg_rating"]).all() and (t["avg_rating"] <= t["ci_high"]).all()


def test_platform_gap(ratings):
    g = M.platform_gap(ratings).set_index("country")
    assert set(g.index) == {"us", "jp"}
    assert g.loc["us", "gap"] == pytest.approx(0.1)
    assert g.loc["jp", "gap"] == pytest.approx(-0.1)


def test_gp_local_low_share(ratings):
    g = M.gp_local(ratings).set_index("country")
    assert g.loc["jp", "low_share"] == pytest.approx(0.15)


def test_bucket_counts():
    df = pd.DataFrame({"rating_bucket": ["negative"] * 2 + ["neutral"] + ["positive"] * 7})
    b = M.bucket_counts(df).set_index("bucket")
    assert b.loc["negative", "count"] == 2
    assert b.loc["positive", "share"] == pytest.approx(0.7)
    assert b["count"].sum() == 10


def test_topic_matrix_multilabel():
    df = pd.DataFrame({
        "topics": ["ads;purchases", "ads", None, "praise"],
        "rating_bucket": ["negative", "negative", "positive", "positive"],
    })
    m = M.topic_matrix(df)
    assert m.loc["ads", "negative"] == 2
    assert m.loc["purchases", "negative"] == 1
    assert m.loc["praise", "positive"] == 1
    assert list(m.columns) == ["negative", "neutral", "positive", "total"]
    assert m.index[0] == "ads"


def test_topic_summary():
    df = pd.DataFrame({
        "topics": ["ads", "ads;difficulty", "praise", ""],
        "rating": [1, 3, 5, 5],
        "rating_bucket": ["negative", "neutral", "positive", "positive"],
    })
    s = M.topic_summary(df)
    assert s.loc["ads", "n"] == 2
    assert s.loc["ads", "avg_rating"] == pytest.approx(2.0)
    assert s.loc["ads", "negative"] == 1 and s.loc["ads", "neutral"] == 1
    assert "" not in s.index


def test_cohen_kappa_known_values():
    assert M.cohen_kappa([1, 1, 0, 0], [1, 1, 0, 0]) == pytest.approx(1.0)
    # po = 0.5, pe = 0.5 -> 0
    assert M.cohen_kappa([1, 0, 1, 0], [1, 1, 0, 0]) == pytest.approx(0.0)
    # Classic 2x2: a=20,b=5,c=10,d=15 (n=50) -> kappa = 0.4
    a = [1] * 20 + [1] * 5 + [0] * 10 + [0] * 15
    b = [1] * 20 + [0] * 5 + [1] * 10 + [0] * 15
    assert M.cohen_kappa(a, b) == pytest.approx(0.4)
    assert math.isnan(M.cohen_kappa([1, 1], [1, 1]))


def test_label_agreement():
    human = pd.DataFrame({"review_id": ["a", "b", "c"], "topics": ["ads", "praise", "ads;bugs_performance"]})
    model = pd.DataFrame({"review_id": ["a", "b", "c"], "topics": ["ads", "praise", "ads"]})
    tbl, exact = M.label_agreement(human, model, ["ads", "praise", "bugs_performance"])
    t = tbl.set_index("topic")
    assert t.loc["ads", "agreement"] == 1.0
    assert t.loc["bugs_performance", "agreement"] == pytest.approx(2 / 3)
    assert exact == pytest.approx(2 / 3)


def test_matches_display():
    assert M.matches_display(4.786, 1885, 4.8, 1900)
    assert M.matches_display(4.654, 1296, 4.7, 1300)
    assert not M.matches_display(4.74, 1885, 4.8, 1900)
    assert not M.matches_display(4.79, 1700, 4.8, 1900)


def test_apply_human_labels_overrides_and_keeps_raw():
    model = pd.DataFrame({"review_id": ["a", "b"], "topics": ["mechanics", "praise"],
                          "churn_signal": [True, False], "monetization": ["", ""], "level_mentions": ["", ""]})
    human = pd.DataFrame({"review_id": ["a"], "topics": ["difficulty"], "churn_signal": ["False"],
                          "monetization": ["ads"], "level_mentions": ["29"]})
    out = M.apply_human_labels(model, human).set_index("review_id")
    assert out.loc["a", "topics"] == "difficulty" and out.loc["a", "topics_gemini"] == "mechanics"
    assert not out.loc["a", "churn_signal"] and out.loc["a", "churn_signal_gemini"]
    assert out.loc["a", "label_source"] == "insan" and out.loc["b", "label_source"] == "gemini"
    assert out.loc["b", "topics"] == "praise"
    assert M.apply_human_labels(model, None)["label_source"].eq("gemini").all()


def test_topic_reliability():
    assert M.topic_reliability(0.83) == "strong"
    assert M.topic_reliability(0.51) == "directional"
    assert M.topic_reliability(0.2) == "anecdotal"
    assert M.topic_reliability(float("nan")) == "anecdotal"


# ---- chart takeaways (src.insights) ----
from src import insights as I  # noqa: E402


def _countries(rows):
    df = pd.DataFrame(rows, columns=["country", "n", "avg_rating"])
    df["prior"] = (df["n"] * df["avg_rating"]).sum() / df["n"].sum() if len(df) else float("nan")
    df["ci_low"], df["ci_high"] = df["avg_rating"] - 0.1, df["avg_rating"] + 0.1
    return df


def test_takeaways_empty_inputs_say_nothing():
    empty = _countries([])
    assert I.map_takeaways(empty) == []
    assert I.concentration_takeaways(empty) == []
    assert I.ranking_takeaways(empty) == []
    assert I.platform_takeaways(pd.DataFrame(columns=["country", "as_n", "as_avg", "gp_avg", "gap"])) == []


def test_map_takeaways_share_and_thin_countries():
    c = _countries([("us", 600, 4.8), ("gb", 300, 4.6), ("jp", 95, 4.3), ("de", 5, 4.0)])
    out = I.map_takeaways(c)
    assert "%60" in out[0] and "ABD" in out[0]          # 600 / 1000 from one country
    assert any("10'dan az" in b and "<b>1</b>" in b for b in out)


def test_ranking_takeaways_needs_two_reliable_countries():
    assert I.ranking_takeaways(_countries([("us", 600, 4.8), ("gb", 10, 4.6)])) == []
    out = I.ranking_takeaways(_countries([("us", 600, 4.8), ("gb", 300, 4.6), ("jp", 95, 4.3)]))
    assert "ABD" in out[0] and "Japonya" in out[0]


def test_platform_takeaways_always_flags_unknown_counts():
    gap = pd.DataFrame({"country": ["us", "au"], "as_n": [500, 90], "as_avg": [4.8, 4.6],
                        "gp_avg": [4.8, 4.9], "gap": [0.0, 0.3]})
    out = I.platform_takeaways(gap)
    assert "<b>1</b>'inde" in out[0]                     # only us is within 0.2
    assert "Avustralya" in out[1] and "Google Play" in out[1]
    assert "kesin değildir" in out[-1]


# ---- industry benchmark file (Market Context page)
def test_industry_benchmark_rows_are_sourced():
    from src import config
    b = pd.read_csv(config.DATA_DIR / "industry_benchmark.csv")
    assert len(b) > 0
    assert b[["section", "item", "value", "unit", "page", "pdf_page", "year", "cohort"]].notna().all().all()
    assert (b["page"] > 0).all() and (b["pdf_page"] >= b["page"]).all()
    assert not b.duplicated(["section", "item"]).any()
    assert set(b.loc[b["section"] == "monetization", "value"]) <= set(range(0, 101))
