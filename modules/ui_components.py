"""Shared Streamlit UI components."""

from __future__ import annotations

import html

import streamlit as st


def inject_base_styles() -> None:
    st.markdown(
        """
        <style>
        .vandabi-card {
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 18px 18px 16px;
            background: #ffffff;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
            min-height: 132px;
        }
        .vandabi-card h3 {
            font-size: 1.02rem;
            margin: 0 0 8px;
            color: #102a43;
        }
        .vandabi-card p {
            font-size: 0.92rem;
            line-height: 1.55;
            color: #334e68;
            margin: 0;
        }
        .vandabi-metric {
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 14px 16px;
            background: #f8fbff;
        }
        .vandabi-metric .label {
            font-size: 0.82rem;
            color: #52606d;
            margin-bottom: 4px;
        }
        .vandabi-metric .value {
            font-size: 1.45rem;
            font-weight: 700;
            color: #102a43;
        }
        .vandabi-box {
            border-radius: 8px;
            padding: 14px 16px;
            margin: 8px 0;
            line-height: 1.55;
        }
        .vandabi-box.info {
            border: 1px solid #9fb3c8;
            background: #f0f7ff;
            color: #102a43;
        }
        .vandabi-box.warning {
            border: 1px solid #f7c948;
            background: #fffbea;
            color: #513c06;
        }
        .vandabi-badge {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.78rem;
            font-weight: 700;
            background: #e6f6ff;
            color: #0b4f71;
            border: 1px solid #bae3ff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, description: str = "") -> None:
    st.subheader(title)
    if description:
        st.caption(description)


def metric_card(label: str, value: str | int | float, help_text: str = "") -> None:
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))
    safe_help = html.escape(str(help_text))
    st.markdown(
        f"""
        <div class="vandabi-metric">
            <div class="label">{safe_label}</div>
            <div class="value">{safe_value}</div>
            <div>{safe_help}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_box(message: str) -> None:
    st.markdown(
        f'<div class="vandabi-box info">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def warning_box(message: str) -> None:
    st.markdown(
        f'<div class="vandabi-box warning">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def status_badge(label: str) -> None:
    st.markdown(
        f'<span class="vandabi-badge">{html.escape(label)}</span>',
        unsafe_allow_html=True,
    )


def feature_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="vandabi-card">
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
