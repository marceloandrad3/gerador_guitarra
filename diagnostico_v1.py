#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

print("=" * 70)
print("DIAGNOSTICO V1 — Analisando seu gerador_web_dinamico.py")
print("=" * 70)

# Tenta importar o modulo do usuario
try:
    sys.path.insert(0, '/Users/marcelo/gerador_guitarra')
    from gerador_web_dinamico import gerar_dinamico, parse_simbolo
    print("[OK] Modulo gerador_web_dinamico importado com sucesso.\n")
except Exception as e:
    print(f"[ERRO] Nao consegui importar: {e}")
    sys.exit(1)

# Teste 1: Parser
print("-" * 70)
print("TESTE 1: O que o parser entende de 'F7M(11+)/C'?")
print("-" * 70)
try:
    tonica, formula, baixo, qualidade = parse_simbolo("F7M(11+)/C")
    print(f"  Tônica : {tonica}")
    print(f"  Formula: {formula}")
    print(f"  Baixo  : {baixo}")
    print(f"  Nome   : {qualidade}")
except Exception as e:
    print(f"  [ERRO no parser]: {e}")

# Teste 2: Geracao
print("\n" + "-" * 70)
print("TESTE 2: Gerando diagramas para 'F7M(11+)/C'...")
print("-" * 70)
resultado = gerar_dinamico("F7M(11+)/C")
print(f"  Total de diagramas: {resultado.get('total_diagramas', 0)}")

# Teste 3: Verificando intrusos nota por nota
print("\n" + "-" * 70)
print("TESTE 3: Verificando se ha NOTAS INTRUSAS nos diagramas")
print("-" * 70)

AFINACAO = [4, 9, 2, 7, 11, 4]
NOMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

# Notas CORRETAS de F7M(#11): F, A, C, E, B  -> pitch classes: 5, 9, 0, 4, 11
NOTAS_CORRETAS = {0, 4, 5, 9, 11}

diagramas = resultado.get('diagramas', [])
intrusos = 0
corretos = 0

for i, d in enumerate(diagramas[:20]):  # Analisa os 20 primeiros
    frets = d.get('diagrama', [])
    notas_presentes = set()
    notas_nomes = []
    for idx, f in enumerate(frets):
        if f != 'X':
            pc = (AFINACAO[idx] + int(f)) % 12
            notas_presentes.add(pc)
            notas_nomes.append(NOMES[pc])
    
    tem_intruso = notas_presentes != NOTAS_CORRETAS
    if tem_intruso:
        intrusos += 1
        status = "❌ INTRUSO!"
    else:
        corretos += 1
        status = "✅ OK"
    
    print(f"  #{i+1:2d} | frets={frets} | notas={notas_nomes} | {status}")

print(f"\n  Resumo dos 20 primeiros: {corretos} corretos, {intrusos} com intrusos")

# Teste 4: Shape especifico que deveria aparecer
print("\n" + "-" * 70)
print("TESTE 4: O shape [X, 3, 3, 2, 0, 0] esta nos resultados?")
print("-" * 70)
shape_alvo = ['X', '3', '3', '2', '0', '0']
encontrado = False
for d in diagramas:
    if d.get('diagrama') == shape_alvo:
        encontrado = True
        break
print(f"  Resultado: {'SIM ✅' if encontrado else 'NAO ❌ (este e o problema!)'}")

print("\n" + "=" * 70)
print("FIM DO DIAGNOSTICO. Copie TUDO acima e envie de volta.")
print("=" * 70)
