import pandas as pd


def compute_metrics(df: pd.DataFrame, name: str) -> dict:
    close = df["Close"]
    return {
        "name": name,
        "current_price": close.iloc[-1],
        "return_pct": (close.iloc[-1] / close.iloc[0] - 1) * 100,
        "min_price": close.min(),
        "max_price": close.max(),
        "avg_price": close.mean(),
        "last_date": df.index[-1].strftime("%d/%m/%Y"),
    }


def format_brl(value: float) -> str:
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def format_pct(value: float) -> str:
    return f"{value:+.2f}%"
