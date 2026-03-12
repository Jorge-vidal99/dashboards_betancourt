from __future__ import annotations

import streamlit as st

from utils.loaders import load_facturas_externas, load_facturas_vencidas, get_last_update_externas
from utils.formatters import (
    format_compact_currency_clp,
    format_number,
    format_datetime_update,
)

st.set_page_config(
    page_title="Dashboard Facturación y Cobranza",
    page_icon="📊",
    layout="wide",
)

st.title("Dashboard de Facturación y Cobranza")
st.caption("Transportes Betancourt | Versión Streamlit")

df_externas = load_facturas_externas()
df_vencidas = load_facturas_vencidas()
last_update = get_last_update_externas()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Facturas externas", format_number(len(df_externas)))

with col2:
    st.metric("Facturas vencidas impagas", format_number(len(df_vencidas)))

with col3:
    st.metric("Monto total externo", format_compact_currency_clp(df_externas["MONTO"].sum()))

with col4:
    st.metric("Última actualización", format_datetime_update(last_update))

st.markdown("---")

st.subheader("Estado de carga")
st.write(f"**Archivo externo cargado:** {'True' if not df_externas.empty else 'False'}")
st.write(f"**Archivo vencidas cargado:** {'True' if not df_vencidas.empty else 'False'}")

st.info("Usa el menú lateral para navegar a **Resumen Financiero** y **Gestión de Cobranza**.")