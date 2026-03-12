from __future__ import annotations

import pandas as pd
import plotly.express as px


COLOR_PRINCIPAL = "#1F4E79"
COLOR_IMPAGO = "#C62828"
COLOR_PAGADA = "#2E7D32"
COLOR_NULA = "#6C757D"

TEMPLATE = "plotly_dark"


def chart_facturacion_mensual(df: pd.DataFrame):
    plot_df = (
        df.groupby("anio_mes", as_index=False)["MONTO"]
        .sum()
        .sort_values("anio_mes")
    )

    fig = px.bar(
        plot_df,
        x="anio_mes",
        y="MONTO",
        title="Evolución de facturación mensual",
        text_auto=".2s",
    )
    fig.update_traces(marker_color=COLOR_PRINCIPAL)
    fig.update_layout(
        xaxis_title="Año-Mes",
        yaxis_title="Monto",
        template=TEMPLATE,
        height=420,
    )
    return fig


def chart_top_clientes(df: pd.DataFrame, top_n: int = 10):
    plot_df = (
        df.groupby("CLIENTE", as_index=False)["MONTO"]
        .sum()
        .sort_values("MONTO", ascending=False)
        .head(top_n)
    )

    fig = px.bar(
        plot_df,
        x="MONTO",
        y="CLIENTE",
        orientation="h",
        title=f"Top {top_n} clientes por facturación",
        text_auto=".2s",
    )
    fig.update_traces(marker_color=COLOR_PRINCIPAL)
    fig.update_layout(
        xaxis_title="Monto",
        yaxis_title="Cliente",
        template=TEMPLATE,
        height=420,
        yaxis={"categoryorder": "total ascending"},
    )
    return fig


def chart_facturacion_por_empresa(df: pd.DataFrame):
    plot_df = (
        df.groupby("RAZON_SOCIAL", as_index=False)["MONTO"]
        .sum()
        .sort_values("MONTO", ascending=False)
    )

    fig = px.bar(
        plot_df,
        x="MONTO",
        y="RAZON_SOCIAL",
        orientation="h",
        title="Facturación por empresa emisora",
        text_auto=".2s",
    )
    fig.update_traces(marker_color=COLOR_PRINCIPAL)
    fig.update_layout(
        xaxis_title="Monto",
        yaxis_title="Razón social",
        template=TEMPLATE,
        height=350,
        yaxis={"categoryorder": "total ascending"},
    )
    return fig


def chart_estado(df: pd.DataFrame):
    plot_df = (
        df.groupby("ESTADO", as_index=False)["MONTO"]
        .sum()
        .sort_values("MONTO", ascending=False)
    )

    color_map = {
        "IMPAGA": COLOR_IMPAGO,
        "PAGADA": COLOR_PAGADA,
        "NULA": COLOR_NULA,
    }

    fig = px.pie(
        plot_df,
        names="ESTADO",
        values="MONTO",
        title="Distribución por estado",
        color="ESTADO",
        color_discrete_map=color_map,
        hole=0.45,
    )
    fig.update_layout(
        template=TEMPLATE,
        height=350,
    )
    return fig


def chart_top_clientes_morosos(df: pd.DataFrame, top_n: int = 10):
    plot_df = (
        df.groupby("CLIENTE", as_index=False)["MONTO"]
        .sum()
        .sort_values("MONTO", ascending=False)
        .head(top_n)
    )

    fig = px.bar(
        plot_df,
        x="MONTO",
        y="CLIENTE",
        orientation="h",
        title=f"Top {top_n} clientes con deuda",
        text_auto=".2s",
    )
    fig.update_traces(marker_color=COLOR_IMPAGO)
    fig.update_layout(
        xaxis_title="Monto impago",
        yaxis_title="Cliente",
        template=TEMPLATE,
        height=420,
        yaxis={"categoryorder": "total ascending"},
    )
    return fig


def chart_aging_deuda(df: pd.DataFrame):
    plot_df = df.copy()

    bins = [-1, 30, 60, 90, 99999]
    labels = ["0-30", "31-60", "61-90", "90+"]

    plot_df["rango_aging"] = pd.cut(
        plot_df["DIAS_TRANSCURRIDOS"],
        bins=bins,
        labels=labels
    )

    plot_df = (
        plot_df.groupby("rango_aging", as_index=False, observed=False)["MONTO"]
        .sum()
    )

    total = plot_df["MONTO"].sum()

    if total > 0:
        plot_df["PORCENTAJE"] = plot_df["MONTO"] / total
    else:
        plot_df["PORCENTAJE"] = 0

    plot_df["ETIQUETA"] = plot_df.apply(
        lambda row: f"{row['MONTO']/1_000_000:.1f}M ({row['PORCENTAJE']*100:.1f}%)",
        axis=1
    )

    color_map = {
        "0-30": "#F4A261",
        "31-60": "#E76F51",
        "61-90": "#D62828",
        "90+": "#9B2226",
    }

    fig = px.bar(
        plot_df,
        x="rango_aging",
        y="MONTO",
        title="Aging de deuda",
        text="ETIQUETA",
        color="rango_aging",
        color_discrete_map=color_map,
    )

    fig.update_layout(
        xaxis_title="Rango de días",
        yaxis_title="Monto impago",
        template=TEMPLATE,
        height=350,
        showlegend=False,
    )

    fig.update_traces(textposition="outside")
    return fig


def chart_deuda_por_empresa(df: pd.DataFrame):
    plot_df = (
        df.groupby("RAZON_SOCIAL", as_index=False)["MONTO"]
        .sum()
        .sort_values("MONTO", ascending=False)
    )

    fig = px.bar(
        plot_df,
        x="MONTO",
        y="RAZON_SOCIAL",
        orientation="h",
        title="Deuda por empresa emisora",
        text_auto=".2s",
    )
    fig.update_traces(marker_color=COLOR_IMPAGO)
    fig.update_layout(
        xaxis_title="Monto impago",
        yaxis_title="Razón social",
        template=TEMPLATE,
        height=350,
        yaxis={"categoryorder": "total ascending"},
    )
    return fig