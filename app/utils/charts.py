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


def chart_resumen_riesgo_clientes(df_resumen: pd.DataFrame):
    if df_resumen.empty:
        return px.bar(title="Clientes por nivel de riesgo")

    plot_df = (
        df_resumen.groupby("NIVEL_RIESGO", as_index=False)
        .agg(
            CLIENTES=("CLIENTE", "nunique"),
            MONTO_IMPAGO=("MONTO_IMPAGO", "sum"),
        )
    )

    orden = ["Alto", "Medio", "Bajo"]
    plot_df["NIVEL_RIESGO"] = pd.Categorical(
        plot_df["NIVEL_RIESGO"],
        categories=orden,
        ordered=True
    )
    plot_df = plot_df.sort_values("NIVEL_RIESGO")

    color_map = {
        "Alto": "#D62828",
        "Medio": "#F4A261",
        "Bajo": "#2E7D32",
    }

    plot_df["ETIQUETA"] = plot_df.apply(
        lambda row: f"{int(row['CLIENTES'])} clientes | ${row['MONTO_IMPAGO']/1_000_000:.1f}M",
        axis=1
    )

    fig = px.bar(
        plot_df,
        x="NIVEL_RIESGO",
        y="CLIENTES",
        color="NIVEL_RIESGO",
        color_discrete_map=color_map,
        title="Clientes por nivel de riesgo",
        text="ETIQUETA",
    )

    fig.update_layout(
        xaxis_title="Nivel de riesgo",
        yaxis_title="Cantidad de clientes",
        template=TEMPLATE,
        height=350,
        showlegend=False,
    )
    fig.update_traces(textposition="outside")
    return fig


def chart_top_clientes_criticos(df_resumen: pd.DataFrame, top_n: int = 10):
    if df_resumen.empty:
        return px.bar(title="Top clientes críticos")

    plot_df = (
        df_resumen[df_resumen["NIVEL_RIESGO"] == "Alto"]
        .sort_values("MONTO_IMPAGO", ascending=False)
        .head(top_n)
    )

    if plot_df.empty:
        return px.bar(title="Top clientes críticos")

    fig = px.bar(
        plot_df,
        x="MONTO_IMPAGO",
        y="CLIENTE",
        orientation="h",
        title=f"Top {top_n} clientes críticos",
        text_auto=".2s",
    )

    fig.update_traces(marker_color="#D62828")
    fig.update_layout(
        xaxis_title="Monto impago",
        yaxis_title="Cliente",
        template=TEMPLATE,
        height=420,
        yaxis={"categoryorder": "total ascending"},
    )
    return fig