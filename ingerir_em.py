#!/usr/bin/env python3
import sqlite3
from collections import Counter
from datetime import datetime
from dedicacao import calcular_dedos_e_pestana

DATA = datetime.now().isoformat(timespec="seconds")

SHAPES = [
    "0,2,2,0,0,0",
    "0,2,2,0,0,3",
    "12,14,14,12,12,12",
    "X,X,2,4,5,3",
    "12,14,14,12,12,15",
    "12,10,9,9,12,X",
    "X,7,9,9,8,7",
    "12,10,9,12,X,X",
]

def parse(s):
    return [None if p.strip().upper() == "X" else int(p.strip())
            for p in s.split(",")]

def traste_max(s):
    v = [x for x in parse(s) if x is not None and x > 0]
    return max(v) if v else 0

def pestana_dupla(s):
    dedos, _ = calcular_dedos_e_pestana(parse(s))
    c = Counter(d for d in dedos if d and d > 0)
    return len([d for d, n in c.items() if n >= 2]) >= 2

conn = sqlite3.connect("auditoria.db")
cur = conn.cursor()
cur.execute("SELECT id FROM FONTES WHERE nome='queroaprenderagora'")
fonte_id = cur.fetchone()[0]

ins = 0
rej = []
for s in SHAPES:
    if traste_max(s) > 12:
        rej.append((s, "traste acima de 12")); continue
    if pestana_dupla(s):
        rej.append((s, "pestana dupla")); continue
    cur.execute("SELECT COUNT(*) FROM CONFIRMACOES "
                "WHERE acorde='Em' AND shape=? AND fonte_id=?", (s, fonte_id))
    if cur.fetchone()[0]:
        continue
    cur.execute("INSERT INTO CONFIRMACOES (acorde, shape, fonte_id, data, confiavel) "
                "VALUES ('Em', ?, ?, ?, 1)", (s, fonte_id, DATA))
    ins += 1
conn.commit()

print(f"Inseridos: {ins}   Rejeitados: {len(rej)}")
for s, m in rej:
    print(f"   {s:22s} -> {m}")

print("--- Em: shapes com 2+ fontes ---")
for s, n in cur.execute(
        "SELECT shape, COUNT(DISTINCT fonte_id) FROM CONFIRMACOES "
        "WHERE acorde='Em' AND confiavel=1 GROUP BY shape "
        "HAVING COUNT(DISTINCT fonte_id)>=2"):
    print(f"   {s:22s} fontes={n}")
conn.close()
