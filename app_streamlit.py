import os
import datetime
import pyperclip
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

# === CONFIG ===
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# === VISUAL ===
st.set_page_config(page_title="Agente Jurídico Cerizze", layout="wide")
st.markdown("""
    <style>
        body, .stApp {
            background-color: #0D0D0D;
            color: #E5DCD4;
            font-family: sans-serif;
        }

        /* Remove borda branca externa do form */
        div[data-testid="stForm"] {
            border: none !important;
            box-shadow: none !important;
        }

        /* Input customizado */
        .stTextInput input {
            background-color: #2E2E2E;
            color: white;
            border-radius: 30px;
            padding: 0.8rem 1.5rem;
            border: none;
            font-size: 1rem;
            width: 100%;
        }

        /* Centraliza o input */
        .custom-center {
            max-width: 700px;
            margin: auto;
            display: flex;
            justify-content: center;
        }

        /* Esconde o label interno (dica de submit) */
        .stTextInput > label {
            display: none !important;
        }

        .stMarkdown {
            font-size: 1.1rem;
        }
    </style>
""", unsafe_allow_html=True)

# === HISTÓRICO ===
if "historico" not in st.session_state:
    st.session_state.historico = []

# === SIDEBAR ===
st.sidebar.title("⚙️ IA Cerizze")
modelo = st.sidebar.selectbox("Modelo de IA:", ["gpt-4", "gpt-3.5-turbo"])
area = st.sidebar.selectbox("Área Jurídica:", [
    "Societário", "Tributário", "Trabalhista", "Cível", "Empresarial", "Licitações", "Regulatório", "Ambiental"
])

# Botão para limpar histórico
if st.sidebar.button("🗑️ Limpar Histórico"):
    st.session_state.historico = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💼 Cerizze - Advocacia Empresarial Full Service")

# === TÍTULO ===
st.markdown("<h2 style='text-align: center;'>🤖 Agente Jurídico Inteligente - Cerizze</h2>", unsafe_allow_html=True)

# === PROMPT ===
def montar_prompt(pergunta_usuario, area_juridica):
    return f'''Você é um agente de IA jurídico da banca Cerizze, especializado em Direito {area_juridica} Brasileiro. Atue com ética, excelência técnica, visão de negócios e foco prático.

Estruture sua resposta nos tópicos:
1. **Contexto**
2. **Análise jurídica**
3. **Recomendações práticas**
4. **Referências normativas**
5. **Limitações**

Pergunta:
{pergunta_usuario}
'''

def responder(pergunta, area):
    prompt = montar_prompt(pergunta, area)
    resposta = client.chat.completions.create(
        model=modelo,
        messages=[
            {"role": "system", "content": f"Você é um especialista em Direito {area} Brasileiro."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1200
    )
    return resposta.choices[0].message.content.strip()

# === INPUT COM ENTER ===
with st.form("form_pergunta", clear_on_submit=False):
    with st.container():
        st.markdown('<div class="custom-center">', unsafe_allow_html=True)
        pergunta = st.text_input("", placeholder="Digite sua pergunta aqui...", label_visibility="collapsed", key="input_pergunta")
        # Contador de caracteres
        if pergunta:
            st.markdown(f'<div style="text-align: right; color: #666;">Caracteres: {len(pergunta)}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        enviado = st.form_submit_button("")  # sem botão visível

# === PROCESSAMENTO ===
if enviado and pergunta.strip():
    with st.spinner("Consultando agente..."):
        resposta = responder(pergunta, area)
    st.session_state.historico.append({
        "pergunta": pergunta,
        "resposta": resposta,
        "area": area,
        "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    })
    st.success("Resposta obtida com sucesso!")

# === ÚLTIMA RESPOSTA ===
if st.session_state.historico:
    ultima = st.session_state.historico[-1]
    st.markdown("### 🧾 Resposta do Agente")
    st.markdown(ultima["resposta"], unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Copiar resposta"):
            pyperclip.copy(ultima["resposta"])
            st.balloons()  # Efeito visual ao copiar
            st.success("Resposta copiada com sucesso! ✨")
    with col2:
        st.download_button("📥 Baixar como .txt", data=ultima["resposta"], file_name="resposta_agente.txt")
    with col3:
        st.download_button("📄 Baixar como .md", data=ultima["resposta"], file_name="resposta_agente.md")

# === HISTÓRICO ===
if st.session_state.historico:
    st.markdown("### 📚 Histórico de Consultas")
    for item in reversed(st.session_state.historico):
        with st.expander(f"📅 {item['data']} | ⚖️ {item['area']}"):
            st.markdown(f"**❓ Pergunta:** {item['pergunta']}")
            st.markdown("---")
            st.markdown(f"**✅ Resposta:**\n\n{item['resposta']}", unsafe_allow_html=True)