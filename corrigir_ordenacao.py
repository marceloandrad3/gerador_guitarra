#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

ARQUIVO = '/Users/marcelo/gerador_guitarra/gerador_web_dinamico.py'

with open(ARQUIVO, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Encontra e substitui a ordenacao atual
# O problema: ordena por score (soma das casas + span), o que favorece shapes com poucas cordas
# Solucao: ordenar por: mais cordas > menor posicao > menor span

old_ordenacao = 'ordenados = sorted(unicos, key=lambda x: x["score"])'

new_ordenacao = '''# Ordenacao inteligente: prioriza shapes canonicos (mais cordas, posicao baixa, span razoavel)
def ordenar_shapes(item):
    diagrama = item["diagrama"]
    casas = [int(c) for c in diagrama if c != 'X' and int(c) > 0]
    n_cordas = len([c for c in diagrama if c != 'X'])
    if casas:
        span = max(casas) - min(casas)
        min_casa = min(casas)
        score = min_casa + span
    else:
        span = 0
        min_casa = 0
        score = 0
    # Ordem de prioridade: mais cordas (desc), menor score (asc)
    return (-n_cordas, score, span)

ordenados = sorted(unicos, key=ordenar_shapes)'''

if old_ordenacao in conteudo:
    conteudo = conteudo.replace(old_ordenacao, new_ordenacao)
    print("[OK] Ordenacao corrigida: agora prioriza shapes com MAIS cordas tocadas")
else:
    # Tenta encontrar outra variacao
    if 'ordenados = sorted(' in conteudo:
        conteudo = re.sub(
            r'ordenados = sorted\([^)]+?\)',
            'ordenados = sorted(unicos, key=lambda x: (-len([c for c in x["diagrama"] if c != "X"]), sum([int(c) for c in x["diagrama"] if c != "X" and int(c) > 0]) + (max([int(c) for c in x["diagrama"] if c != "X" and int(c) > 0]) - min([int(c) for c in x["diagrama"] if c != "X" and int(c) > 0]) if [c for c in x["diagrama"] if c != "X" and int(c) > 0] else 0)))',
            conteudo
        )
        print("[OK] Ordenacao corrigida (padrao alternativo)")

with open(ARQUIVO, 'w', encoding='utf-8') as f:
    f.write(conteudo)

print("\nTestando C maior...")
import sys
sys.path.insert(0, '/Users/marcelo/gerador_guitarra')
from gerador_web_dinamico import gerar_dinamico

r = gerar_dinamico('C')
print(f"Total: {r['total_diagramas']}")
if r['total_diagramas'] > 0:
    primeiro = r['diagramas'][0]['diagrama']
    print(f"Primeiro shape: {primeiro}")
    
    # Verifica se é o canonico
    canonico = ['X', '3', '2', '0', '1', '0']
    if primeiro == canonico:
        print("✅ SHAPE CANONICO DE C MAIOR ENCONTRADO!")
    else:
        print(f"❌ Esperado: {canonico}")
        
    # Mostra top 5
    print("\nTop 5 shapes:")
    for i, d in enumerate(r['diagramas'][:5]):
        print(f"  {i+1}. {d['diagrama']}")

print("\nTestando F7M(11+)/C...")
r2 = gerar_dinamico('F7M(11+)/C')
if r2['total_diagramas'] > 0:
    print(f"Primeiro: {r2['diagramas'][0]['diagrama']}")
