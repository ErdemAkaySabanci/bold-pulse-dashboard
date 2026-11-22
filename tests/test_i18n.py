"""TR / EN switch: formatting follows the language, and every page renders in both languages."""
from pathlib import Path

import pandas as pd
import pytest

from src import i18n
from src.ui import fmt

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["app.py", "views/markets.py", "views/context.py", "views/voice.py", "views/recommendations.py",
         "views/explorer.py"]


@pytest.fixture
def lang(monkeypatch):
    def set_(code):
        monkeypatch.setattr(i18n, "lang", lambda: code)
    return set_


def test_formats_follow_language(lang):
    lang("tr")
    assert fmt.num(4466) == "4.466" and fmt.num(4.712, 2) == "4,71" and fmt.pct(0.071) == "%7,1"
    assert fmt.date_long(pd.Timestamp("2026-11-18")) == "18 Kasım 2026" and fmt.country("jp") == "Japonya"
    assert fmt.topic("ads") == "Reklamlar" and fmt.TRUST["strong"][1] == "Güvenilir"
    lang("en")
    assert fmt.num(4466) == "4,466" and fmt.num(4.712, 2) == "4.71" and fmt.pct(0.071) == "7.1%"
    assert fmt.date_long(pd.Timestamp("2026-11-18")) == "18 November 2026" and fmt.country("jp") == "Japan"
    assert fmt.topic("ads") == "Ads" and fmt.TRUST["strong"][1] == "Reliable"
    assert list(fmt.TOPIC) == list(fmt.TOPIC._tr)      # keys never change with the language


def test_T_picks_language(lang):
    lang("tr")
    assert i18n.T("Merhaba", "Hello") == "Merhaba"
    lang("en")
    assert i18n.T("Merhaba", "Hello") == "Hello"


@pytest.mark.parametrize("code", ["tr", "en"])
@pytest.mark.parametrize("page", PAGES)
def test_pages_render_in_both_languages(page, code):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / page), default_timeout=90)
    at.session_state["lang"] = code
    at.run()
    assert not at.exception, [e.value for e in at.exception]
