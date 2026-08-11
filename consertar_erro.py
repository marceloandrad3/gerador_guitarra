#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

ARQUIVO = '/Users/marcelo/gerador_guitarra/gerador_web_dinamico.py'

with open(ARQUIVO, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Remove a função ordenar_shapes quebrada que foi inserida no lugar errado
padrao = r'# Ordenacao inteligente: prioriza shapes canonicos.*?    return \(-n_cordas, score, span\)\n'
conteudo = re.sub(padrao, '', conteudo, flags=re.DOTALL)

# Substitui a linha de ordenação por uma lambda inline correta
old = 'ordenados = sorted(unicos, key=lambda x: x["score"])'
new = 'ordenados = sorted(unicos, key=lambda x: (-len([c for c in x["diagrama"] if c != "X"]), sum([int(c) for c in x["diagrama"] if c != "X" and int(c) > 0]) + (max([int(c) for c in x["diagrama"] if c != "X" and int(c) > 0]) - min([int(c) for c in x["diagrama"] if c != "X" and int(c) > 0]) if [c for c in x["diagrama"] if c != "X" and int(c) > 0] else 0)))'

if old in conteudo:
    conteudo = conteudo.replace(old, new)
    print("[OK] Ordenacao corrigida")
else:
    print("❌ Nao encontrou a linha de ordenacao")
    # Tenta outro padrao
    old2 = 'ordenados = sorted(unicos, key=ordenar_shapes)'
    if old2 in conteudo:
        conteudo = conteudo.replace(old2, new)
        print("[OK] Ordenacao corrigida (padrao 2)")

with open(ARQUIVO, 'w', encoding='utf-8') as f:
    f.write(conteudo)

# Testa
print("\nTestando...")
import sys
sys.path.insert(0, '/Users/marcelo/gerador_guitarra')
from gerador_web_dinamico import gerar_dinamico

r = gerar_dinamico('C')
print(f"C maior - Total: {r['total_diagramas']}")
if r['total_diagramas'] > 0:
    print(f"Primeiro: {r['diagramas'][0]['diagrama']}")
    canonico = ['X', '3', '2', '0', '1', '0']
    if r['diagramas'][0]['diagrama'] == canonico:
        print("✅ CANONICO!")

r2 = gerar_dinamico('F7M(11+)/C')
print(f"\nF7M(11+)/C - Total: {r2['total_diagramas']}")
if r2['total_diagramas'] > 0:
    print(f"Primeiro: {r2['diagramas'][0]['diagrama']}")
