import os
import requests
import json
from flask import Flask, render_template, request, session

# --- Configurações da Aplicação ---
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.urandom(24)

# --- Configurações do Assistente (Ollama) ---
OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "qwen-rapido"
NOME_ARQUIVO_CONTEXTO = "assistente_academica.txt"

# NOVA CONFIGURAÇÃO: Limite de mensagens no histórico
MAX_HISTORICO = 4  # REDUZIDO: apenas 4 mensagens (2 trocas)
MAX_TOKENS_CONTEXTO = 1500  # Ajustado para o banco otimizado


def carregar_contexto():
    """Lê o arquivo de texto da base de conhecimento com limite de tamanho."""
    try:
        with open(NOME_ARQUIVO_CONTEXTO, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        # NOVO: Limita o tamanho do contexto para evitar sobrecarga
        if len(conteudo) > MAX_TOKENS_CONTEXTO:
            print(f"AVISO: Contexto muito grande ({len(conteudo)} chars). Limitando para {MAX_TOKENS_CONTEXTO} chars.")
            conteudo = conteudo[:MAX_TOKENS_CONTEXTO] + "\n[...contexto truncado para otimização...]"

        return conteudo
    except FileNotFoundError:
        print(f"AVISO: Arquivo de contexto '{NOME_ARQUIVO_CONTEXTO}' não encontrado.")
        return "Você é uma assistente acadêmica chamada UniHelp. Ajude o estudante de forma clara e objetiva."


def construir_prompt_sistema():
    """Cria a diretiva inicial SUPER REDUZIDA para o modelo."""
    contexto_texto = carregar_contexto()

    # NOVO: Prompt minimalista
    prompt = f"""Você é UniHelp. Responda usando apenas os dados abaixo:

{contexto_texto}"""

    return prompt


def limitar_historico(historico):
    """
    NOVO: Mantém apenas o prompt do sistema e as últimas N mensagens.
    """
    if len(historico) <= MAX_HISTORICO + 1:  # +1 por causa do system prompt
        return historico

    # Mantém o primeiro (system) e os últimos MAX_HISTORICO
    return [historico[0]] + historico[-(MAX_HISTORICO):]


def obter_resposta_assistente(historico_mensagens):
    """
    Envia o histórico LIMITADO para a API do Ollama e retorna a resposta.
    """
    try:
        # NOVO: Limita o histórico antes de enviar
        historico_limitado = limitar_historico(historico_mensagens)

        # NOVO: Log para debug - mostra quantas mensagens estão sendo enviadas
        print(f"\nINFO: Enviando {len(historico_limitado)} mensagens para o Ollama")
        print(f"INFO: Total de caracteres: {sum(len(msg['content']) for msg in historico_limitado)}")

        payload = {
            "model": MODELO,
            "messages": historico_limitado,
            "stream": False,
            "options": {
                "num_predict": 512,  # NOVO: Limita resposta para 512 tokens
                "temperature": 0.7
            }
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=90)  # Aumentado timeout
        response.raise_for_status()
        print("INFO: Resposta recebida do Ollama.")

        data = response.json()
        resposta = data.get("message", {}).get("content", "Desculpe, não consegui processar sua pergunta.")

        # NOVO: Log de quanto tempo levou (se disponível)
        if "eval_duration" in data:
            tempo_segundos = data["eval_duration"] / 1_000_000_000
            print(f"INFO: Tempo de resposta: {tempo_segundos:.2f}s")

        return resposta

    except requests.exceptions.Timeout:
        print("ERRO: Timeout - o modelo demorou mais de 90 segundos.")
        return "⏱️ A resposta está demorando muito. Tente fazer uma pergunta mais simples ou limpe a conversa."

    except requests.exceptions.RequestException as e:
        print(f"ERRO DE CONEXÃO: {e}")
        return "❌ Erro ao conectar com a IA. Verifique se o Ollama está rodando: `ollama serve`"

    except json.JSONDecodeError:
        print("ERRO: Resposta inválida do Ollama.")
        return "❌ Resposta inválida do servidor. Tente novamente."


@app.route('/', methods=['GET', 'POST'])
def home():
    """Renderiza a página principal e gerencia a conversa."""

    # Inicializa o histórico se não existir
    if 'historico' not in session:
        prompt_sistema = construir_prompt_sistema()
        session['historico'] = [{"role": "system", "content": prompt_sistema}]
        print("INFO: Nova sessão iniciada")

    if request.method == 'POST':
        pergunta_usuario = request.form.get('pergunta', '').strip()

        if pergunta_usuario:
            # Adiciona pergunta do usuário
            session['historico'].append({"role": "user", "content": pergunta_usuario})

            # Obtém resposta da IA
            resposta_ia = obter_resposta_assistente(session['historico'])

            # Adiciona resposta da IA
            session['historico'].append({"role": "assistant", "content": resposta_ia})

            # NOVO: Limita o histórico na sessão também (economiza memória)
            session['historico'] = limitar_historico(session['historico'])
            session.modified = True

    # Filtra mensagens do sistema para não exibir
    historico_para_exibir = [msg for msg in session.get('historico', []) if msg['role'] != 'system']

    return render_template('index.html', historico=historico_para_exibir)


@app.route('/limpar', methods=['POST'])
def limpar_historico():
    """Limpa o histórico de conversa da sessão."""
    session.pop('historico', None)
    print("INFO: Histórico limpo pelo usuário")
    return '', 204


# --- Execução da Aplicação ---
if __name__ == '__main__':
    print("=" * 60)
    print("INFO: Assistente Acadêmico Web - VERSÃO OTIMIZADA")
    print(f"INFO: Modelo: {MODELO}")
    print(f"INFO: Limite de histórico: {MAX_HISTORICO} mensagens")
    print(f"INFO: Limite de contexto: {MAX_TOKENS_CONTEXTO} caracteres")
    print(f"INFO: Carregando contexto de '{NOME_ARQUIVO_CONTEXTO}'")

    # Testa o carregamento do contexto
    contexto = carregar_contexto()
    print(f"INFO: Contexto carregado: {len(contexto)} caracteres")
    print("=" * 60)

    app.run(debug=True)