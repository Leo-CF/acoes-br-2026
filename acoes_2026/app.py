import streamlit as st
import pandas as pd

from data import TICKERS, fetch_all_data
from metrics import compute_metrics, format_brl, format_pct
from charts import normalized_returns_chart, close_price_chart, volume_chart, NAMES

st.set_page_config(
    page_title="Análise de Ações BR 2026",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.title("📈 Ações BR 2026")
    st.caption("Performance de jan a mai/2026")

    selected_names = st.multiselect(
        "Ações",
        options=list(TICKERS.keys()),
        default=list(TICKERS.keys()),
    )
    selected_tickers = [TICKERS[n] for n in selected_names]

    st.divider()
    st.caption("Período: 01/01/2026 — 12/05/2026")

    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("Dados: Yahoo Finance via yfinance")

# Carregar dados
all_data = fetch_all_data()

# Filtrar pelos tickers selecionados
data = {t: all_data[t] for t in selected_tickers if t in all_data and not all_data[t].empty}

if not data:
    st.error("Nenhum dado disponível. Verifique a conexão e tente atualizar.")
    st.stop()

# Verificar erros por ticker
for ticker in selected_tickers:
    if ticker not in all_data or all_data[ticker].empty:
        st.warning(f"Não foi possível carregar dados para {ticker}.")

# Header
st.title("Dashboard de Ações Brasileiras — 2026")
last_dates = [df.index[-1].strftime("%d/%m/%Y") for df in data.values()]
st.caption(f"Última atualização dos dados: {max(last_dates)}")

st.divider()

# Seção 1: Cards de métricas
st.subheader("Resumo")
cols = st.columns(len(data))
for col, (ticker, df) in zip(cols, data.items()):
    m = compute_metrics(df, NAMES.get(ticker, ticker))
    with col:
        st.metric(
            label=m["name"],
            value=format_brl(m["current_price"]),
            delta=format_pct(m["return_pct"]),
        )
        st.caption(
            f"Mín: {format_brl(m['min_price'])} · "
            f"Máx: {format_brl(m['max_price'])} · "
            f"Méd: {format_brl(m['avg_price'])}"
        )

st.divider()

# Seção 2: Gráfico de retorno normalizado
st.subheader("Retorno Acumulado Comparativo")
fig_returns = normalized_returns_chart(data)
st.plotly_chart(fig_returns, use_container_width=True)

st.divider()

# Seção 3: Detalhe por ação (abas)
st.subheader("Detalhe por Ação")
tabs = st.tabs([NAMES.get(t, t) for t in data.keys()])
for tab, (ticker, df) in zip(tabs, data.items()):
    with tab:
        col_left, col_right = st.columns(2)
        with col_left:
            st.plotly_chart(
                close_price_chart(df, ticker),
                use_container_width=True,
            )
        with col_right:
            st.plotly_chart(
                volume_chart({ticker: df}),
                use_container_width=True,
            )

        display_df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        display_df.index = display_df.index.strftime("%d/%m/%Y")
        display_df.index.name = "Data"
        display_df = display_df.sort_index(ascending=False)

        price_cols = ["Open", "High", "Low", "Close"]
        fmt = {c: "R$ {:.2f}" for c in price_cols}
        fmt["Volume"] = "{:,.0f}"

        styled = display_df.style.format(fmt).background_gradient(
            subset=["Close"], cmap="RdYlGn"
        )
        st.dataframe(styled, use_container_width=True, height=300)

st.divider()

# Seção 4: Tabela comparativa
st.subheader("Fechamento Comparativo")

close_frames = {}
for ticker, df in data.items():
    s = df["Close"].copy()
    s.name = NAMES.get(ticker, ticker)
    close_frames[ticker] = s

comparative = pd.concat(close_frames.values(), axis=1)
comparative.index = comparative.index.strftime("%d/%m/%Y")
comparative = comparative.sort_index(ascending=False)

fmt_all = {col: "R$ {:.2f}" for col in comparative.columns}
styled_comp = comparative.style.format(fmt_all).background_gradient(cmap="RdYlGn")
st.dataframe(styled_comp, use_container_width=True)
