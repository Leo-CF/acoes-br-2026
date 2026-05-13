# Dashboard de Ações Brasileiras 2026

Aplicativo web para análise e visualização da performance das ações **PETR4** (Petrobras), **ITUB4** (Itaú) e **VALE3** (Vale) no ano de 2026.

## Funcionalidades

- Cards com preço atual, retorno acumulado (%), mínimo, máximo e média
- Gráfico comparativo de retorno normalizado desde 01/01/2026
- Candlestick com média móvel de 20 dias por ação
- Gráfico de volume negociado
- Tabela histórica com heatmap de preços
- Botão para atualizar dados manualmente

## Instalação

```bash
pip install -r requirements.txt
```

## Como rodar

```bash
streamlit run app.py
```

O app abrirá automaticamente em `http://localhost:8501`.

## Stack

| Pacote | Uso |
|---|---|
| Streamlit | Interface web |
| yfinance | Dados da Yahoo Finance |
| Plotly | Gráficos interativos |
| Pandas | Manipulação de dados |
| Matplotlib | Heatmap nas tabelas |
