from __future__ import annotations

import pandas as pd


def kpi_facturacion_total(df):
    return df["MONTO"].sum()


def kpi_facturas_totales(df):
    return len(df)


def kpi_monto_impago(df):
    return df.loc[df["ESTADO"] == "IMPAGA", "MONTO"].sum()


def kpi_facturas_impagas(df):
    return (df["ESTADO"] == "IMPAGA").sum()


def kpi_clientes_con_deuda(df):
    df_impagas = df[df["ESTADO"] == "IMPAGA"].copy()
    return df_impagas["CLIENTE"].nunique()


def kpi_monto_vencido(df):
    return df["MONTO"].sum()


def kpi_tasa_mora(df):
    facturacion_total = kpi_facturacion_total(df)
    monto_impago = kpi_monto_impago(df)

    if facturacion_total in [0, None]:
        return 0

    return monto_impago / facturacion_total


def aging_deuda(df):
    df_impagas = df[df["ESTADO"] == "IMPAGA"].copy()

    bins = [-1, 30, 60, 90, 9999]
    labels = ["0-30 días", "31-60 días", "61-90 días", "90+ días"]

    df_impagas["tramo_edad"] = pd.cut(
        df_impagas["DIAS_TRANSCURRIDOS"],
        bins=bins,
        labels=labels
    )

    resumen = (
        df_impagas
        .groupby("tramo_edad", observed=False)["MONTO"]
        .sum()
        .reset_index()
    )

    return resumen


def resumen_riesgo_clientes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resume clientes con deuda y clasifica riesgo:
    - Alto: max_dias > 60 o tasa_impago >= 20%
    - Medio: max_dias > 30 o tasa_impago >= 5%
    - Bajo: resto con deuda > 0
    """
    df = df.copy()

    # Facturación total por cliente (todas las facturas del filtro)
    facturado = (
        df.groupby("CLIENTE", as_index=False)["MONTO"]
        .sum()
        .rename(columns={"MONTO": "MONTO_FACTURADO"})
    )

    # Solo facturas impagas
    impagas = df[df["ESTADO"] == "IMPAGA"].copy()

    if impagas.empty:
        return pd.DataFrame(
            columns=[
                "CLIENTE",
                "MONTO_FACTURADO",
                "MONTO_IMPAGO",
                "FACTURAS_IMPAGAS",
                "MAX_DIAS",
                "TASA_IMPAGO",
                "NIVEL_RIESGO",
                "ICONO_RIESGO",
            ]
        )

    deuda = (
        impagas.groupby("CLIENTE", as_index=False)
        .agg(
            MONTO_IMPAGO=("MONTO", "sum"),
            FACTURAS_IMPAGAS=("MONTO", "size"),
            MAX_DIAS=("DIAS_TRANSCURRIDOS", "max"),
        )
    )

    resumen = facturado.merge(deuda, on="CLIENTE", how="inner")

    resumen["TASA_IMPAGO"] = resumen["MONTO_IMPAGO"] / resumen["MONTO_FACTURADO"]
    resumen["TASA_IMPAGO"] = resumen["TASA_IMPAGO"].fillna(0)

    def clasificar(row):
        if row["MONTO_IMPAGO"] <= 0:
            return "Bajo"
        if row["MAX_DIAS"] > 60 or row["TASA_IMPAGO"] >= 0.20:
            return "Alto"
        if row["MAX_DIAS"] > 30 or row["TASA_IMPAGO"] >= 0.05:
            return "Medio"
        return "Bajo"

    resumen["NIVEL_RIESGO"] = resumen.apply(clasificar, axis=1)

    iconos = {
        "Alto": "🔴 Alto",
        "Medio": "🟡 Medio",
        "Bajo": "🟢 Bajo",
    }
    resumen["ICONO_RIESGO"] = resumen["NIVEL_RIESGO"].map(iconos)

    orden = {"Alto": 1, "Medio": 2, "Bajo": 3}
    resumen["ORDEN_RIESGO"] = resumen["NIVEL_RIESGO"].map(orden)

    resumen = resumen.sort_values(
        ["ORDEN_RIESGO", "MONTO_IMPAGO"],
        ascending=[True, False]
    ).drop(columns=["ORDEN_RIESGO"])

    return resumen