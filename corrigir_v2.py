#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORRIGIR_V2.PY — Aplica 3 correções no gerador_web_dinamico.py
"""
import re

ARQUIVO = '/Users/marcelo/gerador_guitarra/gerador_web_dinamico.py'

with open(ARQUIVO, 'r', encoding='utf-8') as f:
    conteudo = f.read()

original = conteudo
correcoes = 0

# CORRECAO 1: Parser deve usar 'maj7' em vez de '7' quando detecta 7M/maj7
old1 = "    elif 'maj7' in rest or '7m' in rest or '7+' in rest:\n        formula = ['1', '3', '5', '7']"
new1 = "    elif 'maj7' in rest or '7m' in rest or '7+' in rest:\n        formula = ['1', '3', '5', 'maj7']"
if old1 in conteudo:
    conteudo = conteudo.replace(old1, new1)
    correcoes += 1
    print("[OK] Correcao 1: Parser agora usa 'maj7' em vez de '7' para 7M")

# CORRECAO 2: Filtro de intrusos — issubset → igualdade estrita
old2 = "        if not notas_permitidas.issubset(notas_no_acorde):\n            continue"
new2 = "        if notas_no_acorde != notas_permitidas:\n            continue"
if old2 in conteudo:
    conteudo = conteudo.replace(old2, new2)
    correcoes += 1
    print("[OK] Correcao 2: Filtro agora rejeita notas intrusas (igualdade estrita)")

# CORRECAO 3: Adiciona '7M' e 'M7' como aliases de maj7 no INTERVALOS_MAP
# Verifica se ja existe
if "'7M':" not in conteudo and "'M7':" not in conteudo:
    # Procura a linha do maj7 e adiciona aliases depois
    old3 = "    'maj7': 11, '7m': 11,"
    new3 = "    'maj7': 11, '7m': 11, '7M': 11, 'M7': 11,"
    if old3 in conteudo:
        conteudo = conteudo.replace(old3, new3)
        correcoes += 1
        print("[OK] Correcao 3: Adicionados aliases '7M' e 'M7' para maj7")

if conteudo != original:
    with open(ARQUIVO, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"\n✅ {correcoes} correcoes aplicadas em {ARQUIVO}")
else:
    print("\n⚠️ Nenhuma correcao aplicada (talvez ja esteja corrigido?)")

print("\nProximo passo: Rode o teste para verificar:")
print("  python3 -c \"from gerador_web_dinamico import gerar_dinamico; r=gerar_dinamico('F7M(11+)/C'); print('Total:', r['total_diagramas']); [print(d['diagrama']) for d in r['diagramas'][:5]]\"")
