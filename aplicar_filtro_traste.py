#!/usr/bin/env python3
"""Filtro GLOBAL de traste: nenhum diagrama com traste >= 12 e' exibido.

Criterio do usuario (musico): a partir da casa 12 o corpo do instrumento
bloqueia o acesso da mao. Vale para shape gerado internamente (CAGED) ou
vindo de fonte externa - o filtro roda na saida, nao na ingestao."""
import shutil

ARQ = "servidor.py"
shutil.copy(ARQ, ARQ + ".bak_filtro_traste")
src = open(ARQ, encoding="utf-8").read()

BLOCO = '''def _traste_alto(diagrama, limite=12):
    """True se algum traste pisado for >= limite (default 12)."""
    for v in (diagrama or []):
        s = str(v).upper()
        if s in ("X", "-1", "0"):
            continue
        try:
            if int(s) >= limite:
                return True
        except ValueError:
            continue
    return False


def filtrar_traste_alto(resultado):
    """Filtro GLOBAL: remove diagramas com traste >= 12."""
    diagramas = resultado.get("diagramas", [])
    antes = len(diagramas)
    resultado["diagramas"] = [
        d for d in diagramas if not _traste_alto(d.get("diagrama"))]
    removidos = antes - len(resultado["diagramas"])
    if removidos:
        resultado["total_diagramas"] = len(resultado["diagramas"])
        resultado["shapes_impossiveis_ocultos"] = (
            resultado.get("shapes_impossiveis_ocultos", 0) + removidos)
    return resultado


'''

MARCA = "def gerar_relatorio_impossiveis():"
if "_traste_alto" in src:
    print("Funcao ja existia.")
elif MARCA not in src:
    print("ERRO: ponto de insercao nao encontrado.")
else:
    src = src.replace(MARCA, BLOCO + MARCA, 1)
    print("Funcao inserida.")

old = "                resultado = filtrar_pestana_dupla(resultado)"
new = ("                resultado = filtrar_pestana_dupla(resultado)\n"
       "                resultado = filtrar_traste_alto(resultado)")
if "filtrar_traste_alto(resultado)" in src:
    print("Filtro ja estava ligado.")
elif old not in src:
    print("ERRO: nao achei a chamada de filtrar_pestana_dupla.")
else:
    src = src.replace(old, new, 1)
    print("Filtro ligado no fluxo.")

open(ARQ, "w", encoding="utf-8").write(src)
