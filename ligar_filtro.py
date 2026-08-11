#!/usr/bin/env python3
import shutil

ARQ = "servidor.py"
shutil.copy(ARQ, ARQ + ".bak_antes_ligar_filtro")
src = open(ARQ, encoding="utf-8").read()

old = "                resultado = remover_shapes_impossiveis(resultado)"
new = ("                resultado = remover_shapes_impossiveis(resultado)\n"
       "                resultado = filtrar_pestana_dupla(resultado)")

if "filtrar_pestana_dupla(resultado)" in src:
    print("Filtro ja estava ligado.")
elif old not in src:
    print("ERRO: ponto de insercao nao encontrado.")
else:
    open(ARQ, "w", encoding="utf-8").write(src.replace(old, new, 1))
    print("Filtro global ligado no fluxo principal.")
