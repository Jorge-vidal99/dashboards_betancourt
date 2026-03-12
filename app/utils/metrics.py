from __future__ import annotations

import pandas as pd


def kpi_facturacion_total(df: pd.DataFrame) -> float:
    return float(df["MONTO"].sum())


def kpi_facturas_totales(df: pd.DataFrame) -> int:
    return int(df["N_FACTURA"].nunique())


def kpi_monto_impago(df: pd.DataFrame) -> float:
    return float(df.loc[df["ESTADO"] == "IMPAGA", "MONTO"].sum())


def kpi_facturas_impagas(df: pd.DataFrame) -> int:
    return int(df.loc[df["ESTADO"] == "IMPAGA", "N_FACTURA"].nunique())


def kpi_clientes_con_deuda(df: pd.DataFrame) -> int:
    return int(df.loc[df["ESTADO"] == "IMPAGA", "CLIENTE"].nunique())


def kpi_monto_vencido(df_vencidas: pd.DataFrame) -> float:
    return float(df_vencidas["MONTO"].sum())