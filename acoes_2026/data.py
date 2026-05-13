import streamlit as st
import yfinance as yf
import pandas as pd

TICKERS = {
    "PETR4": "PETR4.SA",
    "ITUB4": "ITUB4.SA",
    "VALE3": "VALE3.SA",
}

START_DATE = "2026-01-01"
END_DATE = "2026-05-12"


@st.cache_data(ttl=3600)
def fetch_all_data() -> dict[str, pd.DataFrame]:
    symbols = list(TICKERS.values())
    try:
        raw = yf.download(
            tickers=symbols,
            start=START_DATE,
            end="2026-05-13",
            auto_adjust=True,
            group_by="ticker",
            threads=False,
            progress=False,
        )
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return {sym: pd.DataFrame() for sym in symbols}

    result = {}
    for sym in symbols:
        try:
            if len(symbols) == 1:
                df = raw.copy()
            else:
                df = raw[sym].copy()
            df = df.dropna(subset=["Close"])
            result[sym] = df
        except Exception:
            result[sym] = pd.DataFrame()

    return result


def get_normalized_returns(df: pd.DataFrame) -> pd.Series:
    close = df["Close"]
    return (close / close.iloc[0] - 1) * 100
