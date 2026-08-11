#!/usr/bin/env python3
import shutil
ARQ = "dificuldade.py"
shutil.copy(ARQ, ARQ + ".bak_ligar_override")
linhas = open(ARQ, encoding="utf-8").read().split("\n")

alvo = '    return {"score": score, "nivel": nivel, "rotulo": rotulo,'
idx = [i for i, l in enumerate(linhas) if l == alvo]
if not idx:
    print("ERRO: return final nao encontrado.")
elif any("if _padrao_dois_blocos(" in l for l in linhas):
    print("Override ja presente de verdade.")
else:
    i = idx[-1]
    linhas[i:i] = [
        "    if _padrao_dois_blocos(diagrama, dedos, pestana):",
        '        nivel, rotulo = 5, "Muito Dificil"',
        "",
    ]
    open(ARQ, "w", encoding="utf-8").write("\n".join(linhas))
    print("Override inserido.")

print("--- verificacao ---")
for n, l in enumerate(open(ARQ, encoding="utf-8").read().split("\n"), 1):
    if "_padrao_dois_blocos" in l:
        print(f"  linha {n}: {l.strip()}")
