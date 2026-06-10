from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.loaders import (
    load_facturas_externas,
    load_facturas_vencidas,
    get_last_update_externas,
    get_last_update_vencidas,
)
from utils.metrics import (
    kpi_monto_impago,
    kpi_facturas_impagas,
    kpi_clientes_con_deuda,
    kpi_monto_vencido,
    resumen_riesgo_clientes,
)
from utils.charts import (
    chart_top_clientes_morosos,
    chart_deuda_por_empresa,
    chart_aging_deuda,
    chart_resumen_riesgo_clientes,
    chart_top_clientes_criticos,
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

# FIX CACHÉ: mtime invalida caché automáticamente cuando cambia el parquet
last_update = get_last_update_vencidas()
df_externas = load_facturas_externas(_mtime=get_last_update_externas()).copy()
df_vencidas = load_facturas_vencidas(_mtime=last_update).copy()

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
        "Razón social", empresas, default=empresas, key="cobranza_empresa"
    )

    clientes = sorted(df_externas["CLIENTE"].dropna().unique().tolist())
    clientes_sel = st.multiselect(
        "Cliente", clientes, default=clientes, key="cobranza_cliente"
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

df_impagas_filtrado = df_filtrado[df_filtrado["ESTADO"] == "IMPAGA"].copy()

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
    st.markdown(f"**Última actualización:** {format_datetime_update(last_update)}")

# -----------------------------
# KPIs
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Monto impago", format_compact_currency_clp(kpi_monto_impago(df_filtrado)))

with col2:
    st.metric("Facturas impagas", format_number(kpi_facturas_impagas(df_filtrado)))

with col3:
    st.metric("Clientes con deuda", format_number(kpi_clientes_con_deuda(df_filtrado)))

with col4:
    st.metric(
        "Monto vencido > 30 días",
        format_compact_currency_clp(kpi_monto_vencido(df_vencidas_filtrado)),
    )

st.markdown("---")

# -----------------------------
# Gráficos principales
# -----------------------------
col_g1, col_g2 = st.columns([1.1, 1])

with col_g1:
    fig_morosos = chart_top_clientes_morosos(df_vencidas_filtrado, top_n=10)
    st.plotly_chart(fig_morosos, use_container_width=True)

with col_g2:
    st.subheader("Aging de facturas impagas")
    fig_aging = chart_aging_deuda(df_impagas_filtrado.copy())
    st.plotly_chart(fig_aging, use_container_width=True)

fig_empresa = chart_deuda_por_empresa(df_vencidas_filtrado)
st.plotly_chart(fig_empresa, use_container_width=True)

st.markdown("---")

# -----------------------------
# Semáforo de riesgo de clientes
# -----------------------------
st.subheader("Semáforo de riesgo de clientes")

df_riesgo = resumen_riesgo_clientes(df_filtrado)

col_r1, col_r2 = st.columns([1, 1.2])

with col_r1:
    fig_riesgo = chart_resumen_riesgo_clientes(df_riesgo)
    st.plotly_chart(fig_riesgo, use_container_width=True)

with col_r2:
    fig_criticos = chart_top_clientes_criticos(df_riesgo, top_n=10)
    st.plotly_chart(fig_criticos, use_container_width=True)

if not df_riesgo.empty:
    st.markdown("### Detalle de clientes por riesgo")

    riesgo_detalle = df_riesgo[
        [
            "CLIENTE",
            "MONTO_FACTURADO",
            "MONTO_IMPAGO",
            "FACTURAS_IMPAGAS",
            "MAX_DIAS",
            "TASA_IMPAGO",
            "ICONO_RIESGO",
        ]
    ].copy()

    riesgo_detalle["MONTO_FACTURADO"] = riesgo_detalle["MONTO_FACTURADO"].apply(format_currency_clp)
    riesgo_detalle["MONTO_IMPAGO"] = riesgo_detalle["MONTO_IMPAGO"].apply(format_currency_clp)
    riesgo_detalle["FACTURAS_IMPAGAS"] = riesgo_detalle["FACTURAS_IMPAGAS"].apply(format_number)
    riesgo_detalle["MAX_DIAS"] = riesgo_detalle["MAX_DIAS"].apply(
        lambda x: f"{format_number(x)} días"
    )
    riesgo_detalle["TASA_IMPAGO"] = riesgo_detalle["TASA_IMPAGO"].apply(
        lambda x: f"{x * 100:.2f}%".replace(".", ",")
    )

    st.dataframe(riesgo_detalle, use_container_width=True, hide_index=True)

st.markdown("---")

# -----------------------------
# Tabla detalle de vencidas
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

# Ordenar ANTES de formatear para que el ordenamiento sea numérico
detalle = detalle.sort_values(["DIAS_TRANSCURRIDOS"], ascending=[False])


def _clasificar_urgencia(dias):
    if pd.isna(dias):
        return ""
    if dias > 90:
        return "🔴 Crítico"
    if dias > 60:
        return "🟡 Alerta"
    if dias > 30:
        return "🟠 Atención"
    return ""


detalle["URGENCIA"] = detalle["DIAS_TRANSCURRIDOS"].apply(_clasificar_urgencia)

detalle["FECHA_EMISION"] = format_date_ddmmyyyy(detalle["FECHA_EMISION"])
detalle["MONTO"] = detalle["MONTO"].apply(format_currency_clp)
detalle["DIAS_TRANSCURRIDOS"] = detalle["DIAS_TRANSCURRIDOS"].apply(format_number)

st.dataframe(
    detalle,
    use_container_width=True,
    hide_index=True,
)
