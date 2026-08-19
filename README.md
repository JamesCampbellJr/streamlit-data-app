# streamlit-data-app — AI-Company Delivery Template

A Streamlit template for **data-driven web apps**: business metrics dashboards,
expense trackers, automated weekly reports, and content calendars. Maps to
catalog items #6, #12, #13, #14.

## What you get
- `app.py` — sample app: uploads a CSV, shows summary stats + a chart, and
  offers an AI-generated "insights" blurb (flag-gated; works without a key).
- `ai_client.py` — shared AI scaffolding.
- `.github/workflows/ci.yml` — CI.
- `tests/test_app.py` — offline tests.
- `requirements.txt`.

## Quick start
```bash
pip install -r requirements.txt
export AI_ENABLED=true
export AI_API_KEY=sk-...
streamlit run app.py
```
Open the shown localhost URL, upload a CSV with a numeric column, and view the
auto chart + optional AI insights.

## Feature flags (env)
`AI_ENABLED`, `AI_API_KEY`, `AI_MODEL`, `AI_BASE_URL` — same as shared scaffolding.
Without a key the app still renders charts and stats; AI insights show a
graceful notice.
