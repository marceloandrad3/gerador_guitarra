#!/usr/bin/env python3
"""
Reconstroi auditoria.db com schema generico (N fontes) e ingere o
chords-db (tombatossals, GitHub, MIT license) como fonte independente
adicional, alem de migrar os dados ja coletados (nosso gerador + JGuitar).

NAO apaga o banco antigo: renomeia para auditoria_OLD_<timestamp>.db
e cria um auditoria.db novo do zero.
"""
import sqlite3
import json
import os
import shutil
import datetime
import urllib.request
import ssl
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = None

DB_PATH = "auditoria.db"
CHORDS_DB_URL = "https://raw.githubusercontent.com/tombatossals/chords-db/master/lib/guitar.json"

CHORDSDB_KEY_PARA_NOSSO = {
    "C": "C", "C#": "C#", "D": "D", "Eb": "D#", "E": "E", "F": "F",
    "F#": "F#", "G": "G", "Ab": "G#", "A": "A", "Bb": "A#", "B": "B",
}

CHORDSDB_SUFFIX_PARA_NOSSO = {
    "major": "", "minor": "m", "7": "7", "m7": "m7", "maj7": "7M",
    "mmaj7": "m7M", "dim": "dim", "dim7": "dim7", "aug": "aug",
    "sus2": "sus2", "sus4": "sus4", "6": "6", "m6": "m6", "9": "9",
    "add9": "add9",
}


def timestamp():
    return datetime.datetime.now().isoformat(timespec="seconds")


def backup_banco_antigo():
    if os.path.exists(DB_PATH):
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = f"auditoria_OLD_{stamp}.db"
        shutil.copy(DB_PATH, destino)
        print(f"[OK] Backup do banco antigo salvo em: {destino}")
        return destino
    return None


def criar_schema_novo(con):
    con.executescript("""
        DROP TABLE IF EXISTS fontes;
        DROP TABLE IF EXISTS confirmacoes;

        CREATE TABLE FONTES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            tipo TEXT,
            url TEXT
        );

        CREATE TABLE CONFIRMACOES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            acorde TEXT NOT NULL,
            shape TEXT NOT NULL,
            fonte_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            UNIQUE(acorde, shape, fonte_id),
            FOREIGN KEY(fonte_id) REFERENCES fontes(id)
        );
    """)
    con.commit()
    print("[OK] Schema novo criado (tabelas fontes + confirmacoes).")


def get_fonte_id(con, nome, tipo=None, url=None):
    con.execute(
        "INSERT OR IGNORE INTO FONTES (nome, tipo, url) VALUES (?, ?, ?)",
        (nome, tipo, url),
    )
    con.commit()
    cur = con.execute("SELECT id FROM FONTES WHERE nome = ?", (nome,))
    return cur.fetchone()[0]


def registrar(con, acorde, shape, fonte_id, agora):
    con.execute("""
        INSERT OR IGNORE INTO CONFIRMACOES (acorde, shape, fonte_id, data)
        VALUES (?, ?, ?, ?)
    """, (acorde, shape, fonte_id, agora))


def migrar_dados_antigos(con, caminho_antigo, agora):
    if not caminho_antigo or not os.path.exists(caminho_antigo):
        print("[AVISO] Nenhum banco antigo encontrado para migrar.")
        return 0

    fonte_nosso = get_fonte_id(con, "nosso", tipo="interno")
    fonte_jguitar = get_fonte_id(con, "jguitar", tipo="scraper",
                                  url="https://jguitar.com")

    con_antigo = sqlite3.connect(caminho_antigo)
    cur = con_antigo.execute("SELECT acorde, shape, gerado_por FROM auditoria")
    linhas = cur.fetchall()
    con_antigo.close()

    total = 0
    for acorde, shape, gerado_por in linhas:
        shape_norm = ",".join(p.strip().upper() for p in shape.split(","))
        if gerado_por in ("nosso", "ambos"):
            registrar(con, acorde, shape_norm, fonte_nosso, agora)
            total += 1
        if gerado_por in ("jguitar", "ambos"):
            registrar(con, acorde, shape_norm, fonte_jguitar, agora)
            total += 1
    con.commit()
    print(f"[OK] Migrados {total} registros do banco antigo "
          f"({len(linhas)} linhas originais) para nosso/jguitar.")
    return total


def baixar_chords_db():
    print(f"[..] Baixando chords-db de {CHORDS_DB_URL}")
    req = urllib.request.Request(CHORDS_DB_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as resp:
        dados = json.loads(resp.read().decode("utf-8"))
    print(f"[OK] chords-db baixado ({len(dados.get('chords', {}))} grupos de tonica).")
    return dados


def ingerir_chords_db(con, dados, agora):
    fonte_id = get_fonte_id(con, "chords_db", tipo="dataset",
                             url="https://github.com/tombatossals/chords-db")
    total = 0
    ignorados_suffix = set()
    ignorados_key = set()

    for key_raw, lista_acordes in dados.get("chords", {}).items():
        for entrada in lista_acordes:
            key = entrada.get("key", key_raw)
            suffix = entrada.get("suffix", "")
            tonica = CHORDSDB_KEY_PARA_NOSSO.get(key)
            tipo = CHORDSDB_SUFFIX_PARA_NOSSO.get(suffix)
            if tonica is None:
                ignorados_key.add(key)
                continue
            if tipo is None:
                ignorados_suffix.add(suffix)
                continue
            acorde = tonica + tipo
            for pos in entrada.get("positions", []):
                frets = pos.get("frets")
                if not frets or len(frets) != 6:
                    continue
                shape = ",".join("X" if f == -1 else str(f) for f in frets)
                registrar(con, acorde, shape, fonte_id, agora)
                total += 1
    con.commit()
    print(f"[OK] Ingeridos {total} shapes do chords_db "
          f"(cobrindo os 15 tipos suportados pelo nosso gerador).")
    if ignorados_suffix:
        print(f"[INFO] Sufixos do chords-db ainda nao mapeados "
              f"(ignorados por ora, {len(ignorados_suffix)} tipos): "
              f"{sorted(ignorados_suffix)[:20]}...")
    return total


def relatorio_validacao(con):
    cur = con.execute("""
        SELECT acorde, shape, COUNT(DISTINCT fonte_id) as n_fontes
        FROM CONFIRMACOES
        GROUP BY acorde, shape
    """)
    linhas = cur.fetchall()

    por_acorde = {}
    for acorde, shape, n_fontes in linhas:
        d = por_acorde.setdefault(acorde, {"total_shapes": 0, "validados": 0})
        d["total_shapes"] += 1
        if n_fontes >= 2:
            d["validados"] += 1

    total_acordes = len(por_acorde)
    acordes_com_pelo_menos_1_validado = sum(
        1 for d in por_acorde.values() if d["validados"] > 0
    )
    total_shapes = sum(d["total_shapes"] for d in por_acorde.values())
    total_shapes_validados = sum(d["validados"] for d in por_acorde.values())

    print("=" * 60)
    print(" RELATORIO DE VALIDACAO (>=2 fontes confirmando o mesmo shape)")
    print("=" * 60)
    print(f" Acordes com dados:                  {total_acordes}")
    print(f" Acordes com >=1 shape validado:      {acordes_com_pelo_menos_1_validado}")
    print(f" Total de shapes distintos:           {total_shapes}")
    print(f" Total de shapes validados:           {total_shapes_validados}")
    print("-" * 60)
    print(" Amostra (10 acordes):")
    for acorde in sorted(por_acorde)[:10]:
        d = por_acorde[acorde]
        print(f"   {acorde:<6} {d['validados']:>2}/{d['total_shapes']:<3} shapes validados")
    print("=" * 60)


def main():
    caminho_antigo = backup_banco_antigo()
    con = sqlite3.connect(DB_PATH)
    agora = timestamp()

    criar_schema_novo(con)
    migrar_dados_antigos(con, caminho_antigo, agora)

    try:
        dados = baixar_chords_db()
        ingerir_chords_db(con, dados, agora)
    except Exception as e:
        print(f"[ERRO] Falha ao baixar/ingerir chords-db: {e}")
        print("        (prosseguindo so com nosso + jguitar)")

    relatorio_validacao(con)
    con.close()


if __name__ == "__main__":
    main()
