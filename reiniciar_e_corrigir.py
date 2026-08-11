#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import sys

print("=" * 60)
print("MATANDO SERVIDOR ANTIGO...")
print("=" * 60)

# Mata qualquer processo na porta 8000
subprocess.run("lsof -ti:8000 | xargs kill -9 2>/dev/null; echo 'Servidor antigo morto (se existia)'", shell=True)

# Limpa cache do Python
print("\nLimpando cache Python...")
for root, dirs, files in os.walk('/Users/marcelo/gerador_guitarra'):
    for d in dirs:
        if d == '__pycache__':
            path = os.path.join(root, d)
            subprocess.run(f"rm -rf '{path}'", shell=True)
print("Cache limpo.")

# Verifica se o gerador_web_dinamico.py está realmente corrigido
print("\n" + "=" * 60)
print("VERIFICANDO CORRECOES NO ARQUIVO...")
print("=" * 60)

with open('/Users/marcelo/gerador_guitarra/gerador_web_dinamico.py', 'r') as f:
    conteudo = f.read()

checks = {
    "Parser usa 'maj7'": "'maj7'" in conteudo and "'1', '3', '5', 'maj7'" in conteudo,
    "Filtro rejeita intrusos": "!= notas_permitidas" in conteudo,
    "Alias 7M existe": "'7M': 11" in conteudo,
}

for check, ok in checks.items():
    print(f"  {'✅' if ok else '❌'} {check}")

if not all(checks.values()):
    print("\n❌ ALGUNAS CORRECOES FALTAM! Aplicando agora...")
    # Reaplica correcoes
    if "'1', '3', '5', '7'" in conteudo:
        conteudo = conteudo.replace("'1', '3', '5', '7'", "'1', '3', '5', 'maj7'")
    if "issubset(notas_no_acorde)" in conteudo:
        conteudo = conteudo.replace("if not notas_permitidas.issubset(notas_no_acorde):", "if notas_no_acorde != notas_permitidas:")
    if "'7M':" not in conteudo:
        conteudo = conteudo.replace("'maj7': 11,", "'maj7': 11, '7M': 11, 'M7': 11,")
    with open('/Users/marcelo/gerador_guitarra/gerador_web_dinamico.py', 'w') as f:
        f.write(conteudo)
    print("✅ Correcoes reaplicadas.")

# Teste rapido
print("\n" + "=" * 60)
print("TESTE RAPIDO DO BACKEND...")
print("=" * 60)
sys.path.insert(0, '/Users/marcelo/gerador_guitarra')
from gerador_web_dinamico import gerar_dinamico

r = gerar_dinamico('F7M(11+)/C')
print(f"Total: {r['total_diagramas']} diagramas")

AFINACAO = [4, 9, 2, 7, 11, 4]
NOTAS_CORRETAS = {0, 4, 5, 9, 11}
intrusos = 0
for d in r['diagramas']:
    notas = set()
    for idx, f in enumerate(d['diagrama']):
        if f != 'X':
            notas.add((AFINACAO[idx] + int(f)) % 12)
    if notas != NOTAS_CORRETAS:
        intrusos += 1

print(f"Intrusos: {intrusos}")
print(f"Shape [X,3,3,2,0,0] presente: {'SIM' if any(d['diagrama']==['X','3','3','2','0','0'] for d in r['diagramas']) else 'NAO'}")

print("\n" + "=" * 60)
print("INICIANDO SERVIDOR NOVO...")
print("=" * 60)
print("Acesse: http://localhost:8000")
print("NO NAVEGADOR: aperte Cmd+Shift+R para limpar cache")
print("=" * 60)

# Inicia o servidor em background
os.system("cd /Users/marcelo/gerador_guitarra && python3 servidor.py &")
