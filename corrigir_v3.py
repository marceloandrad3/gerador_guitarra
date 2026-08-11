#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

ARQUIVO = '/Users/marcelo/gerador_guitarra/gerador_web_dinamico.py'

with open(ARQUIVO, 'r', encoding='utf-8') as f:
    conteudo = f.read()

print("=" * 60)
print("ESTADO ATUAL DO ARQUIVO (trechos relevantes):")
print("=" * 60)

# Mostra a linha do filtro de notas
for i, linha in enumerate(conteudo.split('\n'), 1):
    if 'issubset' in linha or 'notas_no_acorde' in linha and 'notas_permitidas' in linha:
        print(f"  Linha {i}: {linha.strip()}")

# Mostra a linha do maj7 no dicionario
for i, linha in enumerate(conteudo.split('\n'), 1):
    if "'maj7'" in linha and ':' in linha:
        print(f"  Linha {i}: {linha.strip()}")

print("\n" + "=" * 60)
print("APLICANDO CORRECOES RESTANTES...")
print("=" * 60)

correcoes = 0

# CORRECAO 2: Filtro de intrusos (qualquer variacao de issubset)
padrao_filtro = r'if\s+not\s+\w+\.issubset\(\w+\):'
if re.search(padrao_filtro, conteudo):
    conteudo = re.sub(
        r'(if\s+not\s+)(\w+)(\.issubset\()(\w+)(\):)',
        r'if \4 != \2:',
        conteudo
    )
    correcoes += 1
    print("[OK] Correcao 2: Filtro agora rejeita intrusos")

# CORRECAO 3: Adicionar aliases 7M e M7
if "'7M':" not in conteudo:
    conteudo = conteudo.replace("'maj7': 11,", "'maj7': 11, '7M': 11, 'M7': 11,")
    correcoes += 1
    print("[OK] Correcao 3: Adicionados aliases '7M' e 'M7'")

with open(ARQUIVO, 'w', encoding='utf-8') as f:
    f.write(conteudo)

print(f"\n✅ {correcoes} correcao(oes) aplicadas.")
print("\nTestando agora...")

# Teste rapido
import sys
sys.path.insert(0, '/Users/marcelo/gerador_guitarra')
from gerador_web_dinamico import gerar_dinamico

r = gerar_dinamico('F7M(11+)/C')
print(f"\nTotal de diagramas: {r['total_diagramas']}")

AFINACAO = [4, 9, 2, 7, 11, 4]
NOMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
NOTAS_CORRETAS = {0, 4, 5, 9, 11}

corretos = 0
intrusos = 0
shape_alvo_encontrado = False

for d in r['diagramas']:
    frets = d.get('diagrama', [])
    notas = set()
    for idx, f in enumerate(frets):
        if f != 'X':
            notas.add((AFINACAO[idx] + int(f)) % 12)
    if notas == NOTAS_CORRETAS:
        corretos += 1
    else:
        intrusos += 1
    if frets == ['X', '3', '3', '2', '0', '0']:
        shape_alvo_encontrado = True

print(f"Diagramas corretos: {corretos}")
print(f"Diagramas com intrusos: {intrusos}")
print(f"Shape [X,3,3,2,0,0] encontrado: {'SIM ✅' if shape_alvo_encontrado else 'NAO ❌'}")
