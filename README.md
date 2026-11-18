# PULSE · Market Match! Oyuncu Analitiği

Streamlit dashboard analysing public App Store and Google Play ratings and reviews of
*Market Match!* (Bold Games): ratings by country, platform gap, what players say, and my own
product recommendations after playing the game to level 54.

**Live:** https://bold-pulse-dashboard.streamlit.app

> Independent portfolio work prepared for a Bold Games Data Analyst application, built only from
> publicly available store data. It is not an official Bold Games product.

## Pages
- **Genel Bakış** – headline KPIs, check against the official store numbers, world map, trend
- **Pazarlar & Platformlar** – country ranking with confidence tiers, App Store vs Google Play
- **Oyuncu Sesi** – every review, filterable by store, tone and AI topic (with English translations)
- **Benim Ürün Önerilerim** – competitor-inspired product recommendations with concept mockups
- **Yorum Gezgini** – searchable review table with CSV export
- **Metodoloji & Veri Kalitesi** – sources, cleaning, statistics, and AI-vs-human label agreement

## Run the dashboard
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Rebuild the data (optional)
```bash
pip install -r requirements-pipeline.txt
python -m src.collect      # Stage 1: data/reviews_raw.csv, data/ratings_by_country.csv
python -m src.clean        # Stage 2: data/reviews_clean.csv, data/quality_report.json
python -m src.translate    # Stage 3a: data/translations.csv  (Gemini free tier, GEMINI_API_KEY in .env)
python -m src.classify     # Stage 3b: data/classified.csv    (Gemini free tier)
python -m pytest tests     # metric unit tests
```
Topic labels were checked against a blind 50-review hand-labelled sample
(`PULSE_TOOLS=1 streamlit run app.py` opens the labelling tool).
