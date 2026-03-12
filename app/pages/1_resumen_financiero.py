from __future__ import annotations

import streamlit as st

from utils.loaders import load_facturas_externas
from utils.metrics import (
    kpi_facturacion_total,
    kpi_facturas_totales,
    kpi_monto_impago,
    kpi_facturas_impagas,
)
from utils.charts import (
    chart_facturacion_mensual,
    chart_top_clientes,
    chart_facturacion_por_empresa,
    chart_estado,
)


st.set_page_config(page_title="Resumen Financiero", page_icon="📈", layout="wide")

st.title("Resumen Financiero")
st.caption("Visión ejecutiva de facturación externa")

df = load_facturas_externas().copy()

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

# -----------------------------
# Aplicar filtros
# -----------------------------
df_filtrado = df[
    df["anio"].isin(anios_sel)
    & df["mes_nombre"].isin(meses_sel)
    & df["RAZON_SOCIAL"].isin(empresas_sel)
    & df["ESTADO"].isin(estados_sel)
    & df["CLIENTE"].isin(clientes_sel)
].copy()

if df_filtrado.empty:
    st.warning("No hay datos para la combinación de filtros seleccionada.")
    st.stop()

# -----------------------------
# KPIs
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Facturación externa",
        f"${kpi_facturacion_total(df_filtrado):,.0f}".replace(",", ".")
    )

with col2:
    st.metric(
        "Facturas externas",
        f"{kpi_facturas_totales(df_filtrado):,}".replace(",", ".")
    )

with col3:
    st.metric(
        "Monto impago externo",
        f"${kpi_monto_impago(df_filtrado):,.0f}".replace(",", ".")
    )

with col4:
    st.metric(
        "Facturas impagas externas",
        f"{kpi_facturas_impagas(df_filtrado):,}".replace(",", ".")
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
# Detalle
# -----------------------------
with st.expander("Ver detalle de datos filtrados"):
    st.dataframe(
        df_filtrado[
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
        ],
        width="stretch",
        hide_index=True,
    )