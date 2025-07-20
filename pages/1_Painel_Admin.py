import json
import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# === VISUAL ===
st.set_page_config(page_title="Painel Administrativo - Cerizze", layout="wide")
st.markdown("""
    <style>
        body {
            background-color: #0D5D57;
            color: #E5DCD4;
        }
        .stApp {
            background-color: #0D5D57;
            color: #E5DCD4;
        }
        .css-1d391kg {
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Painel Administrativo - Agente Cerizze")

# === LEITURA DO JSONL ===
caminho = "data/interacoes_jsonl"
dados = []

if os.path.exists(caminho):
    with open(caminho, "r") as f:
        for linha in f:
            try:
                dados.append(json.loads(linha))
            except json.JSONDecodeError:
                continue

if not dados:
    st.warning("Nenhuma interação registrada ainda.")
    st.stop()

df = pd.DataFrame(dados)
df["tokens_total"] = df["tokens_input"] + df["tokens_output"]
df["data"] = pd.to_datetime(df["data"], format="%Y-%m-%d %H:%M:%S")

# === FILTROS ===
st.sidebar.header("🔍 Filtros")
usuarios = st.sidebar.multiselect("Usuário", options=sorted(df["user"].unique()), default=df["user"].unique())
areas = st.sidebar.multiselect("Área Jurídica", options=sorted(df["area"].unique()), default=df["area"].unique())
modelos = st.sidebar.multiselect("Modelo de IA", options=sorted(df["modelo"].unique()), default=df["modelo"].unique())

df_filtrado = df[
    (df["user"].isin(usuarios)) &
    (df["area"].isin(areas)) &
    (df["modelo"].isin(modelos))
]

# === TABELA DE INTERAÇÕES ===
st.subheader("📄 Interações Registradas")
st.caption(f"Total de registros: {len(df_filtrado)}")

for i, row in df_filtrado.sort_values("data", ascending=False).iterrows():
    with st.expander(f"📅 {row['data'].strftime('%d/%m/%Y %H:%M:%S')} | 👤 {row['user']} | ⚖️ {row['area']} | 🧠 {row['modelo']} | 🧮 Tokens: {row['tokens_total']}"):
        st.markdown(f"**❓ Pergunta:**\n\n{row['pergunta']}")
        st.markdown("---")
        st.markdown(f"**✅ Resposta:**\n\n{row['resposta']}")

# === KPIs ===
st.markdown("---")
st.subheader("📌 Métricas Gerais")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Interações", len(df_filtrado))
with col2:
    st.metric("Total de Tokens", int(df_filtrado["tokens_total"].sum()))
with col3:
    st.metric("Usuários Únicos", df_filtrado["user"].nunique())

# === GRÁFICO DE USO NO TEMPO ===
st.markdown("### 📈 Interações por Dia")
interacoes_por_dia = df_filtrado.groupby(df_filtrado["data"].dt.date).size()

fig1, ax1 = plt.subplots()
interacoes_por_dia.plot(kind="bar", ax=ax1, color="#43A6A0")
ax1.set_ylabel("Nº de Interações")
ax1.set_xlabel("Data")
ax1.set_title("Uso diário do Agente Cerizze")
st.pyplot(fig1)

# === GRÁFICO DE TOKENS POR USUÁRIO ===
st.markdown("### 🧮 Tokens Consumidos por Usuário")
tokens_por_usuario = df_filtrado.groupby("user")["tokens_total"].sum().sort_values(ascending=False)

fig2, ax2 = plt.subplots()
tokens_por_usuario.plot(kind="barh", ax=ax2, color="#E5DCD4")
ax2.set_xlabel("Tokens")
ax2.set_ylabel("Usuário")
ax2.set_title("Consumo de Tokens por Usuário")
st.pyplot(fig2)
