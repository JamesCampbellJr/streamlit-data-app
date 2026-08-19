"""Streamlit data-app template: CSV upload -> stats + chart + AI insights.

Runs fully offline (charts/stats) and adds AI insights only when enabled.
"""
from __future__ import annotations

import io
import os

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

from ai_client import complete, ai_enabled


def make_chart(df: pd.DataFrame, numeric_col: str) -> bytes:
    fig, ax = plt.subplots()
    ax.hist(df[numeric_col].dropna(), bins=20, color="#4C78A8")
    ax.set_title(f"Distribution of {numeric_col}")
    ax.set_ylabel("count")
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()


def ai_insights(df: pd.DataFrame, numeric_col: str) -> str:
    if not ai_enabled():
        return "(AI insights disabled — set AI_ENABLED=true and provide AI_API_KEY.)"
    stats = df[numeric_col].describe().to_dict()
    prompt = (
        f"Given these summary stats for column '{numeric_col}': {stats}. "
        "Write 2-3 short, plain-English insights a business owner would care about."
    )
    res = complete(prompt, system="You are a concise data analyst.")
    return res.text if res.ok else f"(AI error: {res.error})"


def main():
    st.set_page_config(page_title="AI-Company Data App", layout="wide")
    st.title("AI-Company Data App")
    st.caption("Upload a CSV to explore and summarize your data.")

    uploaded = st.file_uploader("Choose a CSV", type="csv")
    if uploaded is None:
        st.info("Upload a CSV to begin.")
        return

    df = pd.read_csv(uploaded)
    st.write("Preview", df.head())
    st.write("Shape", df.shape)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        st.warning("No numeric columns found for charting.")
        return

    col = st.selectbox("Pick a numeric column", numeric_cols)
    st.image(make_chart(df, col), caption=f"Distribution of {col}")
    st.subheader("AI Insights")
    with st.spinner("Generating insights..."):
        st.write(ai_insights(df, col))


if __name__ == "__main__":
    main()
