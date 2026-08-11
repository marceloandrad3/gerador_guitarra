#!/usr/bin/env python3
import json, urllib.request, urllib.parse
NOTAS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
TIPOS = ["", "m", "7", "m7", "7M", "m7M", "6", "m6", "9", "add9",
         "sus2", "sus4", "dim", "dim7", "aug"]
def alto(d):
    for v in d:
        s = str(v).upper()
        if s in ("X","-1","0"): continue
        try:
            if int(s) >= 12: return True
        except ValueError: pass
    return False
tot = 0; ach = []
for t in NOTAS:
    for tp in TIPOS:
        a = t + tp
        try:
            d = json.load(urllib.request.urlopen(
                "http://localhost:8000/gerar?acorde=" + urllib.parse.quote(a), timeout=10))
        except Exception: continue
        for i, x in enumerate(d.get("diagramas", []), 1):
            tot += 1
            if alto(x["diagrama"]):
                ach.append((a, i, ",".join(x["diagrama"])))
print(f"Analisados: {tot}   Com traste >=12: {len(ach)}")
for a,i,s in ach: print(f"   {a:9s} Shape {i}  {s}")
