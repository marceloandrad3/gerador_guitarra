#!/usr/bin/env python3
"""DRY-RUN. Nao escreve nada. So mostra o que a fonte 5 traria."""
import sqlite3
from regua_v21 import avaliar, REGRA

# ORIGEM: 'publicado' = frets literais na pagina; 'derivado' = frets
# deduzidos das notas-por-corda publicadas, afinacao padrao.
CANDIDATOS = [
    # guitar-chord.org /aug.html - formas moveis, raiz na 5a corda
    ("Caug",  "X,3,2,1,1,X",   "publicado"),
    ("C#aug", "X,4,3,2,2,X",   "publicado"),
    ("Daug",  "X,5,4,3,3,X",   "publicado"),
    ("D#aug", "X,6,5,4,4,X",   "publicado"),
    ("Eaug",  "X,7,6,5,5,X",   "publicado"),
    ("Faug",  "X,8,7,6,6,X",   "publicado"),
    ("F#aug", "X,9,8,7,7,X",   "publicado"),
    ("Gaug",  "X,10,9,8,8,X",  "publicado"),
    ("G#aug", "X,11,10,9,9,X", "publicado"),
    ("Aaug",  "X,12,11,10,10,X","publicado"),
    ("A#aug", "X,13,12,11,11,X","publicado"),
    ("Baug",  "X,2,1,0,0,X",   "publicado"),
    # /aug.html - voicings de 3 cordas
    ("Aaug",  "X,X,X,2,2,1",   "publicado"),
    ("Baug",  "X,X,X,4,4,3",   "publicado"),
    ("Caug",  "X,X,X,5,5,4",   "publicado"),
    ("Daug",  "X,X,X,7,7,6",   "publicado"),
    ("Eaug",  "X,X,X,9,9,8",   "publicado"),
    ("Faug",  "X,X,X,10,10,9", "publicado"),
    ("Gaug",  "X,X,X,12,12,11","publicado"),
    # /aug.html - posicoes abertas
    ("Caug",  "X,3,2,1,1,0",   "publicado"),
    ("Daug",  "X,X,0,3,3,2",   "publicado"),
    ("Eaug",  "X,X,2,1,1,0",   "publicado"),
    ("Faug",  "X,X,3,2,2,1",   "publicado"),
    ("Gaug",  "3,2,1,0,0,3",   "publicado"),
    ("Aaug",  "X,0,3,2,2,1",   "publicado"),
    ("Baug",  "X,2,1,0,0,3",   "publicado"),
    # /sus2-chords.html - derivados das notas por corda
    ("Bsus2", "X,2,4,4,2,2",   "derivado"),
    ("Esus2", "0,2,4,4,0,0",   "derivado"),
]

con = sqlite3.connect("auditoria.db")
cur = con.cursor()
FONTE = 5

print(f"{'acorde':8s} {'shape':18s} {'origem':10s} {'veredito':12s} "
      f"{'span':4s} {'tmax':4s} {'fontes_hoje':11s} {'depois':6s} acao")
print("-" * 100)

novos = liberam = ja_tem = reprovam = 0
for acorde, shape, origem in CANDIDATOS:
    ver, falhos, notas, span, tmax = avaliar(acorde, shape)

    cur.execute("SELECT COUNT(DISTINCT fonte_id) FROM confirmacoes "
                "WHERE acorde=? AND shape=? AND confiavel=1", (acorde, shape))
    n_hoje = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM confirmacoes "
                "WHERE acorde=? AND shape=? AND fonte_id=?", (acorde, shape, FONTE))
    ja = cur.fetchone()[0]
    cur.execute("SELECT veredito FROM vereditos WHERE acorde=? AND shape=? "
                "AND regra_versao=?", (acorde, shape, REGRA))
    r = cur.fetchone()
    em_vereditos = r[0] if r else None

    depois = n_hoje if ja else n_hoje + 1

    if not ver.startswith("valido"):
        acao = f"REPROVA regua ({falhos})"; reprovam += 1
    elif ja:
        acao = "ja registrado nesta fonte"; ja_tem += 1
    elif em_vereditos is None:
        acao = "SHAPE NOVO -> precisa auditar+gravar"; novos += 1
    elif n_hoje == 1 and depois >= 2:
        acao = "LIBERA fonte_unica"; liberam += 1
    else:
        acao = f"soma fonte (vereditos={em_vereditos})"

    print(f"{acorde:8s} {shape:18s} {origem:10s} {ver:12s} "
          f"{str(span):4s} {str(tmax):4s} {n_hoje:11d} {depois:6d} {acao}")

print("-" * 100)
print(f"reprovados pela regua: {reprovam}   ja na fonte 5: {ja_tem}   "
      f"liberam fonte_unica: {liberam}   shapes novos: {novos}")
print("\nNADA FOI GRAVADO. Dry-run.")
con.close()
