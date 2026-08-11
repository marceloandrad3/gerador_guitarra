#!/usr/bin/env python3
"""Popula dedos/pestana/dificuldade em TODAS as linhas de SHAPES_APROVADOS,
usando as MESMAS funcoes que servidor.py usa (dedicacao.py, dificuldade.py).
Objetivo: SHAPES_APROVADOS vira diagrama pronto - o cifras-facil le uma
linha e monta o acorde sem calcular nada.
"""
import sqlite3
from dedicacao import calcular_dedos_e_pestana
from dificuldade import avaliar_dificuldade
from gerador_web_dinamico import parse_acorde, parsear_inversao

con = sqlite3.connect("auditoria.db")
cur = con.cursor()

linhas = cur.execute(
    "SELECT id, acorde, shape FROM SHAPES_APROVADOS").fetchall()

atualizadas = erros = 0
falhas = []

for id_, acorde, shape in linhas:
    try:
        acorde_base, _baixo = parsear_inversao(acorde)
        tonica, tipo = parse_acorde(acorde_base)

        partes = [p.strip().upper() for p in shape.split(",")]
        conv = [None if p == "X" else int(p) for p in partes]

        dedos, pestana = calcular_dedos_e_pestana(conv)
        dif = avaliar_dificuldade(partes, dedos, pestana, tonica, tipo)

        dedos_str = ",".join(str(d) for d in dedos)
        p_casa = pestana["casa"] if pestana else None
        p_min = min(pestana["cordas"]) if pestana else None
        p_max = max(pestana["cordas"]) if pestana else None

        cur.execute(
            "UPDATE SHAPES_APROVADOS SET dedos=?, pestana_casa=?, "
            "pestana_corda_min=?, pestana_corda_max=?, dificuldade_score=?, "
            "dificuldade_nivel=?, dificuldade_rotulo=? WHERE id=?",
            (dedos_str, p_casa, p_min, p_max,
             dif["score"], dif["nivel"], dif["rotulo"], id_))
        atualizadas += 1
    except Exception as e:
        erros += 1
        falhas.append((acorde, shape, str(e)))

con.commit()

print(f"Linhas totais:   {len(linhas)}")
print(f"Atualizadas:     {atualizadas}")
print(f"Erros:           {erros}")
for a, s, e in falhas[:15]:
    print(f"  ERRO {a} {s}: {e}")

print()
print("=== conferencia: 0 linhas devem continuar com dedos NULL ===")
n_null = cur.execute("SELECT COUNT(*) FROM SHAPES_APROVADOS WHERE dedos IS NULL").fetchone()[0]
print(f"dedos NULL: {n_null}")

con.close()
