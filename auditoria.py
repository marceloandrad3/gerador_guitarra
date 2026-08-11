#!/usr/bin/env python3
"""
Auditor JGuitar - compara shapes do NOSSO gerador com os do JGuitar.

Para cada acorde do universo (12 tonicas x 15 tipos = 180 acordes):
  - Gera shapes com nosso sistema (gerar_dinamico)
  - Busca shapes no JGuitar (chordsearch)
  - Registra em SQLite (auditoria.db):
      match       = presente nos dois
      so_nosso    = so nosso sistema gerou (precisa 2a fonte para validar)
      so_jguitar  = JGuitar tem e NAO geramos (FALHA de cobertura)

Formato de shape (ambos): 6 campos separados por virgula, indice 0 = 6a corda.
Exemplo: X,3,2,0,1,0
"""

import datetime
import re
import sqlite3
import sys
import time
import ssl
import urllib.parse
import urllib.request

# macOS: Python oficial nem sempre tem certificados instalados.
# Usamos o bundle do certifi diretamente (nao depende do sistema).
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = None

from gerador_web_dinamico import gerar_dinamico, NOTAS

DB_PATH = "auditoria.db"
BASE_URL = "https://jguitar.com/chordsearch?chordsearch="
PAUSA_SEGUNDOS = 1.0

# Nosso tipo -> sufixo da query no JGuitar (mapeamento validado em teste)
TIPO_JGUITAR = {
    "":     "",
    "m":    "m",
    "7":    "7",
    "m7":   "m7",
    "7M":   "maj7",
    "m7M":  "mmaj7",
    "dim":  "dim",
    "dim7": "dim7",
    "aug":  "aug",
    "sus2": "sus2",
    "sus4": "sus4",
    "6":    "6",
    "m6":   "m6",
    "9":    "9",
    "add9": "add9",
}


def acorde_para_query(acorde):
    """Converte nome interno (ex: C7M, F#m7M) em query JGuitar (ex: Cmaj7, F#mmaj7)."""
    m = re.match(r"^([A-G][#b]?)(.*)$", acorde)
    if not m:
        return acorde
    tonica, tipo = m.group(1), m.group(2)
    return tonica + TIPO_JGUITAR.get(tipo, tipo)


# Shape = ultimo segmento do nome do PNG: ...-{shape}.png
# Shape = 6 campos (digito ou x) separados por %2C
PADRAO_SHAPE = r'/images/chordshape/[^"]*?-(?:\d+|[xX])(?:%2C(?:\d+|[xX])){5}\.png'


def universo_acordes():
    """12 tonicas x 15 tipos = 180 acordes."""
    for tonica in NOTAS:
        for tipo in TIPO_JGUITAR:
            yield tonica + tipo


def buscar_jguitar(acorde):
    """Retorna SET de shapes que o JGuitar publica para o acorde."""
    url = BASE_URL + urllib.parse.quote(acorde, safe="")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=20, context=SSL_CTX).read().decode("utf-8", errors="replace")
    shapes = set()
    for bruto in re.findall(PADRAO_SHAPE, html):
        segmento = bruto.rsplit("/", 1)[-1]   # nome do arquivo
        segmento = segmento.rsplit("-", 1)[-1]  # apos o ultimo traco
        segmento = segmento[:-4]                # remove .png
        shapes.add(urllib.parse.unquote(segmento).upper())
    return shapes


def shapes_nossos(acorde):
    """Retorna SET de shapes que o nosso gerador produz."""
    resultado = gerar_dinamico(acorde)
    return {
        ",".join(str(x).upper() for x in d["diagrama"])
        for d in resultado["diagramas"]
    }


def criar_banco():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            acorde TEXT NOT NULL,
            shape TEXT NOT NULL,
            gerado_por TEXT NOT NULL,
            status TEXT NOT NULL,
            validacao_extra TEXT,
            fonte_extra TEXT,
            data TEXT NOT NULL,
            UNIQUE(acorde, shape)
        )
    """)
    con.commit()
    return con


def registrar(con, acorde, shape, gerado_por, status, agora):
    con.execute("""
        INSERT INTO auditoria (acorde, shape, gerado_por, status, data)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(acorde, shape) DO UPDATE SET
            gerado_por = excluded.gerado_por,
            status = excluded.status,
            data = excluded.data
    """, (acorde, shape, gerado_por, status, agora))


def auditar_conjunto(con, agora, acordes):
    totais = {"acordes": 0, "match": 0, "so_nosso": 0, "so_jguitar": 0, "falhas": []}
    for acorde in acordes:
        totais["acordes"] += 1
        nosso = shapes_nossos(acorde)
        jg = buscar_jguitar(acorde_para_query(acorde))

        for s in nosso & jg:
            registrar(con, acorde, s, "ambos", "match", agora)
        for s in nosso - jg:
            registrar(con, acorde, s, "nosso", "so_nosso", agora)
        for s in jg - nosso:
            registrar(con, acorde, s, "jguitar", "so_jguitar", agora)
        con.commit()

        so_jg = len(jg - nosso)
        totais["match"] += len(nosso & jg)
        totais["so_nosso"] += len(nosso - jg)
        totais["so_jguitar"] += so_jg
        if so_jg:
            totais["falhas"].append((acorde, so_jg))

        print(f"[{totais['acordes']:>3}] {acorde:<8} "
              f"nosso={len(nosso):>2} jguitar={len(jg):>2} "
              f"match={len(nosso & jg):>2} so_nosso={len(nosso - jg):>2} "
              f"so_jguitar={so_jg:>2}")
        time.sleep(PAUSA_SEGUNDOS)
    return totais


def auditar(acordes=None):
    con = criar_banco()
    agora = datetime.datetime.now().isoformat(timespec="seconds")
    if acordes is None:
        acordes = universo_acordes()
    totais = auditar_conjunto(con, agora, acordes)
    con.close()

    print("=" * 60)
    print(f" Acordes auditados:          {totais['acordes']}")
    print(f" Shapes em comum (match):    {totais['match']}")
    print(f" So nosso (validar depois):  {totais['so_nosso']}")
    print(f" So JGuitar (FALHA nossa):   {totais['so_jguitar']}")
    if totais["falhas"]:
        print("-" * 60)
        print(" Acordes com voicings que NAO geramos:")
        for acorde, qtd in totais["falhas"]:
            print(f"   {acorde}: {qtd} voicing(s) ausente(s)")
    print("=" * 60)


if __name__ == "__main__":
    # Sem argumentos: audita os 180 acordes
    # Com argumentos: audita apenas os acordes informados (modo teste)
    auditar(sys.argv[1:] if len(sys.argv) > 1 else None)
