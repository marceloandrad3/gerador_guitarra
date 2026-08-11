#!/usr/bin/env python3
"""Relatorio: quais shapes a regra de pestana dupla barraria, em TODOS
os acordes. NAO grava nada - so lista, para conferencia do musico."""
import json
import urllib.request
import urllib.parse
from collections import Counter

NOTAS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
TIPOS = ["", "m", "7", "m7", "7M", "m7M", "6", "m6", "9", "add9",
         "sus2", "sus4", "dim", "dim7", "aug"]

def dupla(dedos):
    c = Counter(d for d in dedos if d and d > 0)
    return len([d for d, n in c.items() if n >= 2]) >= 2

total = 0
achados = []
for t in NOTAS:
    for tp in TIPOS:
        acorde = t + tp
        url = "http://localhost:8000/gerar?acorde=" + urllib.parse.quote(acorde)
        try:
            d = json.load(urllib.request.urlopen(url, timeout=10))
        except Exception:
            continue
        for i, x in enumerate(d.get("diagramas", []), 1):
            total += 1
            if dupla(x.get("dedos") or []):
                achados.append((acorde, i, ",".join(x["diagrama"]),
                                x.get("dedos")))

print(f"Diagramas analisados: {total}")
print(f"Com pestana dupla: {len(achados)}")
print()
for a, i, s, ded in achados:
    print(f"  {a:9s} Shape {i}  {s:22s} dedos={ded}")
