from __future__ import annotations

import streamlit as st
from utils.loaders import load_facturas_externas, load_facturas_vencidas


st.set_page_config(
    page_title="Dashboard Facturación y Cobranza",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Dashboard de Facturación y Cobranza")
st.caption("Transportes Betancourt | Versión Streamlit")

# Carga mínima para validar que todo funciona
df_externas = load_facturas_externas()
df_vencidas = load_facturas_vencidas()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Facturas externas", f"{len(df_externas):,}".replace(",", "."))

with col2:
    st.metric("Facturas vencidas impagas", f"{len(df_vencidas):,}".replace(",", "."))

with col3:
    monto_total = df_externas["MONTO"].sum()
    st.metric("Monto total externo", f"${monto_total:,.0f}".replace(",", "."))

st.markdown("---")
st.subheader("Estado de carga")

st.write("**Archivo externo cargado:**", not df_externas.empty)
st.write("**Archivo vencidas cargado:**", not df_vencidas.empty)

st.info(
    "Usa el menú lateral de páginas para navegar a "
    "**Resumen Financiero** y **Gestión de Cobranza**."
)