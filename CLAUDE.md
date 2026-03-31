# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Dashboard de Facturación y Cobranza** - A billing and collections management system for Transportes Betancourt.

The system automatically syncs invoice data from OneDrive, processes it through an ETL pipeline, and visualizes KPIs and risk metrics through a Streamlit dashboard.

## Architecture

### Data Pipeline (ETL)

```
OneDrive (FACTURAS_2026/)
    ↓ [check_onedrive_updates.py - detect remote changes]
    ↓ [download_facturas_2026.py - download .xlsx files]
data_raw/
    ↓ [process_facturas.py - ETL & normalization]
data_processed/ (parquet files)
    ↓ [Streamlit dashboard]
Interactive Dashboard (localhost:8501)
```

**Key scripts:**
- `scripts/auth_onedrive.py` - OAuth token management (device flow, MSAL)
- `scripts/download_facturas_2026.py` - Sync .xlsx from OneDrive → data_raw/ (SHA256 dedup)
- `scripts/process_facturas.py` - Main ETL: normalize columns, validate data, classify invoices, generate parquets + audit report
- `scripts/check_onedrive_updates.py` - Remote change detection (metadata comparison)
- `scripts/check_updates.py` - Local change detection (SHA256 of data_raw files)
- `main.py` - Orchestrates the full pipeline (download + process) with logging

### Output Files (Parquets)

Generated in `data_processed/`:
- `facturas_consolidadas_todas.parquet` - All invoices (consolidation)
- `facturas_externas.parquet` - **External clients only** (main dashboard data)
- `facturas_intercompany.parquet` - Internal company-to-company invoices
- `facturas_vencidas_impagas.parquet` - Overdue unpaid (>30 days, status=IMPAGA)
- `facturas_invalidas.xlsx` - Audit: invalid dates/amounts

### Streamlit App

Three-page dashboard structure:

1. **`app/app.py`** (Home)
   - Global metrics + data load status
   - Navigation hub to other pages

2. **`app/pages/1_resumen_financiero.py`** (Financial Overview)
   - Total billing by customer, company, status
   - Filters: year, month, company, invoice status, customer
   - Charts: monthly evolution, top 10 customers, distribution by status
   - Expandable detail table

3. **`app/pages/2_gestion_cobranza.py`** (Collections Management)
   - Overdue debt analysis and customer risk classification
   - Aging of debt (0-30, 31-60, 61-90, 90+ days)
   - Risk levels: 🔴 Alto (>60 days OR >20% unpaid rate), 🟡 Medio (>30 days OR >5% unpaid rate), 🟢 Bajo
   - Charts: top delinquent customers, aging, debt by company, client risk heatmap
   - Client risk detail table + overdue invoice detail table

### Shared Utilities

**`app/utils/loaders.py`**
- Loads parquets with Streamlit caching (@st.cache_data)
- Cache invalidation via `_mtime` parameter (file modification time)
- Adds computed columns: `anio`, `mes_num`, `mes_nombre`, `anio_mes`
- Functions: `load_facturas_*()`, `get_last_update_*()`, `clear_cache()`

**`app/utils/formatters.py`**
- Currency: `format_currency_clp()` ($1.234.567), `format_compact_currency_clp()` ($1.2B, $500MM, $50K)
- Numbers: `format_number()` (1.000)
- Dates: `format_date_ddmmyyyy()` (31-12-2024), `format_datetime_update()` (timestamp → 31-12-2024 14:30)
- Percent: `format_percent()` (15,50%)

**`app/utils/metrics.py`**
- KPI calculations: `kpi_facturacion_total()`, `kpi_monto_impago()`, `kpi_tasa_mora()`
- Aging: `aging_deuda()` → bins by day ranges
- Risk classification: `resumen_riesgo_clientes()` → returns DataFrame with NIVEL_RIESGO

**`app/utils/charts.py`**
- Plotly bar/pie/donut charts (dark template)
- Functions for each dashboard visualization
- Color scheme: `COLOR_PRINCIPAL` (#1F4E79), `COLOR_IMPAGO` (#C62828), `COLOR_PAGADA` (#2E7D32)

## Common Commands

### Run the full pipeline
```bash
python main.py
```
Logs to `logs/pipeline_YYYYMMDD_HHMMSS.log`

### Run only ETL (data_raw → data_processed)
```bash
python scripts/process_facturas.py
```

### Check for OneDrive changes (metadata only)
```bash
python scripts/check_onedrive_updates.py
```
Returns JSON with `{"should_run": true/false, "changed_files": [...]}`

### Download from OneDrive
```bash
python scripts/download_facturas_2026.py
```

### Start Streamlit dashboard
```bash
streamlit run app/app.py
```
Access at http://localhost:8501

### Test OneDrive connection
```bash
python scripts/test_onedrive.py
```

## Important Concepts

### Data Model (Standard Columns)

After ETL, all invoices have:
```
N_FACTURA, FECHA_EMISION, CLIENTE, RUT, CARGA_O_CONCEPTO, MONTO, ESTADO,
RAZON_SOCIAL, DIAS_TRANSCURRIDOS, TIPO_FACTURA, ES_INTERCOMPANY,
anio, mes_num, mes_nombre, anio_mes
```

### Factura Classification

- **EXTERNA** (RUT not in RUTS_INTERCOMPANY) → visible in main dashboard
- **INTERCOMPANY** (RUT in predefined set) → filtered out from external metrics, tracked separately

### Cache Invalidation Pattern

Streamlit's default file hashing is unreliable for parquets. The codebase uses `_mtime` (file modification time) as a cache key:

```python
@st.cache_data(show_spinner=False)
def load_facturas_externas(_mtime: float = 0.0) -> pd.DataFrame:
    pass  # When _mtime changes → cache reloads
```

When loading: `df = load_facturas_externas(_mtime=get_last_update_externas())`

The underscore prefix (`_mtime`) tells Streamlit to use it as a direct discriminator, not as hashable data.

### OneDrive Authentication

Uses MSAL (Microsoft Authentication Library) with **device flow** (no interactive browser needed):
- Shows user a link + code to authenticate
- Tokens cached in `token_cache.bin`
- Subsequent calls use silent auth (no login prompt)
- Microsoft Graph API used for file operations

### Change Detection

Two levels:
1. **Remote** (`check_onedrive_updates.py`): Compares eTag/lastModifiedDateTime/size
2. **Local** (`check_updates.py`): SHA256 hashing of data_raw/*.xlsx

Both avoid redundant processing.

## Development Notes

- **Python 3.8+** (type hints use `|` union syntax, requires 3.10+)
- **Timezone:** Uses system timezone via `datetime.now()`
- **Column normalization:** Removes accents, converts to UPPERCASE, standardizes column names across 3 vendors
- **Error handling:** process_facturas.py generates audit report for invalid rows (bad dates/amounts), doesn't skip them silently
- **Dependencies:** Minimal stack (pandas, plotly, streamlit, pyarrow for parquet, openpyxl for Excel read/write)

## File Structure Summary

```
REPORTE/
├── main.py                      # Pipeline orchestrator
├── requirements.txt             # Dependencies (minimal)
├── app/
│   ├── app.py                   # Home page
│   ├── pages/
│   │   ├── 1_resumen_financiero.py
│   │   └── 2_gestion_cobranza.py
│   └── utils/
│       ├── loaders.py           # Parquet loading + caching
│       ├── formatters.py        # Display formatting
│       ├── metrics.py           # KPI calculations
│       └── charts.py            # Plotly charts
├── scripts/
│   ├── auth_onedrive.py         # MSAL token management
│   ├── download_facturas_2026.py # OneDrive sync
│   ├── process_facturas.py      # Main ETL
│   ├── check_onedrive_updates.py # Remote change detection
│   ├── check_updates.py         # Local change detection
│   └── test_onedrive.py         # Connectivity test
├── data_raw/                    # Downloaded .xlsx files (git-ignored)
├── data_processed/              # Generated parquets
├── state/                       # Control files (change tracking)
├── logs/                        # Pipeline logs
└── token_cache.bin              # MSAL token cache (git-ignored)
```
