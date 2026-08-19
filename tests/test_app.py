import os
os.environ["AI_ENABLED"] = "false"  # offline path for tests

import pandas as pd
import matplotlib
matplotlib.use("Agg")

from app import make_chart, ai_insights


def test_make_chart_returns_png():
    df = pd.DataFrame({"amount": [1, 2, 2, 3, 3, 3, 4]})
    png = make_chart(df, "amount")
    assert isinstance(png, bytes)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic


def test_ai_insights_offline_notice():
    df = pd.DataFrame({"amount": [1, 2, 3]})
    out = ai_insights(df, "amount")
    assert "disabled" in out.lower()
