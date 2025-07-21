import openai
import streamlit as st
import json
import os
import uuid
import datetime
from typing import Dict, Any

# === CONFIGURAÇÃO ===
# ⚠️ Use st.secrets ou variável de ambiente no deploy
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

# === MODELO PADRÃO ===
modelo_default = "gpt-4o"

def calcular_custo(tokens_input: int, tokens_output: int, modelo: str) -> float:
    precos = {
        "gpt-4o": {"input": 0.005 / 1000, "output": 0.015 / 1000},
        "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
        "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000}
    }
    if modelo in precos:
        return round(
            tokens_input * precos[modelo]["input"] +
            tokens_output * precos[modelo]["output"], 6
        )
    return 0.0

def gerar_id_sessao() -> str:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

def obter_usuario_atual() -> str:
    return st.session_state.get("usuario_logado", "admin@cerizze.com")

def salvar_log(log_entry: Dict[str, Any]):
    try:
        os.makedirs("data/logs", exist_ok=True)
        path = f"data/logs/interacoes_{datetime.date.today().strftime('%Y%m')}.jsonl"
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        st.error(f"Erro ao salvar log: {e}")

def atualizar_metricas_sessao(log: Dict[str, Any]):
    if "metricas_sessao" not in st.session_state:
        st.session_state.metricas_sessao = {
            "consultas_realizadas": 0,
            "tokens_utilizados": 0,
            "custo_acumulado": 0.0,
            "areas_consultadas": set(),
            "tempo_total": 0.0
        }

    m = st.session_state.metricas_sessao
    m["consultas_realizadas"] += 1
    m["tokens_utilizados"] += log.get("tokens_total", 0)
    m["custo_acumulado"] += log.get("custo_estimado", 0)
    m["areas_consultadas"].add(log.get("area", ""))
    m["tempo_total"] += log.get("tempo_resposta", 0)

def exibir_metricas_sidebar():
    if "metricas_sessao" not in st.session_state:
        return
    m = st.session_state.metricas_sessao
    st.sidebar.markdown("### 📊 Métricas da Sessão")
    st.sidebar.metric("Consultas", m["consultas_realizadas"])
    st.sidebar.metric("Tokens", f"{m['tokens_utilizados']:,}")
    st.sidebar.metric("Custo", f"${m['custo_acumulado']:.4f}")
    st.sidebar.metric("Tempo Médio", f"{m['tempo_total'] / max(1, m['consultas_realizadas']):.1f}s")
    if m["areas_consultadas"]:
        st.sidebar.write("**Áreas consultadas:**")
        for area in m["areas_consultadas"]:
            st.sidebar.write(f"• {area}")

def responder(pergunta: str, area: str, modelo: str = modelo_default) -> str:
    try:
        prompt = f"Você é um advogado especialista em Direito {area}. Responda à seguinte pergunta jurídica com clareza e objetividade:\n\n{pergunta}"
        inicio = datetime.datetime.now()

        from openai import OpenAI

        client = OpenAI()
        resposta = client.chat.completions.create(
    model=modelo,
    messages=[
        {"role": "system", "content": f"Você é um especialista em Direito {area} brasileiro."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=1200
)

        fim = datetime.datetime.now()
        conteudo = resposta.choices[0].message.content.strip()
        tokens_input = resposta.usage.prompt_tokens
        tokens_output = resposta.usage.completion_tokens
        tempo_resposta = (fim - inicio).total_seconds()
        custo_estimado = calcular_custo(tokens_input, tokens_output, modelo)

        log_entry = {
            "id": str(uuid.uuid4()),
            "session_id": gerar_id_sessao(),
            "user": obter_usuario_atual(),
            "area": area,
            "pergunta": pergunta,
            "resposta": conteudo,
            "modelo": modelo,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "tokens_total": tokens_input + tokens_output,
            "custo_estimado": custo_estimado,
            "tempo_resposta": tempo_resposta,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "sucesso"
        }

        salvar_log(log_entry)
        atualizar_metricas_sessao(log_entry)

        return conteudo

    except Exception as e:
        st.error(f"❌ Erro ao consultar o modelo: {str(e)}")
        return "❌ Ocorreu um erro ao consultar a IA. Tente novamente em instantes."
