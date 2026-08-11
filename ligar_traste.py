#!/usr/bin/env python3
import shutil
ARQ = "servidor.py"
shutil.copy(ARQ, ARQ + ".bak_ligar_traste")
src = open(ARQ, encoding="utf-8").read()

old = "                resultado = filtrar_pestana_dupla(resultado)"
new = ("                resultado = filtrar_pestana_dupla(resultado)\n"
       "                resultado = filtrar_traste_alto(resultado)")

if new in src:
    print("Ja estava ligado de verdade.")
elif old not in src:
    print("ERRO: chamada de filtrar_pestana_dupla nao encontrada.")
else:
    open(ARQ, "w", encoding="utf-8").write(src.replace(old, new, 1))
    print("Filtro de traste ligado no fluxo.")
