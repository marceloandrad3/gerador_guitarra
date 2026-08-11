#!/usr/bin/env python3
"""Detecta o padrao: 2+ dedos numa casa, casa(s) vazia(s) no meio,
2+ dedos em outra casa. Ergonomicamente muito complexo (criterio do
usuario, musico, 2026-08-08). Nao grava nada - so relatorio."""
import json
import urllib.request
import urllib.parse
from collections import Counter

NOTAS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
TIPOS = ["", "m", "7", "m7", "7M", "m7M", "6", "m6", "9", "add9",
         "sus2", "sus4", "dim", "dim7", "aug"]


def padrao_gap(diagrama):
    """True se houver >=2 notas numa casa, gap, >=2 notas noutra casa."""
    casas = []
    for v in diagrama:
        s = str(v).upper()
        if s in ("X", "-1", "0"):
            continue
        casas.append(int(s))
    if not casas:
        return None
    cont = Counter(casas)
    blocos = sorted(c for c, n in cont.items() if n >= 2)
    if len(blocos) < 2:
        return None
    for i in range(len(blocos) - 1):
        a, b = blocos[i], blocos[i + 1]
        gap = b - a - 1
        if gap >= 1:
            # ha casa(s) vazia(s) entre os dois blocos?
            vazias = [c for c in range(a + 1, b) if cont.get(c, 0) == 0]
            if vazias:
                return f"blocos casa {a} e {b}, {len(vazias)} casa(s) vazia(s)"
    return None


tot = 0
achados = []
for t in NOTAS:
    for tp in TIPOS:
        a = t + tp
        try:
            d = json.load(urllib.request.urlopen(
                "http://localhost:8000/gerar?acorde=" + urllib.parse.quote(a),
                timeout=10))
        except Exception:
            continue
        for i, x in enumerate(d.get("diagramas", []), 1):
            tot += 1
            m = padrao_gap(x["diagrama"])
            if m:
                dif = x.get("dificuldade") or {}
                achados.append((a, i, ",".join(x["diagrama"]),
                                dif.get("nivel"), dif.get("rotulo"), m))

print(f"Diagramas analisados: {tot}")
print(f"Com padrao bloco-gap-bloco: {len(achados)}")
print()
por_nivel = Counter(x[3] for x in achados)
print("Dificuldade atribuida hoje:", dict(sorted(
    (k, v) for k, v in por_nivel.items() if k)))
print()
for a, i, s, n, rot, m in achados:
    print(f"  {a:9s} Shape {i}  {s:22s} Dif {n}/5 {rot or '':13s} | {m}")
