from __future__ import annotations

import pandas as pd


def format_currency_clp(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "$0"
    return f"${value:,.0f}".replace(",", ".")


def format_compact_currency_clp(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "$0"

    value = float(value)
    abs_value = abs(value)

    if abs_value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B".replace(".", ",")
    if abs_value >= 1_000_000:
        return f"${value / 1_000_000:.1f}MM".replace(".", ",")
    if abs_value >= 1_000:
        return f"${value / 1_000:.1f}K".replace(".", ",")

    return f"${value:,.0f}".replace(",", ".")


def format_number(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "0"
    return f"{int(value):,}".replace(",", ".")


def format_date_ddmmyyyy(series: pd.Series) -> pd.Series:
    s = pd.to_datetime(series, errors="coerce")
    return s.dt.strftime("%d-%m-%Y")


def format_datetime_update(value) -> str:
    if value is None or pd.isna(value):
        return "-"

    ts = pd.to_datetime(value, unit="s", errors="coerce")

    if pd.isna(ts):
        return "-"

    return ts.strftime("%d-%m-%Y %H:%M")

def format_percent(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "0,00%"
    return f"{value * 100:.2f}%".replace(".", ",")