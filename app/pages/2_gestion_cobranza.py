from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.loaders import (
    load_facturas_externas,
    load_facturas_vencidas,
    get_last_update_vencidas,
)
from utils.metrics import (
    kpi_monto_impago,
    kpi_facturas_impagas,
    kpi_clientes_con_deuda,
    kpi_monto_vencido,
)
from utils.charts import (
    chart_top_clientes_morosos,
    chart_deuda_por_empresa,
    chart_aging_deuda,
)
from utils.formatters import (
    format_compact_currency_clp,
    format_currency_clp,
    format_number,
    format_date_ddmmyyyy,
    format_datetime_update,
)

st.set_page_config(page_title="Gestión de Cobranza", page_icon="💳", layout="wide")

st.title("Gestión de Cobranza")
st.caption("Seguimiento de deuda y facturas vencidas")

df_externas = load_facturas_externas().copy()
df_vencidas = load_facturas_vencidas().copy()
last_update = get_last_update_vencidas()

# -----------------------------
# Filtros
# -----------------------------
with st.sidebar:
    st.header("Filtros")

    anios = sorted(df_externas["anio"].dropna().astype(int).unique().tolist())
    anios_sel = st.multiselect("Año", anios, default=anios, key="cobranza_anio")

    meses_ordenados = (
        df_externas[["mes_num", "mes_nombre"]]
        .drop_duplicates()
        .sort_values("mes_num")
    )
    meses = meses_ordenados["mes_nombre"].tolist()
    meses_sel = st.multiselect("Mes", meses, default=meses, key="cobranza_mes")

    empresas = sorted(df_externas["RAZON_SOCIAL"].dropna().unique().tolist())
    empresas_sel = st.multiselect(
        "Razón social",
        empresas,
        default=empresas,
        key="cobranza_empresa"
    )

    clientes = sorted(df_externas["CLIENTE"].dropna().unique().tolist())
    clientes_sel = st.multiselect(
        "Cliente",
        clientes,
        default=clientes,
        key="cobranza_cliente"
    )

# -----------------------------
# Aplicar filtros
# -----------------------------
df_filtrado = df_externas[
    df_externas["anio"].isin(anios_sel)
    & df_externas["mes_nombre"].isin(meses_sel)
    & df_externas["RAZON_SOCIAL"].isin(empresas_sel)
    & df_externas["CLIENTE"].isin(clientes_sel)
].copy()

df_vencidas_filtrado = df_vencidas[
    df_vencidas["anio"].isin(anios_sel)
    & df_vencidas["mes_nombre"].isin(meses_sel)
    & df_vencidas["RAZON_SOCIAL"].isin(empresas_sel)
    & df_vencidas["CLIENTE"].isin(clientes_sel)
].copy()

# Para el aging: todas las IMPAGAS, incluyendo las no vencidas
df_impagas_filtrado = df_filtrado[
    df_filtrado["ESTADO"] == "IMPAGA"
].copy()

if df_filtrado.empty:
    st.warning("No hay datos para la combinación de filtros seleccionada.")
    st.stop()

# -----------------------------
# Encabezado ejecutivo
# -----------------------------
col_info_1, col_info_2 = st.columns([2, 1])

with col_info_1:
    st.markdown("**Sistema de Facturación y Cobranza | Módulo de Gestión de Cobranza**")

with col_info_2:
    st.markdown(
        f"**Última actualización:** {format_datetime_update(last_update)}"
    )

# -----------------------------
# KPIs
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Monto impago",
        format_compact_currency_clp(kpi_monto_impago(df_filtrado))
    )

with col2:
    st.metric(
        "Facturas impagas",
        format_number(kpi_facturas_impagas(df_filtrado))
    )

with col3:
    st.metric(
        "Clientes con deuda",
        format_number(kpi_clientes_con_deuda(df_filtrado))
    )

with col4:
    st.metric(
        "Monto vencido > 30 días",
        format_compact_currency_clp(kpi_monto_vencido(df_vencidas_filtrado))
    )

st.markdown("---")

# -----------------------------
# Gráficos
# -----------------------------
col_g1, col_g2 = st.columns([1.1, 1])

with col_g1:
    fig_morosos = chart_top_clientes_morosos(df_vencidas_filtrado, top_n=10)
    st.plotly_chart(fig_morosos, width="stretch")

with col_g2:
    st.subheader("Aging de facturas impagas")

    df_aging = df_impagas_filtrado.copy()

    bins = [-1, 30, 60, 90, 99999]
    labels = ["0-30", "31-60", "61-90", "90+"]

    df_aging["rango_aging"] = pd.cut(
        df_aging["DIAS_TRANSCURRIDOS"],
        bins=bins,
        labels=labels
    )

    df_aging = (
        df_aging.groupby("rango_aging", as_index=False)["MONTO"]
        .sum()
    )

    fig_aging = chart_aging_deuda(df_aging)
    st.plotly_chart(fig_aging, width="stretch")

col_g3, col_g4 = st.columns([1.2, 1])

with col_g3:
    fig_empresa = chart_deuda_por_empresa(df_vencidas_filtrado)
    st.plotly_chart(fig_empresa, width="stretch")

with col_g4:
    st.subheader("Resumen rápido")
    st.write(f"**Registros vencidos:** {format_number(len(df_vencidas_filtrado))}")
    st.write(
        f"**Monto promedio por factura vencida:** "
        f"{format_currency_clp(df_vencidas_filtrado['MONTO'].mean())}"
        if not df_vencidas_filtrado.empty
        else "$0"
    )
    st.write(
        f"**Máxima antigüedad:** "
        f"{format_number(df_vencidas_filtrado['DIAS_TRANSCURRIDOS'].max())} días"
        if not df_vencidas_filtrado.empty
        else "0 días"
    )

st.markdown("---")

# -----------------------------
# Tabla detalle
# -----------------------------
st.subheader("Detalle de facturas impagas vencidas")

detalle = df_vencidas_filtrado[
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
    detalle.sort_values(["DIAS_TRANSCURRIDOS"], ascending=[False]),
    width="stretch",
    hide_index=True,
)