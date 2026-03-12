from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.loaders import load_facturas_externas, get_last_update_externas
from utils.metrics import (
    kpi_facturacion_total,
    kpi_facturas_totales,
    kpi_monto_impago,
    kpi_facturas_impagas,
    kpi_tasa_mora,
)
from utils.charts import (
    chart_facturacion_mensual,
    chart_top_clientes,
    chart_facturacion_por_empresa,
    chart_estado,
)
from utils.formatters import (
    format_compact_currency_clp,
    format_currency_clp,
    format_number,
    format_date_ddmmyyyy,
    format_datetime_update,
    format_percent
)

st.set_page_config(page_title="Resumen Financiero", page_icon="📈", layout="wide")

st.title("Resumen Financiero")
st.caption("Visión ejecutiva de facturación externa")

df = load_facturas_externas().copy()
last_update = get_last_update_externas()

# -----------------------------
# Filtros
# -----------------------------
with st.sidebar:
    st.header("Filtros")

    anios = sorted(df["anio"].dropna().astype(int).unique().tolist())
    anios_sel = st.multiselect("Año", anios, default=anios)

    meses_ordenados = (
        df[["mes_num", "mes_nombre"]]
        .drop_duplicates()
        .sort_values("mes_num")
    )
    meses = meses_ordenados["mes_nombre"].tolist()
    meses_sel = st.multiselect("Mes", meses, default=meses)

    empresas = sorted(df["RAZON_SOCIAL"].dropna().unique().tolist())
    empresas_sel = st.multiselect("Razón social", empresas, default=empresas)

    estados = sorted(df["ESTADO"].dropna().unique().tolist())
    estados_sel = st.multiselect("Estado", estados, default=estados)

    clientes = sorted(df["CLIENTE"].dropna().unique().tolist())
    clientes_sel = st.multiselect("Cliente", clientes, default=clientes)

# Aplicar filtros
df_filtrado = df[
    df["anio"].isin(anios_sel)
    & df["mes_nombre"].isin(meses_sel)
    & df["RAZON_SOCIAL"].isin(empresas_sel)
    & df["ESTADO"].isin(estados_sel)
    & df["CLIENTE"].isin(clientes_sel)
].copy()

# -----------------------------
# Encabezado ejecutivo
# -----------------------------
col_info_1, col_info_2 = st.columns([2, 1])

with col_info_1:
    st.markdown("**Sistema de Facturación y Cobranza | Transportes Betancourt**")

with col_info_2:
    st.markdown(
        f"**Última actualización:** {format_datetime_update(last_update)}"
    )

# -----------------------------
# KPIs
# -----------------------------
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Facturación externa",
        format_compact_currency_clp(kpi_facturacion_total(df_filtrado))
    )

with col2:
    st.metric(
        "Facturas externas",
        format_number(kpi_facturas_totales(df_filtrado))
    )

with col3:
    st.metric(
        "Monto impago externo",
        format_compact_currency_clp(kpi_monto_impago(df_filtrado))
    )

with col4:
    st.metric(
        "Facturas impagas externas",
        format_number(kpi_facturas_impagas(df_filtrado))
    )
with col5:
    st.metric(
        "Tasa de mora",
        format_percent(kpi_tasa_mora(df_filtrado))
    )   

st.markdown("---")

# -----------------------------
# Gráficos
# -----------------------------
col_g1, col_g2 = st.columns([1.6, 1])

with col_g1:
    fig_mensual = chart_facturacion_mensual(df_filtrado)
    st.plotly_chart(fig_mensual, width="stretch")

with col_g2:
    fig_estado = chart_estado(df_filtrado)
    st.plotly_chart(fig_estado, width="stretch")

col_g3, col_g4 = st.columns([1.3, 1])

with col_g3:
    fig_clientes = chart_top_clientes(df_filtrado, top_n=10)
    st.plotly_chart(fig_clientes, width="stretch")

with col_g4:
    fig_empresa = chart_facturacion_por_empresa(df_filtrado)
    st.plotly_chart(fig_empresa, width="stretch")

st.markdown("---")

# -----------------------------
# Tabla detalle
# -----------------------------
with st.expander("Ver detalle de datos filtrados"):
    detalle = df_filtrado[
        [
            "N_FACTURA",
            "FECHA_EMISION",
            "CLIENTE",
            "RUT",
            "CARGA_O_CONCEPTO",
            "MONTO",
            "ESTADO",
            "RAZON_SOCIAL",
            "DIAS_TRANSCURRIDOS",
        ]
    ].copy()

    detalle["FECHA_EMISION"] = format_date_ddmmyyyy(detalle["FECHA_EMISION"])
    detalle["MONTO"] = detalle["MONTO"].apply(format_currency_clp)
    detalle["DIAS_TRANSCURRIDOS"] = detalle["DIAS_TRANSCURRIDOS"].apply(format_number)

    st.dataframe(
        detalle,
        width="stretch",
        hide_index=True,
    )