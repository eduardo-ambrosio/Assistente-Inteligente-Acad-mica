import os
import google.generativeai as genai
from flask import Flask, render_template, request, session, redirect, url_for

# --- Configurações da Aplicação ---
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.urandom(24)

# --- Configurações do Gemini API ---
GOOGLE_API_KEY = "AIzaSyANk03n6Z6pWzK7dAthderUXfIvJBSH5OI"

# Configurando o Gemini
genai.configure(api_key=GOOGLE_API_KEY)
modelo_gemini = genai.GenerativeModel('gemini-2.5-flash')

NOME_ARQUIVO_CONTEXTO = "assistente_academica.txt"


def carregar_contexto():
    """Lê o arquivo de texto da base de conhecimento."""
    try:
        with open(NOME_ARQUIVO_CONTEXTO, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"AVISO: Arquivo de contexto '{NOME_ARQUIVO_CONTEXTO}' não encontrado.")
        return "Nenhum contexto específico fornecido."


def construir_prompt_sistema():
    """Cria a diretiva inicial para o modelo com base no contexto."""
    contexto_texto = carregar_contexto()
    prompt = f"""Você é UniHelp, uma assistente acadêmica da UniEVANGÉLICA.
Responda de forma clara e objetiva usando APENAS as informações abaixo.

BASE DE CONHECIMENTO:
{contexto_texto}

REGRAS:
- Responda apenas com dados da base
- Seja breve e direta
- Se não souber, peça mais informações"""

    return prompt


def obter_resposta_gemini(historico_mensagens):
    """Envia o histórico para o Gemini API e retorna a resposta."""
    try:
        historico_gemini = []

        for msg in historico_mensagens:
            if msg['role'] == 'system':
                historico_gemini.append({
                    'role': 'model',
                    'parts': [msg['content']]
                })
            elif msg['role'] == 'user':
                historico_gemini.append({
                    'role': 'user',
                    'parts': [msg['content']]
                })
            elif msg['role'] == 'assistant':
                historico_gemini.append({
                    'role': 'model',
                    'parts': [msg['content']]
                })

        print("\nINFO: Enviando requisição para o Gemini API...")

        chat = modelo_gemini.start_chat(history=historico_gemini[:-1])
        ultima_mensagem = historico_mensagens[-1]['content']
        resposta = chat.send_message(ultima_mensagem)

        print("INFO: Resposta recebida do Gemini! ⚡")
        return resposta.text

    except Exception as e:
        print(f"ERRO: Não foi possível conectar ao Gemini API.")
        print(f"Detalhe do erro: {e}")

        if "API_KEY" in str(e) or "invalid" in str(e).lower():
            return "❌ ERRO: Chave de API inválida. Verifique se você configurou corretamente a GOOGLE_API_KEY no código."
        elif "quota" in str(e).lower():
            return "⚠️ ERRO: Você atingiu o limite de requisições gratuitas do dia. Tente novamente amanhã."
        else:
            return f"❌ Erro ao conectar com o Gemini: {str(e)}"


# --- Rotas da Aplicação Web (Flask) ---

@app.route('/')
def index():
    """Redireciona para login se não estiver logado, senão para chat"""
    if 'usuario_logado' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        ra = request.form.get('ra')
        senha = request.form.get('password')

        # AQUI VOCÊ ADICIONA SUA LÓGICA DE AUTENTICAÇÃO
        # Por enquanto, aceita qualquer login para teste
        if ra and senha:
            session['usuario_logado'] = ra
            session['nome_usuario'] = ra  # Você pode pegar o nome real do banco
            return redirect(url_for('chat'))
        else:
            return render_template('login.html', erro="RA ou senha inválidos")

    return render_template('login.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Página de cadastro"""
    if request.method == 'POST':
        # Coleta os dados do formulário
        dados = {
            'nome_completo': request.form.get('nome_completo'),
            'email': request.form.get('email'),
            'cpf': request.form.get('cpf'),
            'ra': request.form.get('ra'),
            'curso': request.form.get('curso'),
            'senha': request.form.get('password')
        }

        # AQUI VOCÊ ADICIONA SUA LÓGICA DE CADASTRO NO BANCO
        print(f"Novo cadastro: {dados}")

        # Após cadastrar, redireciona para login
        return redirect(url_for('login'))

    return render_template('cadastro.html')


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    """Página do chat (protegida - precisa estar logado)"""
    # Verifica se está logado
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    # Inicializa histórico se não existir
    if 'historico' not in session:
        prompt_sistema = construir_prompt_sistema()
        session['historico'] = [{"role": "system", "content": prompt_sistema}]

    if request.method == 'POST':
        pergunta_usuario = request.form.get('pergunta', '').strip()

        if pergunta_usuario:
            # Adiciona pergunta do usuário
            session['historico'].append({"role": "user", "content": pergunta_usuario})

            # Obtém resposta do Gemini
            resposta_ia = obter_resposta_gemini(session['historico'])

            # Adiciona resposta da IA
            session['historico'].append({"role": "assistant", "content": resposta_ia})

            # Limita o histórico
            if len(session['historico']) > 9:
                session['historico'] = [session['historico'][0]] + session['historico'][-8:]

            session.modified = True

    # Filtra mensagens do sistema
    historico_para_exibir = [msg for msg in session.get('historico', []) if msg['role'] != 'system']

    return render_template('index.html', historico=historico_para_exibir)


@app.route('/limpar', methods=['POST'])
def limpar_historico():
    """Limpa o histórico de conversa da sessão."""
    session.pop('historico', None)
    print("INFO: Histórico limpo pelo usuário")
    return '', 204


@app.route('/logout')
def logout():
    """Faz logout do usuário"""
    session.clear()
    return redirect(url_for('login'))


# --- Execução da Aplicação ---
if __name__ == '__main__':
    print("=" * 60)
    print("INFO: Assistente Acadêmico UniHelp ⚡")
    print("=" * 60)
    print(f"✅ Chave de API configurada!")
    print(f"✅ Modelo: {modelo_gemini.model_name}")
    print(f"✅ Carregando contexto de '{NOME_ARQUIVO_CONTEXTO}'")

    contexto = carregar_contexto()
    print(f"✅ Contexto carregado: {len(contexto)} caracteres")
    print("\n🌐 Rotas disponíveis:")
    print("   • http://localhost:5000/       → Redireciona para login")
    print("   • http://localhost:5000/login  → Tela de login")
    print("   • http://localhost:5000/cadastro → Tela de cadastro")
    print("   • http://localhost:5000/chat   → Chat (precisa estar logado)")
    print("=" * 60)

    app.run(debug=True)