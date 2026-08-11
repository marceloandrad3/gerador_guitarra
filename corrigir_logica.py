caminho = '/Users/marcelo/gerador_guitarra/gerador_web_dinamico.py'
with open(caminho, 'r', encoding='utf-8') as f:
    codigo = f.read()

# Correção 1: Validar que TODAS as notas tocadas pertencem ao acorde
antigo_validacao = '''            if notas_presentes == set(notas_alvo) and len(casas_usadas) >= 3:'''
novo_validacao = '''            # Validação estrita: todas as notas tocadas devem pertencer ao acorde
            notas_tocadas = set()
            for i in range(6):
                if diagrama[i] not in ("X", "x", "0", "-1"):
                    midi_nota = (CORDAS_AFINACAO[i] + int(diagrama[i])) % 12
                    notas_tocadas.add(midi_nota)
            if notas_tocadas.issubset(set(notas_alvo)) and notas_presentes == set(notas_alvo) and len(casas_usadas) >= 3:'''

if antigo_validacao in codigo:
    codigo = codigo.replace(antigo_validacao, novo_validacao)
else:
    print("⚠️ Bloco de validação não encontrado")

# Correção 2: Deduplicação por conjunto de notas MIDI reais (não por diagrama bruto)
antigo_dedup = '''    vistos = set()
    unicos = []
    for s in shapes:
        key = tuple(s["diagrama"])
        if key not in vistos:
            vistos.add(key)
            unicos.append(s)
    return unicos'''

novo_dedup = '''    vistos = set()
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

if antigo_dedup in codigo:
    codigo = codigo.replace(antigo_dedup, novo_dedup)
else:
    # Tentar com a versão já corrigida anteriormente
    antigo_dedup_v2 = '''    vistos = set()
    unicos = []
    for s in shapes:
        # Chave baseada nas notas reais: (corda, casa) onde casa > 0
        # Isso deduplica shapes que soam igual mesmo com cordas X diferentes
        key = frozenset((i, int(s["diagrama"][i])) for i in range(6) if s["diagrama"][i] not in ("X", "x", "0", "-1") and int(s["diagrama"][i]) > 0)
        if key not in vistos:
            vistos.add(key)
            unicos.append(s)
    return unicos'''
    if antigo_dedup_v2 in codigo:
        codigo = codigo.replace(antigo_dedup_v2, novo_dedup)
    else:
        print("⚠️ Bloco de deduplicação não encontrado")

with open(caminho, 'w', encoding='utf-8') as f:
    f.write(codigo)

print("✅ Correções aplicadas: validação estrita + deduplicação por notas MIDI")
