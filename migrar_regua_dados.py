import ast

with open("regua_v21.py") as f:
    src = f.read()

OLD = '''import sqlite3, os

DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(DIR, "auditoria.db")
NOTAS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
CORDAS_MIDI = [40,45,50,55,59,64]   # E A D G B E (grave->agudo)
REGRA = "v2.1-dedutiva"

TIPOS = {
    '':[0,4,7], 'm':[0,3,7], '7':[0,4,7,10], 'm7':[0,3,7,10],
    '7M':[0,4,7,11], 'maj7':[0,4,7,11], 'm7M':[0,3,7,11], 'mmaj7':[0,3,7,11],
    'dim':[0,3,6], 'dim7':[0,3,6,9], 'aug':[0,4,8],
    'sus2':[0,2,7], 'sus4':[0,5,7], '6':[0,4,7,9], 'm6':[0,3,7,9],
    'm7b5':[0,3,6,10], '9':[0,4,7,10,2], 'm9':[0,3,7,10,2], 'maj9':[0,4,7,11,2],
    '69':[0,4,7,9,2], '7b5':[0,4,6,10], '7#5':[0,4,8,10],
    'add9':[0,4,7,2], 'madd9':[0,3,7,2], '5':[0,7],
}
SEM_TERCA = {'sus2','sus4','5'}
TRIADES   = {'','m','dim','aug','sus2','sus4'}
EXTENSAO  = {'7':10,'m7':10,'7M':11,'maj7':11,'m7M':11,'mmaj7':11,'dim7':9,
             '6':9,'m6':9,'m7b5':10,'9':2,'m9':2,'maj9':2,'69':9,
             '7b5':10,'7#5':10,'add9':2,'madd9':2}
QUINTA_ALTERADA = {'dim','dim7','aug','m7b5','7b5','7#5'}'''

NEW = '''import sqlite3, os

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
LIMITE_ALCANCE = _LIMITES.get('fisica.alcance', 15)'''

assert OLD in src, "bloco de dados nao encontrado"
src = src.replace(OLD, NEW)

# usar os limiares carregados do banco em vez dos numeros fixos 4 e 15
OLD2 = '''    if span > 4:  falhos.append("fisica.abertura")  # 4 casas ocupadas

    if falhos:
        return "rejeitado", ",".join(falhos), "-".join(notas), span, tmax
    if tmax > 15:
        return "valido_inacessivel", "fisica.alcance", "-".join(notas), span, tmax'''

NEW2 = '''    if span > LIMITE_ABERTURA:  falhos.append("fisica.abertura")

    if falhos:
        return "rejeitado", ",".join(falhos), "-".join(notas), span, tmax
    if tmax > LIMITE_ALCANCE:
        return "valido_inacessivel", "fisica.alcance", "-".join(notas), span, tmax'''

assert OLD2 in src, "bloco de limiares nao encontrado"
src = src.replace(OLD2, NEW2)

ast.parse(src)
with open("regua_v21.py", "w") as f:
    f.write(src)
print("regua_v21.py: TIPOS, SEM_TERCA, TRIADES, QUINTA_ALTERADA, EXTENSAO e limiares agora vem do banco")
