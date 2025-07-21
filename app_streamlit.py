import streamlit as st
import datetime
from agente_core import responder, exibir_metricas_sidebar

# === CONFIGURAÇÃO DA PÁGINA ===
st.set_page_config(
    page_title="Agente Jurídico Cerizze",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === ESTILO VISUAL ===
st.markdown("""
    <style>
        .stApp {
            background-color: #0D5D57;
            color: #E5DCD4;
        }
        .css-1d391kg {
            color: #E5DCD4;
        }
        .css-ffhzg2 {
            background-color: #0D5D57 !important;
        }
    </style>
""", unsafe_allow_html=True)

# === SIDEBAR ===
st.sidebar.image("https://cerizze.com/wp-content/uploads/2022/04/logo_cerizze-branco.png", use_column_width=True)
st.sidebar.title("Agente Jurídico Cerizze")
st.sidebar.markdown("---")

# Seletor de modelo e área
modelo = st.sidebar.selectbox("🧠 Modelo de IA", ["gpt-4o", "gpt-4", "gpt-3.5-turbo"])
area = st.sidebar.selectbox("⚖️ Área Jurídica", [
    "Tributário", "Societário", "Trabalhista", "Contratual", "Cível", "Consumidor", "Regulatório", "Internacional", "Imobiliário"
])

# === CABEÇALHO ===
st.title("🤖 Agente Jurídico Cerizze")
st.markdown("Sistema de inteligência artificial aplicado à advocacia empresarial.")

# === CAMPO DE PERGUNTA ===
pergunta = st.text_area("Digite sua pergunta jurídica:", height=150, placeholder="Ex: Como funciona a responsabilidade solidária entre sócios?")

# === BOTÃO ===
if st.button("🔍 Consultar IA"):
    if not pergunta.strip():
        st.warning("Digite uma pergunta antes de continuar.")
    else:
        with st.spinner("Consultando o agente Cerizze..."):
            resposta = responder(pergunta, area)

        if isinstance(resposta, str):
            st.success("Resposta gerada com sucesso!")
            st.markdown("### ✅ Resposta da IA")
            st.markdown(resposta)

            # Botão de cópia
            st.code(resposta, language='markdown')
            st.download_button(
                label="⬇️ Baixar resposta (.txt)",
                data=resposta,
                file_name=f"resposta_cerizze_{datetime.date.today()}.txt",
                mime="text/plain"
            )
        else:
            st.error(resposta.get("resposta", "Erro desconhecido."))

# === EXIBE AS MÉTRICAS ===
exibir_metricas_sidebar()
