# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
py -m pip install -r acoes_2026/requirements.txt

# Run the app
py -m streamlit run acoes_2026/app.py

# Kill running Streamlit and restart (Windows PowerShell)
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
py -m streamlit run acoes_2026/app.py --server.headless true
```

The app runs at `http://localhost:8501`. The "Atualizar Dados" button in the sidebar clears the data cache and forces a fresh fetch from Yahoo Finance.

## Architecture

The app is split into four modules with a strict dependency order:

```
data.py  ──►  charts.py
   │               │
   └──►  metrics.py│
              │    │
              └────┴──►  app.py
```

- **`data.py`** — single source of truth for raw data. Fetches all three tickers in one `yfinance.download()` call (more efficient than per-ticker calls). Uses `@st.cache_data(ttl=3600)` so data is shared across browser tabs and only re-fetched once per hour. `threads=False` avoids a Windows/Python 3.12 compatibility issue with yfinance.

- **`metrics.py`** — pure functions, no Streamlit dependency. Takes a single-stock DataFrame and returns computed values. `format_brl()` implements Brazilian number formatting manually (avoids fragile locale configuration on Windows).

- **`charts.py`** — builds Plotly figures. All charts go through `apply_dark_theme()` for consistent styling. `COLORS` and `NAMES` dicts map Yahoo Finance ticker symbols (e.g. `PETR4.SA`) to display values. Imports `get_normalized_returns` from `data.py`.

- **`app.py`** — orchestrates layout and wires the other modules together. All Streamlit calls live here.

## Key Details

- Tickers use the B3 suffix: `PETR4.SA`, `ITUB4.SA`, `VALE3.SA`
- Date range is hardcoded: `START_DATE = "2026-01-01"`, `END_DATE = "2026-05-12"` in `data.py`
- `background_gradient()` in `app.py` requires `matplotlib` — it must be installed even though it's not used directly
- A git post-commit hook at `.git/hooks/post-commit` automatically pushes to GitHub after every commit
