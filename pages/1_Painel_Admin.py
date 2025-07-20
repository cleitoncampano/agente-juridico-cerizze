import json
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import glob
from typing import List, Dict

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

# === VERIFICAÇÃO DE ACESSO ===
def verificar_acesso_admin():
    """Verifica se usuário tem acesso ao painel admin"""
    if not st.session_state.get('usuario_logado'):
        st.error("❌ Acesso negado. Faça login primeiro.")
        st.stop()
    
    if st.session_state.get('role_usuario') != 'admin':
        st.error("❌ Acesso restrito. Apenas administradores podem acessar este painel.")
        st.stop()

# Verificar acesso
verificar_acesso_admin()

st.title("📊 Painel Administrativo - Agente Cerizze")
st.markdown(f"**Bem-vindo, {st.session_state.get('nome_usuario', 'Admin')}!**")

# === CARREGAMENTO DOS DADOS ===
@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_dados() -> pd.DataFrame:
    """Carrega dados de todos os arquivos de log"""
    dados = []
    
    # Procura por todos os arquivos de log
    padroes_arquivos = [
        "data/interacoes.jsonl",  # Arquivo único
        "data/logs/interacoes_*.jsonl",  # Arquivos por mês
        "data/interacoes_jsonl"  # Arquivo sem extensão (legado)
    ]
    
    arquivos_encontrados = []
    for padrao in padroes_arquivos:
        arquivos_encontrados.extend(glob.glob(padrao))
    
    if not arquivos_encontrados:
        st.warning("⚠️ Nenhum arquivo de log encontrado.")
        return pd.DataFrame()
    
    # Carrega dados de todos os arquivos
    for arquivo in arquivos_encontrados:
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                for linha in f:
                    try:
                        log = json.loads(linha.strip())
                        dados.append(log)
                    except json.JSONDecodeError as e:
                        st.sidebar.error(f"Erro ao ler linha em {arquivo}: {e}")
                        continue
        except FileNotFoundError:
            continue
        except Exception as e:
            st.sidebar.error(f"Erro ao ler arquivo {arquivo}: {e}")
    
    if not dados:
        st.warning("⚠️ Nenhuma interação registrada ainda.")
        return pd.DataFrame()
    
    df = pd.DataFrame(dados)

    # === Normalização dos dados ===
    try:
        # Calcula tokens total se não existir
        if 'tokens_total' not in df.columns:
            df["tokens_total"] = df.get("tokens_input", 0) + df.get("tokens_output", 0)

        # Normaliza coluna de data
        if "timestamp" in df.columns:
            df["data_parsed"] = pd.to_datetime(df["timestamp"], errors="coerce")
        elif "data" in df.columns:
            df["data_parsed"] = pd.to_datetime(df["data"], format="%Y-%m-%d %H:%M:%S", errors='coerce')
        else:
            df["data_parsed"] = pd.NaT

        # Filtra apenas registros com sucesso
        if 'status' in df.columns:
            df = df[df['status'] == 'sucesso']

        return df

    except Exception as e:
        st.error(f"❌ Erro ao processar dados: {e}")
        return pd.DataFrame()
