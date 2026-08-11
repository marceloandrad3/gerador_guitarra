caminho = '/Users/marcelo/gerador_guitarra/gerador_web_dinamico.py'
with open(caminho, 'r', encoding='utf-8') as f:
    codigo = f.read()

# Substituir a lógica de deduplicação antiga pela nova
antigo = '''    vistos = set()
    unicos = []
    for s in shapes:
        key = tuple(s["diagrama"])
        if key not in vistos:
            vistos.add(key)
            unicos.append(s)
    return unicos'''

novo = '''    vistos = set()
    unicos = []
    for s in shapes:
        # Chave baseada nas notas reais: (corda, casa) onde casa > 0
        # Isso deduplica shapes que soam igual mesmo com cordas X diferentes
        key = frozenset((i, int(s["diagrama"][i])) for i in range(6) if s["diagrama"][i] not in ("X", "x", "0", "-1") and int(s["diagrama"][i]) > 0)
        if key not in vistos:
            vistos.add(key)
            unicos.append(s)
    return unicos'''

if antigo in codigo:
    codigo = codigo.replace(antigo, novo)
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(codigo)
    print("✅ Deduplicação corrigida com sucesso!")
else:
    print("⚠️ Bloco antigo não encontrado. Verifique se o arquivo já foi modificado.")
