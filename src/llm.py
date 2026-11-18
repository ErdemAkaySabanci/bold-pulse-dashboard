"""Shared Gemini helper (free tier only).

One place for: API key, request timeout, structured JSON output, gentle backoff on
429/503, and falling back to a second free model. No grounding, no paid models.
"""
from __future__ import annotations

import json
import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src import config

load_dotenv(config.ROOT / ".env")


def client() -> genai.Client:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY is missing in .env")
    # Hard timeout so a stuck request can never hang a run.
    return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=120_000))


def _call(cl: genai.Client, model: str, prompt: str, payload, schema):
    resp = cl.models.generate_content(
        model=model,
        contents=[prompt, json.dumps(payload, ensure_ascii=False)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=schema, temperature=0.1),
    )
    return list(resp.parsed or [])


def call_json(cl: genai.Client, prompt: str, payload, schema, tag: str = "LLM"):
    """Returns (items, model). Raises RuntimeError if both free models fail; callers
    skip that batch so it is retried on the next run."""
    for model in (config.GEMINI_MODEL, config.GEMINI_FALLBACK_MODEL):
        for attempt in range(4):
            try:
                return _call(cl, model, prompt, payload, schema), model
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                rate = "429" in msg or "RESOURCE_EXHAUSTED" in msg
                busy = "503" in msg or "UNAVAILABLE" in msg or "timed out" in msg.lower()
                print(f"[{tag}] {model} attempt {attempt + 1} failed: {msg[:140]}", flush=True)
                if "404" in msg or "NOT_FOUND" in msg or "PERMISSION_DENIED" in msg or (
                        rate and "limit: 0" in msg):
                    break  # model not available to this free-tier key
                if busy and attempt == 3:
                    break
                time.sleep(15 * (attempt + 1) if (rate or busy) else 3)
    raise RuntimeError("both free models failed for this batch")
