caminho = '/Users/marcelo/gerador_guitarra/gerador_web_dinamico.py'
with open(caminho, 'r', encoding='utf-8') as f:
    codigo = f.read()

# Substituir deduplicação atual por regra CAGED estrita
antigo = '''    vistos = set()
    unicos = []
    for s in shapes:
        # Chave: conjunto de notas MIDI reais produzidas (independe de cordas X)
        notas_midi = frozenset(
            (CORDAS_AFINACAO[i] + int(s["diagrama"][i])) 
            for i in range(6) 
            if s["diagrama"][i] not in ("X", "x", "0", "-1") and int(s["diagrama"][i]) >= 0
        )
        if notas_midi not in vistos:
            vistos.add(notas_midi)
            unicos.append(s)
    return unicos'''

novo = '''    vistos = set()
    unicos = []
    for s in shapes:
        # Regra CAGED: deduplicar por classes de pitch (ignorar oitava)
        # e exigir mínimo de 4 cordas tocadas (padrão indústria)
        cordas_tocadas = [i for i in range(6) if s["diagrama"][i] not in ("X", "x", "0", "-1") and int(s["diagrama"][i]) >= 0]
        if len(cordas_tocadas) < 4:
            continue
        classes_pitch = frozenset(
            (CORDAS_AFINACAO[i] + int(s["diagrama"][i])) % 12 
            for i in cordas_tocadas
        )
        if classes_pitch not in vistos:
            vistos.add(classes_pitch)
            unicos.append(s)
    return unicos'''

if antigo in codigo:
    codigo = codigo.replace(antigo, novo)
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(codigo)
    print("✅ Regra CAGED aplicada: dedup por pitch class + mín 4 cordas")
else:
    print("⚠️ Bloco não encontrado. Mostre o conteúdo atual da função gerar_shapes_dinamicos")
