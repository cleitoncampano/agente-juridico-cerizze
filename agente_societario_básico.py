import os
from openai import OpenAI
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Inicializa cliente
client = OpenAI(api_key=api_key)

def montar_prompt(pergunta_usuario):
    return f"""
Você é um agente de IA jurídico especializado em Direito Societário Brasileiro da banca Cerizze. Atue com ética, visão de negócios, excelência técnica e foco prático.

Responda SEMPRE nos seguintes tópicos:
1. **Contexto**
2. **Análise jurídica**
3. **Recomendações e próximos passos**
4. **Referências normativas**
5. **Limitações**

Pergunta:
\"\"\"{pergunta_usuario}\"\"\"
"""

def responder(pergunta_usuario):
    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Você é um especialista em Direito Societário Brasileiro."},
            {"role": "user", "content": montar_prompt(pergunta_usuario)}
        ],
        temperature=0.3,
        max_tokens=1024
    )
    return resposta.choices[0].message.content.strip()

# Execução interativa
if __name__ == "__main__":
    print("\n🔷 Agente Societário Jurídico Cerizze")
    print("Digite sua dúvida (ou pressione Enter para sair):\n")

    while True:
        pergunta = input("> ")
        if not pergunta.strip():
            print("Encerrando...\n")
            break
        resposta = responder(pergunta)
        print("\n--- RESPOSTA DO AGENTE ---\n")
        print(resposta)
        print("\n--------------------------\n")
