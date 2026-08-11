#!/usr/bin/env python3
import shutil
ARQ = "servidor.py"
shutil.copy(ARQ, ARQ + ".bak_ligar_ambos")
linhas = open(ARQ, encoding="utf-8").read().split("\n")

alvo = "                resultado = remover_shapes_impossiveis(resultado)"
if alvo not in linhas:
    print("ERRO: linha alvo nao encontrada.")
else:
    i = linhas.index(alvo)
    novas = []
    if "                resultado = filtrar_pestana_dupla(resultado)" not in linhas:
        novas.append("                resultado = filtrar_pestana_dupla(resultado)")
    if "                resultado = filtrar_traste_alto(resultado)" not in linhas:
        novas.append("                resultado = filtrar_traste_alto(resultado)")
    if not novas:
        print("Ambos ja ligados.")
    else:
        linhas[i+1:i+1] = novas
        open(ARQ, "w", encoding="utf-8").write("\n".join(linhas))
        print("Ligados:", len(novas))

for n, l in enumerate(open(ARQ, encoding="utf-8").read().split("\n"), 1):
    if "filtrar_" in l and "def " not in l:
        print(f"  linha {n}: {l.strip()}")
