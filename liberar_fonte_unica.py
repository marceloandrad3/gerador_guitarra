#!/usr/bin/env python3
"""Move de SHAPES_EM_AUDITORIA para SHAPES_APROVADOS os shapes que
atingiram 2+ fontes confiaveis. O registro em auditoria e' removido;
o shape passa a existir SOMENTE em SHAPES_APROVADOS, com rastreabilidade
completa (regras atendidas, veredito original, data) E com o diagrama
pronto (dedos, pestana, dificuldade) - a tabela e' fonte unica para o
cifras-facil, que so le, nunca calcula.

NAO mexe em SHAPES_REPROVADOS - traste_alto e double_barre continuam
validos e nao sao afetados por numero de fontes.
"""
import sqlite3
from datetime import datetime
from dedicacao import calcular_dedos_e_pestana
from dificuldade import avaliar_dificuldade
from gerador_web_dinamico import parse_acorde, parsear_inversao

DATA = datetime.now().isoformat(timespec="seconds")
con = sqlite3.connect("auditoria.db")
cur = con.cursor()

candidatos = cur.execute(
    "SELECT acorde, shape, regra_versao, span, traste_max "
    "FROM SHAPES_EM_AUDITORIA").fetchall()

liberados, mantidos = [], 0
for acorde, shape, regra_versao, span, tmax in candidatos:
    n = cur.execute(
        "SELECT COUNT(DISTINCT fonte_id) FROM CONFIRMACOES "
        "WHERE acorde=? AND shape=? AND confiavel=1", (acorde, shape)).fetchone()[0]
    if n >= 2:
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
            "INSERT OR IGNORE INTO SHAPES_APROVADOS "
            "(acorde, shape, regra_versao, span, traste_max, n_fontes_confiaveis, "
            "regras_validacao_atendidas, veredito_original, data, dedos, "
            "pestana_casa, pestana_corda_min, pestana_corda_max, "
            "dificuldade_score, dificuldade_nivel, dificuldade_rotulo) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (acorde, shape, regra_versao, span, tmax, n,
             "harmonia_completa,min_2_fontes_confiaveis", "valido", DATA,
             dedos_str, p_casa, p_min, p_max,
             dif["score"], dif["nivel"], dif["rotulo"]))
        cur.execute(
            "DELETE FROM SHAPES_EM_AUDITORIA WHERE acorde=? AND shape=? "
            "AND regra_versao=?", (acorde, shape, regra_versao))
        liberados.append((acorde, shape, n))
    else:
        mantidos += 1

con.commit()

print(f"Analisados: {len(candidatos)}")
print(f"Liberados (agora tem 2+ fontes, movidos para SHAPES_APROVADOS): {len(liberados)}")
print(f"Mantidos em SHAPES_EM_AUDITORIA (ainda <2 fontes): {mantidos}")
print()
for a, s, n in liberados:
    print(f"  {a:10s} {s:22s} fontes={n}")

con.close()
