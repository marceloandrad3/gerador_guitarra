#!/usr/bin/env python3
"""Auditoria GLOBAL de dedilhacao.

Criterios objetivos (nao dependem de fonte externa):
  A) ordem invertida  - dedo maior numa casa MENOR que dedo menor
                        (ex: dedo 3 na casa 4 e dedo 1 na casa 7)
  B) dedo repetido    - mesmo dedo em casas DIFERENTES (impossivel)
  C) dedo ausente     - casa pisada sem dedo atribuido (dedo 0)
  D) salto de dedo    - usa dedo 4 sem usar o 3, ou 3 sem o 2
  E) span de dedos    - dedos 1 e 4 a mais de 4 trastes de distancia
"""
import json
import urllib.request
import urllib.parse
from collections import defaultdict

NOTAS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
TIPOS = ["", "m", "7", "m7", "7M", "m7M", "6", "m6", "9", "add9",
         "sus2", "sus4", "dim", "dim7", "aug"]


def analisar(diagrama, dedos):
    casas = []
    for v in diagrama:
        s = str(v).upper()
        casas.append(None if s in ("X", "-1") else int(s))
    dedos = list(dedos or [])
    problemas = []

    # mapa dedo -> casas em que aparece
    por_dedo = defaultdict(set)
    for c, d in zip(casas, dedos):
        if c is None or c == 0:
            continue
        if not d or d == 0:
            problemas.append(("C", f"casa {c} sem dedo"))
        else:
            por_dedo[d].add(c)

    for d, cs in por_dedo.items():
        if len(cs) > 1:
            problemas.append(("B", f"dedo {d} em casas {sorted(cs)}"))

    # ordem: dedo menor deve estar em casa <= dedo maior
    itens = [(d, min(cs)) for d, cs in por_dedo.items()]
    for d1, c1 in itens:
        for d2, c2 in itens:
            if d1 < d2 and c1 > c2:
                problemas.append(("A", f"dedo {d1} casa {c1} > dedo {d2} casa {c2}"))

    usados = set(por_dedo)
    for d in (3, 4):
        if d in usados and (d - 1) not in usados:
            problemas.append(("D", f"usa dedo {d} sem dedo {d-1}"))

    if por_dedo:
        todas = [c for cs in por_dedo.values() for c in cs]
        if max(todas) - min(todas) > 4:
            problemas.append(("E", f"span de dedos {max(todas)-min(todas)}"))

    return problemas


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
            p = analisar(x["diagrama"], x.get("dedos"))
            if p:
                achados.append((a, i, ",".join(x["diagrama"]),
                                x.get("dedos"), p))

print(f"Diagramas analisados: {tot}")
print(f"Com problema de dedilhacao: {len(achados)}")
print()
cont = defaultdict(int)
for a, i, s, ded, ps in achados:
    for cod, _ in ps:
        cont[cod] += 1
print("Por criterio:", dict(sorted(cont.items())))
print()
for a, i, s, ded, ps in achados[:40]:
    print(f"  {a:9s} Shape {i}  {s:22s} dedos={ded}")
    for cod, msg in ps:
        print(f"             [{cod}] {msg}")
if len(achados) > 40:
    print(f"  ... e mais {len(achados)-40}")
