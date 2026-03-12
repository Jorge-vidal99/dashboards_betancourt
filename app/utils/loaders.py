from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


# -------------------------------
# Ruta base del proyecto
# -------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data_processed"


# -------------------------------
# Meses en español
# -------------------------------
MESES_ES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


# -------------------------------
# Preparación de columnas
# -------------------------------
def _prepare_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "FECHA_EMISION" in df.columns:
        df["FECHA_EMISION"] = pd.to_datetime(df["FECHA_EMISION"], errors="coerce")
        df["anio"] = df["FECHA_EMISION"].dt.year.astype("Int64")
        df["mes_num"] = df["FECHA_EMISION"].dt.month.astype("Int64")
        df["mes_nombre"] = df["mes_num"].map(MESES_ES)
        df["anio_mes"] = df["FECHA_EMISION"].dt.strftime("%Y-%m")

    if "MONTO" in df.columns:
        df["MONTO"] = pd.to_numeric(df["MONTO"], errors="coerce").fillna(0)

    if "DIAS_TRANSCURRIDOS" in df.columns:
        df["DIAS_TRANSCURRIDOS"] = pd.to_numeric(
            df["DIAS_TRANSCURRIDOS"], errors="coerce"
        )

    return df


# -------------------------------
# Loaders principales
# -------------------------------
@st.cache_data(show_spinner=False)
def load_facturas_externas() -> pd.DataFrame:
    path = DATA_DIR / "facturas_externas.parquet"
    df = pd.read_parquet(path)
    return _prepare_dates(df)


@st.cache_data(show_spinner=False)
def load_facturas_vencidas() -> pd.DataFrame:
    path = DATA_DIR / "facturas_vencidas_impagas.parquet"
    df = pd.read_parquet(path)
    return _prepare_dates(df)


@st.cache_data(show_spinner=False)
def load_facturas_intercompany() -> pd.DataFrame:
    path = DATA_DIR / "facturas_intercompany.parquet"
    df = pd.read_parquet(path)
    return _prepare_dates(df)


@st.cache_data(show_spinner=False)
def load_facturas_consolidadas() -> pd.DataFrame:
    path = DATA_DIR / "facturas_consolidadas_todas.parquet"
    df = pd.read_parquet(path)
    return _prepare_dates(df)


# -------------------------------
# Utilidades de actualización
# -------------------------------
def clear_cache() -> None:
    st.cache_data.clear()


def get_data_file_timestamp(file_name: str):
    path = DATA_DIR / file_name
    if not path.exists():
        return None
    return path.stat().st_mtime


def get_last_update_externas():
    return get_data_file_timestamp("facturas_externas.parquet")


def get_last_update_vencidas():
    return get_data_file_timestamp("facturas_vencidas_impagas.parquet")