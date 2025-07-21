# agente_core.py
import streamlit as st

def responder(pergunta, area):
    return f"Resposta simulada para a área {area} com a pergunta: {pergunta}"

def exibir_metricas_sidebar():
    st.sidebar.markdown("📊 Métricas fictícias")
