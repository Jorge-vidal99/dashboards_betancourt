from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from utils.loaders import (
    load_facturas_externas,
    load_facturas_vencidas,
    load_facturas_intercompany,
    get_last_update_externas,
)
from utils.metrics import (
    kpi_facturacion_total,
    kpi_monto_impago,
    kpi_tasa_mora,
)
from utils.charts import (
    chart_facturacion_mensual,
    chart_estado,
)
from utils.formatters import (
    format_compact_currency_clp,
    format_currency_clp,
    format_number,
    format_datetime_update,
    format_percent,
)

st.set_page_config(
    page_title="Dashboard Facturación y Cobranza",
    page_icon="📊",
    layout="wide",
)

# -----------------------------
# Header con logo (si existe)
# -----------------------------
LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "logo.png"

col_logo, col_title = st.columns([1, 5])

if LOGO_PATH.exists():
    with col_logo:
        st.image(str(LOGO_PATH), use_container_width=True)
    with col_title:
        st.title("Dashboard de Facturación y Cobranza")
        st.caption("Transportes Betancourt")
else:
    st.title("Dashboard de Facturación y Cobranza")
    st.caption("Transportes Betancourt")

# -----------------------------
# Carga de datos
# -----------------------------
last_update = get_last_update_externas()

df_externas = load_facturas_externas(_mtime=last_update)
df_vencidas = load_facturas_vencidas(_mtime=last_update)
df_intercompany = load_facturas_intercompany(_mtime=last_update)

# -----------------------------
# KPIs (6)
# -----------------------------
st.markdown("### Indicadores principales")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Facturas externas", format_number(len(df_externas)))

with col2:
    st.metric("Facturas vencidas impagas", format_number(len(df_vencidas)))

with col3:
    st.metric(
        "Monto total externo",
        format_compact_currency_clp(kpi_facturacion_total(df_externas)),
    )

col4, col5, col6 = st.columns(3)

with col4:
    st.metric(
        "Monto impago externo",
        format_compact_currency_clp(kpi_monto_impago(df_externas)),
    )

with col5:
    st.metric(
        "Tasa de mora",
        format_percent(kpi_tasa_mora(df_externas)),
    )

with col6:
    st.metric("Última actualización", format_datetime_update(last_update))

# KPI complementario intercompany
monto_intercompany = (
    kpi_facturacion_total(df_intercompany) if not df_intercompany.empty else 0
)
st.caption(
    f"Monto intercompany informativo: **{format_compact_currency_clp(monto_intercompany)}** "
    f"({format_number(len(df_intercompany))} facturas)"
)

st.markdown("---")

# -----------------------------
# Gráficos resumen
# -----------------------------
col_g1, col_g2 = st.columns([1.6, 1])

with col_g1:
    fig_mensual = chart_facturacion_mensual(df_externas)
    st.plotly_chart(fig_mensual, use_container_width=True)

with col_g2:
    fig_estado = chart_estado(df_externas)
    st.plotly_chart(fig_estado, use_container_width=True)

st.markdown("---")

# -----------------------------
# Top 5 clientes con mayor deuda vencida
# -----------------------------
st.markdown("### Top 5 clientes con mayor deuda vencida")

if df_vencidas.empty:
    st.info("No hay facturas vencidas impagas registradas.")
else:
    top5 = (
        df_vencidas.groupby("CLIENTE", as_index=False)
        .agg(
            MONTO_VENCIDO=("MONTO", "sum"),
            FACTURAS=("MONTO", "size"),
            MAX_DIAS=("DIAS_TRANSCURRIDOS", "max"),
        )
        .sort_values("MONTO_VENCIDO", ascending=False)
        .head(5)
    )

    top5_display = top5.copy()
    top5_display["MONTO_VENCIDO"] = top5_display["MONTO_VENCIDO"].apply(format_currency_clp)
    top5_display["FACTURAS"] = top5_display["FACTURAS"].apply(format_number)
    top5_display["MAX_DIAS"] = top5_display["MAX_DIAS"].apply(
        lambda x: f"{format_number(x)} días"
    )
    top5_display = top5_display.rename(
        columns={
            "CLIENTE": "Cliente",
            "MONTO_VENCIDO": "Monto vencido",
            "FACTURAS": "Facturas",
            "MAX_DIAS": "Máx. antigüedad",
        }
    )

    st.dataframe(top5_display, use_container_width=True, hide_index=True)

st.info("Usa el menú lateral para navegar a **Resumen Financiero** y **Gestión de Cobranza**.")
