#!/usr/bin/env python3
"""Adiciona regra ergonomica: dois PARES de dedos distintos em casas
separadas por gap, SEM pestana ancorando -> nivel 5/5.

Criterio do usuario (musico, 2026-08-08): esse padrao trava a mao em
dois blocos sem ancora, sendo complexo mesmo para violonistas
experientes. Pestana NAO entra: e' dificuldade normal, ja coberta pela
rubrica ISMIR."""
import shutil

ARQ = "dificuldade.py"
shutil.copy(ARQ, ARQ + ".bak_regra_gap")
src = open(ARQ, encoding="utf-8").read()

FUNC = '''

def _padrao_dois_blocos(diagrama, dedos, pestana):
    """Dois pares de dedos distintos, casas separadas por gap, sem pestana.

    Criterio do usuario (musico, 2026-08-08). Conta DEDOS, nao casas:
    varias notas do mesmo dedo sao pestana, nao bloco."""
    from collections import defaultdict
    if pestana:
        return False
    casa_por_dedo = {}
    for v, d in zip(diagrama or [], dedos or []):
        s = str(v).upper()
        if s in ("X", "-1", "0") or not d or d == 0:
            continue
        try:
            casa_por_dedo[d] = int(s)
        except ValueError:
            continue
    if len(casa_por_dedo) < 4:
        return False
    por_casa = defaultdict(list)
    for d, c in casa_por_dedo.items():
        por_casa[c].append(d)
    pares = sorted(c for c, ds in por_casa.items() if len(ds) >= 2)
    if len(pares) < 2:
        return False
    for i in range(len(pares) - 1):
        if pares[i + 1] - pares[i] - 1 >= 1:
            return True
    return False

'''

MARCA = "def avaliar_dificuldade("
if "_padrao_dois_blocos" in src:
    print("Funcao ja existia.")
elif MARCA not in src:
    print("ERRO: nao achei avaliar_dificuldade.")
else:
    src = src.replace(MARCA, FUNC.lstrip("\n") + "\n" + MARCA, 1)
    print("Funcao inserida.")

OLD_RET = ('    return {"score": score, "nivel": nivel, "rotulo": rotulo,\n'
           '            "detalhes": {"UC": uc, "CFP": cfp, "CFD": cfd, "RHC": rhc}}')
NEW_RET = ('    if _padrao_dois_blocos(diagrama, dedos, pestana):\n'
           '        nivel, rotulo = 5, "Muito Dificil"\n'
           '\n' + OLD_RET)

if "_padrao_dois_blocos(diagrama, dedos, pestana):" in src:
    print("Override ja aplicado.")
elif OLD_RET not in src:
    print("ERRO: return final nao encontrado - verifique manualmente.")
else:
    src = src.replace(OLD_RET, NEW_RET, 1)
    print("Override de nivel aplicado.")

open(ARQ, "w", encoding="utf-8").write(src)
