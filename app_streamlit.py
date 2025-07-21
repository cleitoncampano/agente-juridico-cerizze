import json
import datetime
import uuid
from typing import Dict, Any
import os
import streamlit as st

def calcular_custo(tokens_input: int, tokens_output: int, modelo: str) -> float:
    """Calcula custo aproximado baseado nos preços da OpenAI"""
    precos = {
        "gpt-4o": {"input": 0.005/1000, "output": 0.015/1000},
        "gpt-3.5-turbo": {"input": 0.0005/1000, "output": 0.0015/1000}
    }
    
    if modelo in precos:
        custo = (tokens_input * precos[modelo]["input"] + 
                tokens_output * precos[modelo]["output"])
        return round(custo, 6)
    return 0.0

def obter_usuario_atual() -> str:
    """Retorna e-mail fixo para testes"""
    return "admin@cerizze.com"

def gerar_id_sessao() -> str:
    """Gera ID único para sessão de chat"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

def responder_com_logging(pergunta: str, area: str) -> Dict[str, Any]:
    """Função principal com logging completo e tratamento de erros"""
    try:
        prompt = montar_prompt(pergunta, area)
        inicio = datetime.datetime.now()
        
        # Chamada para OpenAI
        resposta = client.chat.completions.create(
            model=modelo,
            messages=[
                {"role": "system", "content": f"Você é um especialista em Direito {area} Brasileiro."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1200
        )

        fim = datetime.datetime.now()
        tempo_resposta = (fim - inicio).total_seconds()

        # Extrai dados da resposta
        conteudo = resposta.choices[0].message.content.strip()
        tokens_input = resposta.usage.prompt_tokens
        tokens_output = resposta.usage.completion_tokens
        custo_estimado = calcular_custo(tokens_input, tokens_output, modelo)

        # Monta log completo
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

        return {
            "resposta": conteudo,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "custo": custo_estimado,
            "tempo": tempo_resposta,
            "sucesso": True
        }

    except Exception as e:
        # Log de erro
        log_erro = {
            "id": str(uuid.uuid4()),
            "session_id": gerar_id_sessao(),
            "user": obter_usuario_atual(),
            "area": area,
            "pergunta": pergunta,
            "modelo": modelo,
            "erro": str(e),
            "timestamp": datetime.datetime.now().isoformat(),
            "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "erro"
        }
        
        salvar_log(log_erro)
        
        return {
            "resposta": f"❌ Erro ao processar consulta: {str(e)}",
            "sucesso": False,
            "erro": str(e)
        }

def salvar_log(log_entry: Dict[str, Any]):
    """Salva log no arquivo JSONL"""
    try:
        os.makedirs("data/logs", exist_ok=True)
        arquivo_log = f"data/logs/interacoes_{datetime.date.today().strftime('%Y%m')}.jsonl"
        
        with open(arquivo_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        st.error(f"Erro ao salvar log: {e}")

def atualizar_metricas_sessao(log_entry: Dict[str, Any]):
    """Atualiza métricas da sessão atual"""
    if "metricas_sessao" not in st.session_state:
        st.session_state.metricas_sessao = {
            "consultas_realizadas": 0,
            "tokens_utilizados": 0,
            "custo_acumulado": 0.0,
            "areas_consultadas": set(),
            "tempo_total": 0.0
        }
    
    metricas = st.session_state.metricas_sessao
    metricas["consultas_realizadas"] += 1
    metricas["tokens_utilizados"] += log_entry.get("tokens_total", 0)
    metricas["custo_acumulado"] += log_entry.get("custo_estimado", 0)
    metricas["areas_consultadas"].add(log_entry.get("area", ""))
    metricas["tempo_total"] += log_entry.get("tempo_resposta", 0)

def exibir_metricas_sidebar():
    """Exibe métricas na sidebar"""
    if "metricas_sessao" in st.session_state:
        metricas = st.session_state.metricas_sessao
        
        st.sidebar.markdown("### 📊 Métricas da Sessão")
        st.sidebar.metric("Consultas", metricas["consultas_realizadas"])
        st.sidebar.metric("Tokens", f"{metricas['tokens_utilizados']:,}")
        st.sidebar.metric("Custo", f"${metricas['custo_acumulado']:.4f}")
        st.sidebar.metric("Tempo Médio", f"{metricas['tempo_total']/max(1, metricas['consultas_realizadas']):.1f}s")
        
        if metricas["areas_consultadas"]:
            st.sidebar.write("**Áreas consultadas:**")
            for area in metricas["areas_consultadas"]:
                st.sidebar.write(f"• {area}")

def responder(pergunta, area):
    """Wrapper para manter compatibilidade com código existente"""
    resultado = responder_com_logging(pergunta, area)
    return resultado["resposta"]
