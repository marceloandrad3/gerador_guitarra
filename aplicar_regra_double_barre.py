#!/usr/bin/env python3
"""Varre o /gerar de todos os tipos/tonicas conhecidos e registra em
SHAPES_REPROVADOS os shapes com pestana dupla (2+ dedos diferentes
cobrindo 2+ cordas cada - fisicamente impossivel).

Reexecutavel: util quando novos tipos de acorde forem adicionados no
futuro. O bloqueio em si (filtrar_pestana_dupla) ja e' permanente em
servidor.py - nao depende mais deste script para funcionar; ele so
serve para AUDITAR e registrar novos casos na tabela.
"""
import json
import sqlite3
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from regua_v21 import REGRA

NOTAS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
TIPOS = ["", "m", "7", "m7", "7M", "m7M", "6", "m6", "9", "add9",
         "sus2", "sus4", "dim", "dim7", "aug"]
DATA = datetime.now().isoformat(timespec="seconds")


def dupla(dedos):
    c = Counter(d for d in dedos if d and d > 0)
    return len([d for d, n in c.items() if n >= 2]) >= 2


conn = sqlite3.connect("auditoria.db")
cur = conn.cursor()
novos = 0
for t in NOTAS:
    for tp in TIPOS:
        acorde = t + tp
        url = "http://localhost:8000/gerar?acorde=" + urllib.parse.quote(acorde)
        try:
            d = json.load(urllib.request.urlopen(url, timeout=10))
        except Exception:
            continue
        alvo = d.get("tonica", "") + d.get("tipo", "")
        for x in d.get("diagramas", []):
            if not dupla(x.get("dedos") or []):
                continue
            shape = ",".join(str(v).upper() for v in x["diagrama"])

            cur.execute(
                "SELECT 1 FROM SHAPES_REPROVADOS WHERE acorde=? AND shape=? "
                "AND codigo_regra_reprovacao='double_barre' AND regra_versao=?",
                (alvo, shape, REGRA))
            if cur.fetchone():
                continue

            detalhe = ("Pestana dupla: %s - dois dedos em barra ao mesmo tempo, "
                       "fisicamente impossivel." % str(x.get("dedos")))
            cur.execute(
                "INSERT INTO SHAPES_REPROVADOS (acorde, shape, regra_versao, "
                "codigo_regra_reprovacao, detalhe, veredito_original, data) "
                "VALUES (?,?,?,?,?,?,?)",
                (alvo, shape, REGRA, "double_barre", detalhe, "rejeitado_ergonomia", DATA))
            novos += 1
conn.commit()
conn.close()
print(f"Registrados como double_barre em SHAPES_REPROVADOS: {novos}")
