# assistente_academico_ollama.py
import requests, json, sys, time

URL = "http://localhost:11434/api/chat"   # endpoint do Ollama
MODELO = "gemma3:1b"                     # modelo recomendado (pode trocar)
ATRASO = 0.02                             # atraso por palavra (efeito digitação)
SISTEMA = "Você é uma tutora acadêmica clara e didática."  # papel padrão

# Novo: nome do arquivo de contexto acadêmico
NOME_ARQUIVO_CONTEXTUAL = "assistente_academica.txt"

# Histórico de mensagens (memória)
mensagens = [{"role": "system", "content": SISTEMA}]

def conversar(user_text: str) -> str:
    """Envia o histórico + pergunta do usuário e streama a resposta."""
    mensagens.append({"role": "user", "content": user_text})

    payload = {"model": MODELO, "messages": mensagens, "stream": True}

    r = requests.post(URL, json=payload, stream=True, timeout=600)
    r.raise_for_status()

    buffer, resposta_completa = "", ""
    print("Assistente:", end=" ", flush=True)

    for linha in r.iter_lines(decode_unicode=True):
        if not linha:
            continue
        data = json.loads(linha)

        pedaço = (data.get("message", {}) or {}).get("content", "") or data.get("response", "")
        if pedaço:
            buffer += pedaço
            resposta_completa += pedaço

            while " " in buffer:
                palavra, buffer = buffer.split(" ", 1)
                sys.stdout.write(palavra + " "); sys.stdout.flush()
                time.sleep(ATRASO)

        if data.get("done"):
            if buffer:
                sys.stdout.write(buffer); sys.stdout.flush()
            print()
            break

    mensagens.append({"role": "assistant", "content": resposta_completa})
    return resposta_completa

if __name__ == "__main__":
    print("====== UniHelp ======")

    # BLOCO NOVO: Carrega a base de conhecimento acadêmica
    try:
        with open(NOME_ARQUIVO_CONTEXTUAL, "r", encoding="utf-8") as f:
            contexto_texto = f.read()

        SISTEMA_ACADEMICO = f"""
Você é uma assistente acadêmica inteligente chamada *UniHelp*.
Sua função é auxiliar estudantes em tarefas de aprendizado, revisão e aplicação de conteúdos acadêmicos,
com base exclusivamente nas informações fornecidas na base de conhecimento abaixo.

Regras de comportamento:
- Explique de forma clara, didática e organizada.
- Use exemplos e analogias quando forem úteis.
- Responda apenas sobre temas presentes na base de conhecimento.
- Caso o assunto esteja fora do escopo, informe isso e sugira fontes confiáveis.
- Mantenha um tom formal, cordial e instrutivo.

--- BASE DE CONHECIMENTO ---
{contexto_texto}
--- FIM DA BASE ---
"""
        SISTEMA = SISTEMA_ACADEMICO
        mensagens = [{"role": "system", "content": SISTEMA}]
        print(f"INFO: Base acadêmica '{NOME_ARQUIVO_CONTEXTUAL}' carregada com sucesso. Assistente pronta!\n")

    except FileNotFoundError:
        print(f"AVISO: Arquivo '{NOME_ARQUIVO_CONTEXTUAL}' não encontrado. Usando modo genérico.\n")

    print("Comandos: /sair  /limpar\n")

    try:
        while True:
            pergunta = input("Você: ").strip()
            if not pergunta:
                continue
            if pergunta.lower() == "/sair":
                print("Até mais!"); break
            if pergunta.lower() == "/limpar":
                mensagens[:] = [{"role": "system", "content": SISTEMA}]
                print("[Histórico limpo]\n"); continue
            conversar(pergunta)
    except KeyboardInterrupt:
