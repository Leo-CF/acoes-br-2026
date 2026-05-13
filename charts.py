import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data import get_normalized_returns

COLORS = {
    "PETR4.SA": "#00B4D8",
    "ITUB4.SA": "#F77F00",
    "VALE3.SA": "#2DC653",
}

NAMES = {
    "PETR4.SA": "Petrobras (PETR4)",
    "ITUB4.SA": "Itaú (ITUB4)",
    "VALE3.SA": "Vale (VALE3)",
}


def apply_dark_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(14,17,23,1)",
        font=dict(family="Inter, sans-serif", size=13),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig


def normalized_returns_chart(data: dict[str, pd.DataFrame]) -> go.Figure:
    fig = go.Figure()

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="rgba(255,255,255,0.3)",
        line_width=1,
    )

    for ticker, df in data.items():
        if df.empty:
            continue
        returns = get_normalized_returns(df)
        fig.add_trace(
            go.Scatter(
                x=returns.index,
                y=returns.values,
                name=NAMES.get(ticker, ticker),
                line=dict(color=COLORS.get(ticker, "#ffffff"), width=2.5),
                hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:.2f}%</b><extra></extra>",
            )
        )

    fig.update_layout(
        title="Retorno Acumulado em 2026 (%)",
        xaxis_title="Data",
        yaxis_title="Retorno desde 01/01/2026 (%)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(step="all", label="Tudo"),
                ]
            ),
            rangeslider=dict(visible=False),
        ),
    )

    return apply_dark_theme(fig)


def close_price_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    ma20 = df["Close"].rolling(20).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
            increasing_line_color="#2DC653",
            decreasing_line_color="#E63946",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=ma20,
            name="MM20",
            line=dict(color="#FFD166", width=1.5, dash="dot"),
            hovertemplate="%{x|%d/%m/%Y}<br>MM20: R$ %{y:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"Preço — {NAMES.get(ticker, ticker)}",
        xaxis_title="Data",
        yaxis_title="Preço (R$)",
        xaxis_rangeslider_visible=False,
    )

    return apply_dark_theme(fig)


def volume_chart(data: dict[str, pd.DataFrame]) -> go.Figure:
    fig = go.Figure()

    for ticker, df in data.items():
        if df.empty or "Volume" not in df.columns:
            continue
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name=NAMES.get(ticker, ticker),
                marker_color=COLORS.get(ticker, "#ffffff"),
                hovertemplate="%{x|%d/%m/%Y}<br>Volume: %{y:,.0f}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Volume Negociado",
        xaxis_title="Data",
        yaxis_title="Volume",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    return apply_dark_theme(fig)
