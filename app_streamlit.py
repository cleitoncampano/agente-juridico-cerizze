import os
import datetime
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

# === CONFIG ===
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# === CONFIGURAÇÃO VISUAL ===
st.set_page_config(page_title="Agente Jurídico Cerizze", layout="wide")
st.markdown("""
    <style>
        body {
            background-color: #0D5D57;
            color: #E5DCD4;
            font-family: sans-serif;
        }
        .stApp {
            background-color: #0D5D57;
            color: #E5DCD4;
        }
        .stTextInput input {
            background-color: #2E2E2E;
            color: white;
            border-radius: 30px;
            padding: 0.8rem 1.5rem;
            border: none;
            width: 100%;
            font-size: 1rem;
        }
        .stMarkdown {
            font-size: 1.1rem;
        }
        .copy-box {
            background-color: #1E1E1E;
            padding: 1rem;
            border-radius: 10px;
            color: white;
            font-family: monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
            word-break: break-word;
        }
    </style>
""", unsafe_allow_html=True)

# === SIDEBAR ===
st.sidebar.title("⚙️ IA Cerizze")
modelo = st.sidebar.selectbox("Modelo de IA:", ["gpt-4o", "gpt-3.5-turbo"])
area = st.sidebar.selectbox("Área Jurídica:", [
    "Societário", "Tributário", "Trabalhista", "Cível", "Empresarial", "Licitações", "Regulatório", "Ambiental"
])
st.sidebar.markdown("---")
st.sidebar.info("💼 Cerizze - Advocacia Empresarial Full Service")

# === TÍTULO CENTRAL ===
st.markdown("<h2 style='text-align: center;'>🤖 Agente Jurídico Inteligente - Cerizze</h2>", unsafe_allow_html=True)

# === INICIALIZA HISTÓRICO ===
if "historico" not in st.session_state:
    st.session_state.historico = []

# === PROMPT BUILDER ===
def montar_prompt(pergunta_usuario, area_juridica):
    return f"""
Você é um agente de IA jurídico da banca Cerizze, especializado em Direito {area_juridica} Brasileiro. Atue com ética, excelência técnica, visão de negócios e foco prático.

Estruture sua resposta nos tópicos:
1. **Contexto**
2. **Análise jurídica**
3. **Recomendações práticas**
4. **Referências normativas**
5. **Limitações**

Pergunta:
\"\"\"{pergunta_usuario}\"\"\"
"""

# === EXECUTA CONSULTA ===
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

# === INPUT ESTILO CHAT CENTRAL ===
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    with st.form("form_pergunta", clear_on_submit=False):
        pergunta = st.text_input("Sua pergunta", placeholder="Digite sua pergunta aqui...", key="input_pergunta")
        enviado = st.form_submit_button("Enviar")

# === PROCESSA ENVIO ===
if enviado:
    if pergunta.strip():
        with st.spinner("Consultando agente..."):
            resposta = responder(pergunta, area)
        st.session_state.historico.append({
            "pergunta": pergunta,
            "resposta": resposta,
            "area": area,
            "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        st.success("Resposta obtida com sucesso!")
    else:
        st.warning("Por favor, digite uma pergunta.")

# === EXIBE ÚLTIMA RESPOSTA ===
if st.session_state.historico:
    ultima = st.session_state.historico[-1]
    st.markdown("### 🧾 Resposta do Agente")
    st.markdown(f"<div class='copy-box'>{ultima['resposta']}</div>", unsafe_allow_html=True)

    st.download_button("📥 Baixar como .txt", data=ultima["resposta"], file_name="resposta_agente.txt")

# === HISTÓRICO DE CONSULTAS ===
if st.session_state.historico:
    st.markdown("### 📚 Histórico de Consultas")
    for item in reversed(st.session_state.historico):
        with st.expander(f"📅 {item['data']} | ⚖️ {item['area']}"):
            st.markdown(f"**❓ Pergunta:** {item['pergunta']}")
            st.markdown("---")
            st.markdown(f"<div class='copy-box'>{item['resposta']}</div>", unsafe_allow_html=True)
