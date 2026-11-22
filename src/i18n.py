"""Two-language UI (TR default, EN). The language lives in st.session_state["lang"] and in the
URL (?lang=en) so an English link can be shared. Every visible string is written next to its
translation: T("Ne söylüyor?", "What it says")."""
from __future__ import annotations

LANGS = ("tr", "en")


def lang() -> str:
    try:
        import streamlit as st
        v = st.session_state.get("lang")
    except Exception:  # noqa: BLE001  (no Streamlit runtime, e.g. unit tests)
        v = None
    return v if v in LANGS else "tr"


def is_en() -> bool:
    return lang() == "en"


def T(tr: str, en: str) -> str:
    """Pick the string for the current language."""
    return en if is_en() else tr


class LangDict(dict):
    """A dict whose values follow the current language; keys are shared.
    Behaves like the Turkish dict it replaces (fmt.TOPIC[x], list(fmt.TOPIC), .get, .items)."""

    def __init__(self, tr: dict, en: dict):
        super().__init__(tr)
        self._tr, self._en = tr, en

    def _cur(self) -> dict:
        return self._en if is_en() else self._tr

    def __getitem__(self, k):
        cur = self._cur()
        return cur[k] if k in cur else self._tr[k]

    def get(self, k, default=None):
        cur = self._cur()
        return cur.get(k, self._tr.get(k, default))

    def items(self):
        return [(k, self[k]) for k in self._tr]

    def values(self):
        return [self[k] for k in self._tr]

    def update(self, other=None, en: dict | None = None, **kw):  # keep both languages in sync
        if other:
            self._tr.update(other)
            super().update(other)
        if en:
            self._en.update(en)


class LangList(list):
    """A list whose items follow the current language (month names)."""

    def __init__(self, tr: list, en: list):
        super().__init__(tr)
        self._tr, self._en = tr, en

    def __getitem__(self, i):
        return (self._en if is_en() else self._tr)[i]
