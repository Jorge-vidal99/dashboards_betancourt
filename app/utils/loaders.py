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
# Utilidades de timestamp
# -------------------------------
def get_data_file_timestamp(file_name: str) -> float:
    path = DATA_DIR / file_name
    if not path.exists():
        return 0.0
    return path.stat().st_mtime


def get_last_update_externas() -> float:
    return get_data_file_timestamp("facturas_externas.parquet")


def get_last_update_vencidas() -> float:
    return get_data_file_timestamp("facturas_vencidas_impagas.parquet")


# -------------------------------
# Loaders principales
# FIX CACHÉ: el parámetro _mtime actúa como clave de caché.
# Cuando el archivo cambia → mtime cambia → Streamlit recarga los datos.
# El guion bajo (_mtime) le dice a Streamlit que NO hashee el valor,
# sino que lo use directamente como discriminador de caché.
# -------------------------------
@st.cache_data(show_spinner=False)
def load_facturas_externas(_mtime: float = 0.0) -> pd.DataFrame:
    path = DATA_DIR / "facturas_externas.parquet"
    if not path.exists():
        st.error(f"No se encontró archivo: {path}")
        return pd.DataFrame()
    try:
        df = pd.read_parquet(path)
        return _prepare_dates(df)
    except Exception as e:
        st.error(f"Error cargando {path}: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_facturas_vencidas(_mtime: float = 0.0) -> pd.DataFrame:
    path = DATA_DIR / "facturas_vencidas_impagas.parquet"
    if not path.exists():
        st.error(f"No se encontró archivo: {path}")
        return pd.DataFrame()
    try:
        df = pd.read_parquet(path)
        return _prepare_dates(df)
    except Exception as e:
        st.error(f"Error cargando {path}: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_facturas_intercompany(_mtime: float = 0.0) -> pd.DataFrame:
    path = DATA_DIR / "facturas_intercompany.parquet"
    if not path.exists():
        st.error(f"No se encontró archivo: {path}")
        return pd.DataFrame()
    try:
        df = pd.read_parquet(path)
        return _prepare_dates(df)
    except Exception as e:
        st.error(f"Error cargando {path}: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_facturas_consolidadas(_mtime: float = 0.0) -> pd.DataFrame:
    path = DATA_DIR / "facturas_consolidadas_todas.parquet"
    if not path.exists():
        st.error(f"No se encontró archivo: {path}")
        return pd.DataFrame()
    try:
        df = pd.read_parquet(path)
        return _prepare_dates(df)
    except Exception as e:
        st.error(f"Error cargando {path}: {e}")
        return pd.DataFrame()


# -------------------------------
# Utilidad para limpiar caché manualmente
# -------------------------------
def clear_cache() -> None:
    st.cache_data.clear()
