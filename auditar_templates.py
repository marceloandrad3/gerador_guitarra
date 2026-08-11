#!/usr/bin/env python3
"""Testa TODOS os templates CAGED em TODAS as 12 tonicas e reporta
quais geram shapes com pestana dupla. Nao grava nada."""
from collections import Counter
import gerador_web_dinamico as G
from dedicacao import calcular_dedos_e_pestana

NOTAS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
TIPOS = ["", "m", "7", "m7", "7M", "m7M", "6", "m6", "9", "add9",
         "sus2", "sus4", "dim", "dim7", "aug"]

def dupla(dedos):
    c = Counter(d for d in dedos if d and d > 0)
    return len([d for d, n in c.items() if n >= 2]) >= 2

ruins = {}
for tp in TIPOS:
    for t in NOTAS:
        try:
            res = G.gerar_dinamico(t + tp)
        except Exception:
            continue
        for d in res.get("diagramas", []):
            casas = [None if str(v).upper() in ("X","-1") else int(v)
                     for v in d["diagrama"]]
            dedos, _ = calcular_dedos_e_pestana(casas)
            if dupla(dedos):
                nome = d.get("nome", "?")
                ruins.setdefault(nome, []).append(
                    (t + tp, ",".join(str(v) for v in d["diagrama"])))

print(f"Templates que geram pestana dupla: {len(ruins)}\n")
for nome in sorted(ruins):
    ocorr = ruins[nome]
    print(f"  {nome}  -> {len(ocorr)} ocorrencias")
    for a, s in ocorr[:3]:
        print(f"       {a:8s} {s}")
    if len(ocorr) > 3:
        print(f"       ... +{len(ocorr)-3}")
