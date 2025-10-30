import google.generativeai as genai

# Coloque sua chave aqui
GOOGLE_API_KEY = "AIzaSyANk03n6Z6pWzK7dAthderUXfIvJBSH5OI"  # ← Cole sua chave

genai.configure(api_key=GOOGLE_API_KEY)

print("=" * 60)
print("LISTANDO MODELOS DISPONÍVEIS NA SUA CONTA")
print("=" * 60)
print()

# Lista todos os modelos disponíveis
modelos_disponiveis = []

for modelo in genai.list_models():
    # Verifica se o modelo suporta generateContent (chat)
    if 'generateContent' in modelo.supported_generation_methods:
        print(f"✅ Modelo: {modelo.name}")
        print(f"   Descrição: {modelo.display_name}")
        print(f"   Métodos: {', '.join(modelo.supported_generation_methods)}")
        print("-" * 60)
        modelos_disponiveis.append(modelo.name)

print()
print("=" * 60)
print(f"TOTAL: {len(modelos_disponiveis)} modelos disponíveis para chat")
print("=" * 60)
print()

if modelos_disponiveis:
    print("🎯 COPIE UM DESSES NOMES para usar no seu código:")
    print()
    for modelo in modelos_disponiveis:
        # Remove o prefixo 'models/' se tiver
        nome_limpo = modelo.replace('models/', '')
        print(f"   modelo_gemini = genai.GenerativeModel('{nome_limpo}')")
    print()
else:
    print("❌ Nenhum modelo disponível. Verifique sua chave de API.")