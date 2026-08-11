# === CORREÇÃO 1: Backend - Regra CAGED correta (5 formas) ===
caminho_backend = '/Users/marcelo/gerador_guitarra/gerador_web_dinamico.py'
with open(caminho_backend, 'r', encoding='utf-8') as f:
    codigo = f.read()

# Substituir deduplicação atual pela regra CAGED definitiva
# Chave = menor casa usada (posição no braço) -> agrupa por região CAGED
antigo_dedup = '''    vistos = set()
    unicos = []
    for s in shapes:
        # Regra CAGED final: 
        # - Mínimo 4 cordas tocadas
        # - Chave = (menor_casa_usada, tuple de casas relativas à menor)
        #   Isso agrupa shapes na mesma posição do braço, ignorando cordas X
        cordas_tocadas = [i for i in range(6) if s["diagrama"][i] not in ("X", "x", "0", "-1") and int(s["diagrama"][i]) >= 0]
        if len(cordas_tocadas) < 4:
            continue
        casas = [int(s["diagrama"][i]) for i in cordas_tocadas]
        min_casa = min(casas)
        # Forma relativa: diferenças das casas em relação à menor
        forma_relativa = tuple(sorted(c - min_casa for c in casas))
        key = (min_casa, forma_relativa)
        if key not in vistos:
            vistos.add(key)
            unicos.append(s)
    return unicos'''

novo_dedup = '''    vistos = set()
    unicos = []
    for s in shapes:
        # Regra CAGED definitiva (Cifra Club / JustinGuitar):
        # - Mínimo 4 cordas tocadas
        # - Chave = menor casa usada (define a região/shape CAGED no braço)
        #   Shapes na mesma região com mesmas notas = duplicata
        cordas_tocadas = [i for i in range(6) if s["diagrama"][i] not in ("X", "x", "0", "-1") and int(s["diagrama"][i]) >= 0]
        if len(cordas_tocadas) < 4:
            continue
        casas = [int(s["diagrama"][i]) for i in cordas_tocadas]
        min_casa = min(casas)
        # Agrupar por região do braço (cada 3-4 casas = 1 shape CAGED)
        regiao = min_casa // 3
        key = regiao
        if key not in vistos:
            vistos.add(key)
            unicos.append(s)
    return unicos'''

if antigo_dedup in codigo:
    codigo = codigo.replace(antigo_dedup, novo_dedup)
    with open(caminho_backend, 'w', encoding='utf-8') as f:
        f.write(codigo)
    print("✅ Backend: regra CAGED por região aplicada")
else:
    print("⚠️ Bloco backend não encontrado")

# === CORREÇÃO 2: Frontend - Botão dinâmico correto ===
caminho_frontend = '/Users/marcelo/gerador_guitarra/index.html'
with open(caminho_frontend, 'r', encoding='utf-8') as f:
    html = f.read()

# Corrigir a linha 174 exatamente como está
antigo_btn = """if(data.diagramas.length>1&&!mostrarTodos)h+='<div class="ver-mais-container"><button class="ver-mais-btn" onclick="document.getElementById(\\'resultado\\').dataset.mostrarTodos=\\'true\\';buscarAcorde()">Ver more ('+(data.diagramas.length-5)+' shapes adicionais)</button></div>';"""

# Tentar com o texto exato do grep
antigo_btn_real = "if(data.diagramas.length>1&&!mostrarTodos)h+='<div class=\"ver-mais-container\"><button class=\"ver-mais-btn\" onclick=\"document.getElementById(\\'resultado\\').dataset.mostrarTodos=\\'true\\';buscarAcorde()\">Ver mais ('+(data.diagramas.length-5)+' shapes adicionais)</button></div>';"

novo_btn = "if(data.total_diagramas>1&&!mostrarTodos)h+='<div class=\"ver-mais-container\"><button class=\"ver-mais-btn\" onclick=\"document.getElementById(\\'resultado\\').dataset.mostrarTodos=\\'true\\';buscarAcorde()\">+'+(data.total_diagramas-1)+' variações</button></div>';"

if antigo_btn_real in html:
    html = html.replace(antigo_btn_real, novo_btn)
    with open(caminho_frontend, 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ Frontend: botão corrigido para usar total_diagramas")
else:
    print("⚠️ Texto do botão não encontrado exatamente. Tentando alternativa...")
    # Alternativa: substituir só a parte do texto
    if "data.diagramas.length-5" in html:
        html = html.replace("data.diagramas.length-5", "data.total_diagramas-1")
        html = html.replace("Ver mais (", "+")
        html = html.replace(" shapes adicionais)", " variações")
        html = html.replace("data.diagramas.length>1", "data.total_diagramas>1")
        with open(caminho_frontend, 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ Frontend: botão corrigido via substituição parcial")
    else:
        print("❌ Não foi possível corrigir o frontend automaticamente")
