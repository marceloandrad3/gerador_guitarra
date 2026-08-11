#!/usr/bin/env python3
"""Ingere guitar-chord.org (fonte_id=5).

Regua v2.1 decide harmonia; ergonomia (traste_alto/double_barre) tambem
reprova. Shape harmonicamente ok e sem bloqueio ergonomico vai para
SHAPES_APROVADOS (2+ fontes) ou SHAPES_EM_AUDITORIA (<2 fontes).
Grava DIRETO nas 3 tabelas - nunca em VEREDITOS/PROBLEMAS_ERGONOMIA.
"""
import sqlite3
from collections import Counter
from datetime import datetime
from regua_v21 import avaliar, REGRA
from dedicacao import calcular_dedos_e_pestana
from dificuldade import avaliar_dificuldade
from gerador_web_dinamico import parse_acorde, parsear_inversao

DATA = datetime.now().isoformat(timespec="seconds")
FONTE = 5
FONTE_NOME = "guitar_chord_org"

# origem: 'publicado' = frets literais na pagina
#         'derivado'  = frets deduzidos das notas-por-corda publicadas
CANDIDATOS = [
    ("Caug","X,3,2,1,1,X","publicado"),      ("C#aug","X,4,3,2,2,X","publicado"),
    ("Daug","X,5,4,3,3,X","publicado"),      ("D#aug","X,6,5,4,4,X","publicado"),
    ("Eaug","X,7,6,5,5,X","publicado"),      ("Faug","X,8,7,6,6,X","publicado"),
    ("F#aug","X,9,8,7,7,X","publicado"),     ("Gaug","X,10,9,8,8,X","publicado"),
    ("G#aug","X,11,10,9,9,X","publicado"),   ("Aaug","X,12,11,10,10,X","publicado"),
    ("A#aug","X,13,12,11,11,X","publicado"), ("Baug","X,2,1,0,0,X","publicado"),
    ("Aaug","X,X,X,2,2,1","publicado"),      ("Baug","X,X,X,4,4,3","publicado"),
    ("Caug","X,X,X,5,5,4","publicado"),      ("Daug","X,X,X,7,7,6","publicado"),
    ("Eaug","X,X,X,9,9,8","publicado"),      ("Faug","X,X,X,10,10,9","publicado"),
    ("Gaug","X,X,X,12,12,11","publicado"),
    ("Caug","X,3,2,1,1,0","publicado"),      ("Daug","X,X,0,3,3,2","publicado"),
    ("Eaug","X,X,2,1,1,0","publicado"),      ("Faug","X,X,3,2,2,1","publicado"),
    ("Gaug","3,2,1,0,0,3","publicado"),      ("Aaug","X,0,3,2,2,1","publicado"),
    ("Baug","X,2,1,0,0,3","publicado"),
]

DET_TRASTE = ("Traste {t} >= 12. Verificado pelo usuario (musico) em violao e "
              "guitarra padrao: a partir da casa 12 o corpo do instrumento bloqueia "
              "o acesso da mao, tornando a digitacao inviavel (sem pestana). Existem "
              "voicings equivalentes em posicoes mais baixas do braco. Pode ser viavel "
              "em instrumentos com cutaway profundo.")
DET_BARRE = ("Duas pestanas simultaneas detectadas por calcular_dedos_e_pestana() - "
             "fisicamente impossivel de executar. Origem: {f}.")


def parse(s):
    return [None if p.strip().upper() == "X" else int(p.strip())
            for p in s.split(",")]


def pestana_dupla(s):
    dedos, _ = calcular_dedos_e_pestana(parse(s))
    c = Counter(d for d in dedos if d and d > 0)
    return len([d for d, n in c.items() if n >= 2]) >= 2


con = sqlite3.connect("auditoria.db")
cur = con.cursor()

cur.execute("SELECT nome FROM FONTES WHERE id=?", (FONTE,))
assert cur.fetchone()[0] == FONTE_NOME, "fonte_id 5 nao e' guitar_chord_org"

conf_novas = aprov_novos = audit_novos = rep_novos = 0
linhas = []

for acorde, shape, origem in CANDIDATOS:
    ver, falhos, notas, span, tmax = avaliar(acorde, shape)

    # 1. confirmacao da fonte (sempre grava, independente do veredito)
    cur.execute("SELECT COUNT(*) FROM CONFIRMACOES WHERE acorde=? AND shape=? "
                "AND fonte_id=?", (acorde, shape, FONTE))
    if not cur.fetchone()[0]:
        cur.execute("INSERT INTO CONFIRMACOES (acorde, shape, fonte_id, data, confiavel) "
                    "VALUES (?,?,?,?,1)", (acorde, shape, FONTE, DATA))
        conf_novas += 1

    # ja classificado antes (em qualquer das 3 tabelas)? nao reclassifica.
    cur.execute("SELECT 1 FROM SHAPES_APROVADOS WHERE acorde=? AND shape=? AND regra_versao=?",
                (acorde, shape, REGRA))
    ja_aprov = cur.fetchone()
    cur.execute("SELECT 1 FROM SHAPES_EM_AUDITORIA WHERE acorde=? AND shape=? AND regra_versao=?",
                (acorde, shape, REGRA))
    ja_audit = cur.fetchone()
    cur.execute("SELECT 1 FROM SHAPES_REPROVADOS WHERE acorde=? AND shape=? AND regra_versao=?",
                (acorde, shape, REGRA))
    ja_rep = cur.fetchone()

    if ja_aprov or ja_audit or ja_rep:
        estado = "ja classificado"
        linhas.append(f"  {acorde:8s} {shape:18s} {origem:10s} {ver:12s} {estado}")
        continue

    reprovacoes = []
    if not ver.startswith("valido"):
        for cod in (falhos or "indeterminado").split(","):
            if cod:
                reprovacoes.append((cod, f"Reprovado pela regua: {cod}"))
    if tmax and tmax >= 12:
        reprovacoes.append(("traste_alto", DET_TRASTE.format(t=tmax)))
    if pestana_dupla(shape):
        reprovacoes.append(("double_barre", DET_BARRE.format(f=FONTE_NOME)))

    if reprovacoes:
        for cod, det in reprovacoes:
            cur.execute(
                "INSERT OR IGNORE INTO SHAPES_REPROVADOS "
                "(acorde, shape, regra_versao, codigo_regra_reprovacao, detalhe, "
                "veredito_original, span, traste_max, data) VALUES (?,?,?,?,?,?,?,?,?)",
                (acorde, shape, REGRA, cod, det, ver, span, tmax, DATA))
            rep_novos += 1
        estado = "GRAVADO REPROVADO: " + ",".join(c for c, _ in reprovacoes)
    else:
        n_f = cur.execute(
            "SELECT COUNT(DISTINCT fonte_id) FROM CONFIRMACOES "
            "WHERE acorde=? AND shape=? AND confiavel=1", (acorde, shape)).fetchone()[0]
        if n_f >= 2:
            acorde_base, _baixo = parsear_inversao(acorde)
            tonica, tipo_p = parse_acorde(acorde_base)
            conv = [None if p.strip().upper() == "X" else int(p.strip())
                    for p in shape.split(",")]
            dedos, pestana = calcular_dedos_e_pestana(conv)
            partes = [p.strip().upper() for p in shape.split(",")]
            dif = avaliar_dificuldade(partes, dedos, pestana, tonica, tipo_p)
            dedos_str = ",".join(str(d) for d in dedos)
            p_casa = pestana["casa"] if pestana else None
            p_min = min(pestana["cordas"]) if pestana else None
            p_max = max(pestana["cordas"]) if pestana else None

            cur.execute(
                "INSERT INTO SHAPES_APROVADOS (acorde, shape, regra_versao, span, "
                "traste_max, n_fontes_confiaveis, regras_validacao_atendidas, "
                "veredito_original, data, dedos, pestana_casa, pestana_corda_min, "
                "pestana_corda_max, dificuldade_score, dificuldade_nivel, "
                "dificuldade_rotulo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (acorde, shape, REGRA, span, tmax, n_f,
                 "harmonia_completa,min_2_fontes_confiaveis", ver, DATA,
                 dedos_str, p_casa, p_min, p_max,
                 dif["score"], dif["nivel"], dif["rotulo"]))
            aprov_novos += 1
            estado = f"GRAVADO APROVADO ({n_f} fontes)"
        else:
            cur.execute(
                "INSERT INTO SHAPES_EM_AUDITORIA (acorde, shape, regra_versao, span, "
                "traste_max, n_fontes_confiaveis, motivo, data) VALUES (?,?,?,?,?,?,?,?)",
                (acorde, shape, REGRA, span, tmax, n_f,
                 "aguardando_2a_fonte_confiavel", DATA))
            audit_novos += 1
            estado = f"GRAVADO AUDITORIA ({n_f} fonte)"

    linhas.append(f"  {acorde:8s} {shape:18s} {origem:10s} {ver:12s} {estado}")

con.commit()

print(f"Confirmacoes novas (fonte {FONTE}): {conf_novas}")
print(f"Aprovados novos:  {aprov_novos}")
print(f"Auditoria novos:  {audit_novos}")
print(f"Reprovados novos: {rep_novos}")
print()
for l in linhas:
    print(l)
con.close()
