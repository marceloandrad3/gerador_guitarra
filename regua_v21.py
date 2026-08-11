"""Regua dedutiva v2.1 - reconstrucao a partir dos 7 criterios da tabela `criterios`.
Nao grava nada. Modo prova: reexecuta sobre os shapes ja gravados em `vereditos`
e compara veredito a veredito. So apos 1811/1811 essa regua pode ser usada
para estender a auditoria a slash chords.
"""
import sqlite3, os

DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(DIR, "auditoria.db")
NOTAS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
CORDAS_MIDI = [40,45,50,55,59,64]   # E A D G B E (grave->agudo)
REGRA = "v2.1-dedutiva"


def _carregar_tipos_e_limites():
    """Carrega definicao de tipos de acorde e limiares numericos do banco
    (tabelas TIPOS_DE_ACORDE e REGRAS_DE_VALIDACAO) em vez de hardcoded no
    codigo. Fonte unica de verdade: o banco. Roda uma vez, na importacao."""
    con = sqlite3.connect(DB)
    tipos, sem_terca, triade_ou_quinta_alt, extensao = {}, set(), set(), {}
    for cod, intervalos, s_terca, eh_tq, ext in con.execute(
            "SELECT codigo, intervalos, sem_terca, "
            "eh_triade_ou_quinta_alterada, extensao_intervalo FROM TIPOS_DE_ACORDE"):
        tipos[cod] = [int(x) for x in intervalos.split(",")]
        if s_terca:
            sem_terca.add(cod)
        if eh_tq:
            triade_ou_quinta_alt.add(cod)
        if ext is not None:
            extensao[cod] = ext

    limites = {cod: lim for cod, lim in con.execute(
        "SELECT codigo, limite_numerico FROM REGRAS_DE_VALIDACAO "
        "WHERE limite_numerico IS NOT NULL")}
    con.close()
    return tipos, sem_terca, triade_ou_quinta_alt, extensao, limites


TIPOS, SEM_TERCA, _TRIADE_OU_QUINTA_ALT, EXTENSAO, _LIMITES = _carregar_tipos_e_limites()
# TRIADES e QUINTA_ALTERADA eram dois sets separados no codigo antigo, mas a
# funcao avaliar() so os usa em OR (tipo in TRIADES or tipo in QUINTA_ALTERADA);
# a coluna eh_triade_ou_quinta_alterada ja representa exatamente essa uniao.
TRIADES = _TRIADE_OU_QUINTA_ALT
QUINTA_ALTERADA = set()
LIMITE_ABERTURA = _LIMITES.get('fisica.abertura', 4)
LIMITE_ALCANCE = _LIMITES.get('fisica.alcance', 15)

def idx(n): return NOTAS.index(n.upper())

def parse_acorde(a):
    import re
    m = re.match(r'^([A-G])(#|b)?(.*)$', a)
    if not m: return None, None
    t = m.group(1) + (m.group(2) or '')
    if 'b' in t:
        t = NOTAS[(idx(t[0]) - 1) % 12]
    return t, m.group(3)

def avaliar(acorde, shape_str, fontes_externas=None):
    """Retorna (veredito, criterios_falhos, notas, span, traste_max)."""
    tonica, tipo = parse_acorde(acorde)
    if tonica is None or tipo not in TIPOS:
        return "indeterminado", "", "", None, None

    ti = idx(tonica)
    permitidas = {(ti + i) % 12 for i in TIPOS[tipo]}
    pos = [p.strip().upper() for p in shape_str.split(',')]
    if len(pos) != 6:
        return "rejeitado", "shape.malformado", "", None, None

    notas, trastes = [], []
    for c, p in enumerate(pos):
        if p == 'X': continue
        t = int(p)
        trastes.append(t)
        notas.append(NOTAS[(CORDAS_MIDI[c] + t) % 12])

    if not notas:
        return "rejeitado", "shape.vazio", "", None, None

    tocados = {idx(n) for n in notas}
    presos = [t for t in trastes if t > 0]
    span = (max(presos) - min(presos) + 1) if presos else 1
    tmax = max(trastes)

    falhos = []
    if tocados - permitidas:            falhos.append("harmonia.notas_pertencem")
    if ti not in tocados:               falhos.append("harmonia.fundamental")
    if tipo not in SEM_TERCA:
        terca = 3 if 3 in TIPOS[tipo] else 4
        if (ti + terca) % 12 not in tocados: falhos.append("harmonia.terca")
    if tipo in TRIADES or tipo in QUINTA_ALTERADA:
        q = next((i for i in TIPOS[tipo] if i in (6,7,8)), None)
        if q is not None and (ti + q) % 12 not in tocados:
            falhos.append("harmonia.quinta")
    if tipo in EXTENSAO and (ti + EXTENSAO[tipo]) % 12 not in tocados:
        falhos.append("harmonia.extensao")
    if span > LIMITE_ABERTURA:  falhos.append("fisica.abertura")

    if falhos:
        return "rejeitado", ",".join(falhos), "-".join(notas), span, tmax
    if tmax > LIMITE_ALCANCE:
        return "valido_inacessivel", "fisica.alcance", "-".join(notas), span, tmax
    if fontes_externas is not None and fontes_externas == 0:
        return "valido_raro", "", "-".join(notas), span, tmax
    return "valido", "", "-".join(notas), span, tmax

def main():
    """Delega para teste_regua_v21.py, que compara contra as tabelas
    SHAPES_APROVADOS/SHAPES_EM_AUDITORIA/SHAPES_REPROVADOS (fonte de verdade
    atual). Evita duplicar aqui a mesma logica de comparacao."""
    import subprocess, sys as _sys
    r = subprocess.run([_sys.executable, os.path.join(DIR, "teste_regua_v21.py")])
    _sys.exit(r.returncode)

if __name__ == "__main__":
    main()
