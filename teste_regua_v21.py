"""Regressao: a regua v2.1 (so avalia HARMONIA) deve concordar com o
lado harmonico de cada shape gravado nas 3 tabelas. Rodar apos QUALQUER
alteracao em regua_v21.py. Saida != 0 = regua quebrada."""
import sqlite3, sys, hashlib
from regua_v21 import avaliar, REGRA, DB

con = sqlite3.connect(DB)

# Aprovados e em-auditoria: harmonia SEMPRE aprovada (passaram no criterio
# harmonia_completa). A regua deve dar 'valido' ou 'valido_raro'.
casos_harmonia_ok = []
for acorde, shape, span, tmax, nf in con.execute(
        "SELECT acorde, shape, span, traste_max, n_fontes_confiaveis "
        "FROM SHAPES_APROVADOS WHERE regra_versao=?", (REGRA,)):
    casos_harmonia_ok.append((acorde, shape, span, tmax, nf))
for acorde, shape, span, tmax, nf in con.execute(
        "SELECT acorde, shape, span, traste_max, n_fontes_confiaveis "
        "FROM SHAPES_EM_AUDITORIA WHERE regra_versao=?", (REGRA,)):
    casos_harmonia_ok.append((acorde, shape, span, tmax, nf))

# Reprovados por HARMONIA (nao ergonomia): a regua tem que reproduzir o
# veredito exato. Ergonomia (traste_alto/double_barre) fica de fora - a
# regua nao julga isso, so a harmonia, entao nao ha o que comparar ali.
casos_harmonia_reprovada = con.execute(
    "SELECT DISTINCT acorde, shape, veredito_original, span, traste_max "
    "FROM SHAPES_REPROVADOS WHERE regra_versao=? "
    "AND codigo_regra_reprovacao NOT IN ('traste_alto','double_barre')",
    (REGRA,)).fetchall()

esperado = con.execute(
    "SELECT sha256, linhas_identicas FROM REGUAS WHERE regra_versao=?", (REGRA,)).fetchone()
con.close()

falhas = []
total = 0

for a, s, sp, tm, nf in casos_harmonia_ok:
    total += 1
    fontes_ext = 0 if nf == 0 else None
    ver, _, _, span_calc, tmax_calc = avaliar(a, s, fontes_ext)
    if not ver.startswith("valido") or span_calc != sp or tmax_calc != tm:
        falhas.append((a, s, "valido(_raro)", ver, sp, span_calc, tm, tmax_calc))

for a, s, v_esperado, sp, tm in casos_harmonia_reprovada:
    total += 1
    ver, _, _, span_calc, tmax_calc = avaliar(a, s)
    if ver != v_esperado or span_calc != sp or tmax_calc != tm:
        falhas.append((a, s, v_esperado, ver, sp, span_calc, tm, tmax_calc))

sha = hashlib.sha256(open("regua_v21.py","rb").read()).hexdigest()
print(f"linhas: {total}  falhas: {len(falhas)}")
print(f"sha256 atual:    {sha[:16]}")
print(f"sha256 registrado: {esperado[0][:16]}  {'(inalterado)' if sha==esperado[0] else '(ALTERADO - reprovar registro)'}")
for f in falhas[:10]: print("  FALHA:", f)
sys.exit(1 if falhas else 0)
