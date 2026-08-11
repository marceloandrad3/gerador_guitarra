#!/usr/bin/env python3
"""Padrao ergonomico dificil (criterio do usuario, musico, 2026-08-08):
dois PARES de dedos distintos, em casas separadas por gap, SEM pestana
ancorando. Pestana e' dificuldade normal e nao entra aqui.

Conta DEDOS, nao casas: uma casa com 3 notas do mesmo dedo 1 e' pestana,
nao bloco."""
import json
import urllib.request
import urllib.parse
from collections import Counter, defaultdict

NOTAS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
TIPOS = ["", "m", "7", "m7", "7M", "m7M", "6", "m6", "9", "add9",
         "sus2", "sus4", "dim", "dim7", "aug"]


def padrao(diagrama, dedos, pestana):
    if pestana:
        return None                      # pestana ancora a mao
    casa_por_dedo = {}
    for v, d in zip(diagrama, dedos or []):
        s = str(v).upper()
        if s in ("X", "-1", "0") or not d or d == 0:
            continue
        casa_por_dedo[d] = int(s)
    if len(casa_por_dedo) < 4:
        return None                      # precisa dos 4 dedos ocupados
    por_casa = defaultdict(list)
    for d, c in casa_por_dedo.items():
        por_casa[c].append(d)
    pares = sorted(c for c, ds in por_casa.items() if len(ds) >= 2)
    if len(pares) < 2:
        return None
    for i in range(len(pares) - 1):
        a, b = pares[i], pares[i + 1]
        if b - a - 1 >= 1:
            return (f"dedos {sorted(por_casa[a])} na casa {a} e "
                    f"{sorted(por_casa[b])} na casa {b}, gap de {b-a-1}")
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
            m = padrao(x["diagrama"], x.get("dedos"), x.get("pestana"))
            if m:
                dif = x.get("dificuldade") or {}
                achados.append((a, i, ",".join(x["diagrama"]),
                                x.get("dedos"), dif.get("nivel"),
                                dif.get("rotulo"), m))

print(f"Diagramas analisados: {tot}")
print(f"Com padrao dificil (2 pares + gap, sem pestana): {len(achados)}")
print()
print("Dificuldade atribuida hoje:",
      dict(sorted(Counter(x[4] for x in achados).items(), key=lambda z: z[0] or 0)))
print()
for a, i, s, ded, n, rot, m in achados:
    print(f"  {a:9s} Shape {i}  {s:22s} dedos={ded} Dif {n}/5 {rot or ''}")
    print(f"             {m}")
