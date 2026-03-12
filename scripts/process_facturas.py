from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd


# -----------------------------
# CONFIGURACIÓN
# -----------------------------
# Ruta base del proyecto:
# .../REPORTE
BASE_DIR = Path(__file__).resolve().parents[1]

# Carpetas de entrada y salida
RAW_DIR = BASE_DIR / "data_raw"
PROCESSED_DIR = BASE_DIR / "data_processed"

# Crear carpeta de salida si no existe
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# RUTs intercompany
RUTS_INTERCOMPANY = {
    "76.102.311-K",  # TTES CLAUDIO BETANCOURT CARRASCO
    "76.102.317-9",  # TTES EDUARDO BETANCOURT CARRASCO
    "76.266.746-0",  # TTES BETANCOURT HERMANOS
}


# -----------------------------
# Normalización de columnas
# -----------------------------
def normalize_col(col: str) -> str:
    c = str(col).strip().upper()
    c = re.sub(r"\s+", " ", c)
    c = c.replace("N°", "N").replace("Nº", "N")
    c = (
        c.replace("Á", "A")
         .replace("É", "E")
         .replace("Í", "I")
         .replace("Ó", "O")
         .replace("Ú", "U")
    )
    c = re.sub(r"[^A-Z0-9]+", "_", c).strip("_")
    return c


def standarize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_col(c) for c in df.columns]

    rename_map = {
        "N_FACTURA": "N_FACTURA",
        "N_FACTURAS": "N_FACTURA",
        "NUMERO_FACTURA": "N_FACTURA",
        "NUMERO_DE_FACTURA": "N_FACTURA",

        "FECHA_EMISION": "FECHA_EMISION",
        "FECHA_DE_EMISION": "FECHA_EMISION",

        "CLIENTE": "CLIENTE",
        "RUT": "RUT",

        "CARGA_O_CONCEPTO": "CARGA_O_CONCEPTO",
        "CARGA_CONCEPTO": "CARGA_O_CONCEPTO",

        "MONTO": "MONTO",
        "MONTO_NETO": "MONTO",

        "ESTADO": "ESTADO",
        "STATUS": "ESTADO",
    }

    df.rename(
        columns={k: v for k, v in rename_map.items() if k in df.columns},
        inplace=True
    )
    return df


# -----------------------------
# Tipos / normalización
# -----------------------------
def to_number_monto(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    s = s.str.replace("$", "", regex=False)
    s = s.str.replace(" ", "", regex=False)
    s = s.str.replace(".", "", regex=False)   # separador miles
    s = s.str.replace(",", ".", regex=False)  # separador decimal
    return pd.to_numeric(s, errors="coerce")


def normalize_estado(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.upper()
    s = (
        s.str.replace("Á", "A")
         .str.replace("É", "E")
         .str.replace("Í", "I")
         .str.replace("Ó", "O")
         .str.replace("Ú", "U")
    )
    s = s.str.replace(r"\s+", " ", regex=True)
    return s


def normalize_rut(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper()


def normalize_cliente(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.upper()
    s = (
        s.str.replace("Á", "A")
         .str.replace("É", "E")
         .str.replace("Í", "I")
         .str.replace("Ó", "O")
         .str.replace("Ú", "U")
    )
    s = s.str.replace(r"\s+", " ", regex=True)

    # Quitar puntos, comas, punto y coma, dos puntos al final
    s = s.str.replace(r"[.,;:]+$", "", regex=True)

    return s


def coalesce_columns(df: pd.DataFrame, base_name: str) -> pd.DataFrame:
    """
    Si existen columnas duplicadas como:
    N_FACTURA, N_FACTURA_2, N_FACTURA_3
    se unifican tomando el primer valor no nulo.
    """
    cols = [c for c in df.columns if c == base_name or c.startswith(base_name + "_")]
    if len(cols) <= 1:
        return df

    df = df.copy()
    df[base_name] = df[cols].bfill(axis=1).iloc[:, 0]
    drop_cols = [c for c in cols if c != base_name]
    df.drop(columns=drop_cols, inplace=True)
    return df


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    archivos = {
        "FACTURAS_TBH_2026.xlsx": "BETANCOURT HERMANOS",
        "FACTURAS_EDUARDO_2026.xlsx": "TRANSPORTES EDUARDO",
        "FACTURAS_CLAUDIO_2026.xlsx": "TRANSPORTES CLAUDIO",
    }

    modelo_cols = [
        "N_FACTURA",
        "FECHA_EMISION",
        "CLIENTE",
        "RUT",
        "CARGA_O_CONCEPTO",
        "MONTO",
        "ESTADO",
    ]
    required = set(modelo_cols)

    dfs: list[pd.DataFrame] = []

    print("1) Leyendo y estandarizando archivos...")

    for archivo, empresa in archivos.items():
        ruta = RAW_DIR / archivo

        if not ruta.exists():
            print(f" No se encontró: {ruta}")
            continue

        df = pd.read_excel(ruta)
        df = standarize_columns(df)

        unnamed_cols = [c for c in df.columns if c.startswith("UNNAMED")]
        if unnamed_cols:
            df.drop(columns=unnamed_cols, inplace=True)

        for col in modelo_cols:
            df = coalesce_columns(df, col)

        missing = required - set(df.columns)
        if missing:
            print(f" {archivo}: faltan columnas {sorted(missing)}")
            print(f"   Columnas detectadas: {list(df.columns)}")
            continue

        df = df[modelo_cols].copy()

        # Tipos
        df["FECHA_EMISION"] = pd.to_datetime(df["FECHA_EMISION"], errors="coerce")
        df["MONTO"] = to_number_monto(df["MONTO"])
        df["ESTADO"] = normalize_estado(df["ESTADO"])
        df["RUT"] = normalize_rut(df["RUT"])
        df["CLIENTE"] = normalize_cliente(df["CLIENTE"])

        # Empresa emisora
        df["RAZON_SOCIAL"] = empresa

        # Limpiar N_FACTURA
        df["N_FACTURA"] = (
            df["N_FACTURA"]
            .astype(str)
            .str.strip()
            .str.replace(".0", "", regex=False)
        )

        # Filtrar filas basura
        df = df[df["N_FACTURA"].notna() & (df["N_FACTURA"] != "")].copy()

        dfs.append(df)
        print(f" {archivo} OK ({len(df)} filas)")

    if not dfs:
        print(" No se cargó ningún archivo. Revisa data_raw y nombres.")
        return

    print("\n2) Consolidando datasets (sin filtros de negocio)...")
    df_total = pd.concat(dfs, ignore_index=True)

    print("3) Calculando días transcurridos desde FECHA_EMISION...")
    hoy = datetime.now()
    df_total["DIAS_TRANSCURRIDOS"] = (hoy - df_total["FECHA_EMISION"]).dt.days

    print("4) Clasificando facturas: EXTERNA vs INTERCOMPANY...")
    df_total["TIPO_FACTURA"] = df_total["RUT"].apply(
        lambda x: "INTERCOMPANY" if x in RUTS_INTERCOMPANY else "EXTERNA"
    )

    df_total["ES_INTERCOMPANY"] = df_total["TIPO_FACTURA"].apply(
        lambda x: 1 if x == "INTERCOMPANY" else 0
    )

    # QA
    print("\n5) QA rápido:")
    print("   - Filas totales:", len(df_total))
    print("   - Fechas inválidas (NaT):", int(df_total["FECHA_EMISION"].isna().sum()))
    print("   - Montos inválidos (NaN):", int(df_total["MONTO"].isna().sum()))
    print("   - Estados distintos:", sorted(df_total["ESTADO"].dropna().unique().tolist()))
    print("   - Externas:", int((df_total["TIPO_FACTURA"] == "EXTERNA").sum()))
    print("   - Intercompany:", int((df_total["TIPO_FACTURA"] == "INTERCOMPANY").sum()))

    # Auditoría
    invalid_fecha = df_total[df_total["FECHA_EMISION"].isna()].copy()
    invalid_monto = df_total[df_total["MONTO"].isna()].copy()

    cols_audit = [
        "RAZON_SOCIAL",
        "N_FACTURA",
        "CLIENTE",
        "RUT",
        "FECHA_EMISION",
        "MONTO",
        "ESTADO",
        "CARGA_O_CONCEPTO",
        "TIPO_FACTURA",
    ]

    invalid_out = PROCESSED_DIR / "facturas_invalidas.xlsx"

    with pd.ExcelWriter(invalid_out, engine="openpyxl") as writer:
        invalid_fecha[cols_audit].assign(MOTIVO="FECHA_INVALIDA").to_excel(
            writer,
            sheet_name="FECHA_INVALIDA",
            index=False,
        )
        invalid_monto[cols_audit].assign(MOTIVO="MONTO_INVALIDO").to_excel(
            writer,
            sheet_name="MONTO_INVALIDO",
            index=False,
        )

    print("\n Auditoría generada:")
    print("   -", invalid_out)
    print("   - FECHA_INVALIDA:", len(invalid_fecha))
    print("   - MONTO_INVALIDO:", len(invalid_monto))

    # Separación datasets
    print("\n6) Separando datasets...")
    df_externas = df_total[df_total["TIPO_FACTURA"] == "EXTERNA"].copy()
    df_intercompany = df_total[df_total["TIPO_FACTURA"] == "INTERCOMPANY"].copy()

    df_vencidas = df_externas[
        (df_externas["DIAS_TRANSCURRIDOS"] > 30)
        & (df_externas["ESTADO"] == "IMPAGA")
    ].copy()

    # Outputs
    output_all_parquet = PROCESSED_DIR / "facturas_consolidadas_todas.parquet"
    output_externas_parquet = PROCESSED_DIR / "facturas_externas.parquet"
    output_intercompany_parquet = PROCESSED_DIR / "facturas_intercompany.parquet"
    output_venc_parquet = PROCESSED_DIR / "facturas_vencidas_impagas.parquet"

    df_total.to_parquet(output_all_parquet, index=False)
    df_externas.to_parquet(output_externas_parquet, index=False)
    df_intercompany.to_parquet(output_intercompany_parquet, index=False)
    df_vencidas.to_parquet(output_venc_parquet, index=False)

    print("\n Outputs generados:")
    print("   - Consolidado total      :", output_all_parquet)
    print("   - Facturas externas      :", output_externas_parquet)
    print("   - Facturas intercompany  :", output_intercompany_parquet)
    print("   - Vencidas impagas       :", output_venc_parquet)
    print("   - Registros externas     :", len(df_externas))
    print("   - Registros intercompany :", len(df_intercompany))
    print("   - Vencidas impagas #     :", len(df_vencidas))


if __name__ == "__main__":
    main()