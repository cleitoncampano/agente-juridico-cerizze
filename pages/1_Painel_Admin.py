import json
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import glob

# === CONFIGURAÇÃO DA PÁGINA ===
st.set_page_config(
    page_title="Painel Administrativo - Cerizze", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# === ESTILOS CSS ===
st.markdown("""
    <style>
        body { background-color: #0D5D57; color: #E5DCD4; }
        .stApp { background-color: #0D5D57; color: #E5DCD4; }
        .css-1d391kg { color: white; }
        .metric-card { 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 1rem; 
            border-radius: 10px; 
            margin: 0.5rem 0;
        }
        .alert-success { background-color: #28a745; padding: 0.5rem; border-radius: 5px; }
        .alert-warning { background-color: #ffc107; color: black; padding: 0.5rem; border-radius: 5px; }
        .alert-danger { background-color: #dc3545; padding: 0.5rem; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Painel Administrativo - Agente Cerizze")
st.markdown("**Bem-vindo ao painel de estatísticas do agente jurídico Cerizze!**")

# === CARREGAMENTO DOS DADOS ===
@st.cache_data(ttl=300)
def carregar_dados() -> pd.DataFrame:
    dados = []
    padroes_arquivos = [
        "data/interacoes.jsonl",
        "data/logs/interacoes_*.jsonl",
        "data/interacoes_jsonl"
    ]
    
    arquivos_encontrados = []
    for padrao in padroes_arquivos:
        arquivos_encontrados.extend(glob.glob(padrao))
    
    if not arquivos_encontrados:
        st.warning("⚠️ Nenhum arquivo de log encontrado.")
        return pd.DataFrame()
    
    for arquivo in arquivos_encontrados:
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                for linha in f:
                    try:
                        log = json.loads(linha.strip())
                        dados.append(log)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            continue
    
    if not dados:
        st.warning("⚠️ Nenhuma interação registrada ainda.")
        return pd.DataFrame()
    
    df = pd.DataFrame(dados)

    # Conversão de datas
    if 'timestamp' in df.columns:
        df["data_parsed"] = pd.to_datetime(df["timestamp"], errors="coerce")
    elif 'data' in df.columns:
        df["data_parsed"] = pd.to_datetime(df["data"], format="%Y-%m-%d %H:%M:%S", errors="coerce")

    # Soma de tokens
    if 'tokens_total' not in df.columns:
        df["tokens_total"] = df.get("tokens_input", 0) + df.get("tokens_output", 0)

    # Filtro de sucesso
    if 'status' in df.columns:
        df = df[df['status'] == 'sucesso']
    
    return df

with st.spinner("📊 Carregando dados..."):
    df = carregar_dados()

if df.empty:
    st.stop()

# === FILTROS ===
# Filtro por data
# Filtro por data
if 'data_parsed' in df.columns and not df['data_parsed'].isna().all():
    data_min = df['data_parsed'].min().date()
    data_max = df['data_parsed'].max().date()

    # Garante que data_min <= data_max e fallback de 7 dias se for igual
    if data_min >= data_max:
        data_min = data_max - timedelta(days=7)

    try:
        data_inicio, data_fim = st.sidebar.date_input(
            "Período:",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max
        )
    except Exception as e:
        st.warning(f"⚠️ Erro ao definir período: {e}")
        data_inicio, data_fim = data_min, data_max

    # Aplica filtro de data
    df = df[
        (df['data_parsed'].dt.date >= data_inicio) & 
        (df['data_parsed'].dt.date <= data_fim)
    ]
else:
    st.warning("⚠️ Coluna 'data_parsed' está vazia ou ausente.")
    st.stop()


# === CÁLCULO DE CUSTO ===
def calcular_custo(row):
    precos = {
        "gpt-4o": {"input": 0.005/1000, "output": 0.015/1000},
        "gpt-4": {"input": 0.03/1000, "output": 0.06/1000},
        "gpt-3.5-turbo": {"input": 0.0005/1000, "output": 0.0015/1000}
    }
    modelo = row.get("modelo", "gpt-3.5-turbo")
    ti = row.get("tokens_input", 0)
    to = row.get("tokens_output", 0)
    if modelo in precos:
        return (ti * precos[modelo]["input"] + to * precos[modelo]["output"])
    return 0

if 'custo_estimado' not in df.columns:
    df["custo_estimado"] = df.apply(calcular_custo, axis=1)

# === DASHBOARD EXECUTIVO ===
st.markdown("## 📈 Visão Geral")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("🔄 Interações", f"{len(df):,}")
col2.metric("🧮 Tokens", f"{int(df['tokens_total'].sum()):,}")
col3.metric("👥 Usuários", df["user"].nunique())
col4.metric("💰 Custo (USD)", f"${df['custo_estimado'].sum():.2f}")
col5.metric("⏱ Tempo Médio", f"{df['tempo_resposta'].mean():.1f}s" if 'tempo_resposta' in df else "N/A")

# === GRÁFICOS ===
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📆 Interações por dia")
    df_diario = df.groupby(df["data_parsed"].dt.date).size().reset_index(name="Interações")
    fig = px.line(df_diario, x="data_parsed", y="Interações")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### ⚖️ Por Área Jurídica")
    if 'area' in df.columns:
        df_area = df['area'].value_counts().reset_index()
        fig_area = px.pie(df_area, names='index', values='area', title="Distribuição por área")
        st.plotly_chart(fig_area, use_container_width=True)

# === RANKINGS ===
st.markdown("---")
st.markdown("## 🏆 Rankings")

col1, col2, col3 = st.columns(3)

with col1:
    top_users = df['user'].value_counts().head(5)
    st.markdown("### 👤 Mais Ativos")
    for i, (u, c) in enumerate(top_users.items(), 1):
        st.write(f"{i}. {u} — {c} usos")

with col2:
    if 'tokens_total' in df.columns:
        top_tokens = df.groupby("user")['tokens_total'].sum().sort_values(ascending=False).head(5)
        st.markdown("### 🧮 Tokens")
        for i, (u, t) in enumerate(top_tokens.items(), 1):
            st.write(f"{i}. {u} — {int(t):,} tokens")

with col3:
    if 'custo_estimado' in df.columns:
        top_custos = df.groupby("user")['custo_estimado'].sum().sort_values(ascending=False).head(5)
        st.markdown("### 💰 Custo")
        for i, (u, c) in enumerate(top_custos.items(), 1):
            st.write(f"{i}. {u} — ${c:.2f}")

# === TABELA FINAL ===
st.markdown("---")
st.markdown("### 📋 Interações Detalhadas")

st.dataframe(df[[
    "data_parsed", "user", "area", "modelo", "tokens_total", "custo_estimado"
]].sort_values(by="data_parsed", ascending=False), use_container_width=True)
