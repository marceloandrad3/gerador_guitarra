import sqlite3
import json
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

def fret_absoluto(f, base_fret):
    """Converte fret relativo (schema chords-db) para traste absoluto."""
    if f == -1:
        return "X"
    if f == 0:
        return "0"
    base = base_fret if base_fret else 1
    return str(base + f - 1)

def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{DB_PATH}.bak_{ts}"
    shutil.copy(DB_PATH, backup)
    print(f"[OK] Backup criado: {backup}")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("SELECT id FROM FONTES WHERE nome = 'chords_db'")
    row = cur.fetchone()
    if not row:
        print("[ERRO] fonte 'chords_db' nao encontrada.")
        return
    fonte_id = row[0]

    cur.execute("DELETE FROM CONFIRMACOES WHERE fonte_id = ?", (fonte_id,))
    print(f"[OK] Removidas {cur.rowcount} confirmacoes antigas (contaminadas) do chords_db.")
    con.commit()

    print(f"[..] Baixando chords-db de {CHORDS_DB_URL}")
    req = urllib.request.Request(CHORDS_DB_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as resp:
        dados = json.loads(resp.read().decode("utf-8"))
    print("[OK] chords-db baixado.")

    agora = timestamp()
    total = 0
    exemplos_corrigidos = []

    for key_raw, lista_acordes in dados.get("chords", {}).items():
        for entrada in lista_acordes:
            key = entrada.get("key", key_raw)
            suffix = entrada.get("suffix", "")
            tonica = CHORDSDB_KEY_PARA_NOSSO.get(key)
            tipo = CHORDSDB_SUFFIX_PARA_NOSSO.get(suffix)
            if tonica is None or tipo is None:
                continue
            acorde = tonica + tipo
            for pos in entrada.get("positions", []):
                frets = pos.get("frets")
                if not frets or len(frets) != 6:
                    continue
                base_fret = pos.get("baseFret", 1)
                shape = ",".join(fret_absoluto(f, base_fret) for f in frets)
                cur.execute("""
                    INSERT OR IGNORE INTO CONFIRMACOES (acorde, shape, fonte_id, data)
                    VALUES (?, ?, ?, ?)
                """, (acorde, shape, fonte_id, agora))
                total += 1
                if base_fret and base_fret > 1 and len(exemplos_corrigidos) < 5:
                    exemplos_corrigidos.append((acorde, frets, base_fret, shape))

    con.commit()
    con.close()

    print(f"\n[OK] Reingeridos {total} shapes do chords_db com baseFret corrigido.")
    print("\nExemplos de conversao (antes so gravava 'frets' cru, agora soma baseFret):")
    for acorde, frets_orig, base_fret, shape_corrigido in exemplos_corrigidos:
        print(f"  {acorde}: frets={frets_orig} baseFret={base_fret} -> shape absoluto: {shape_corrigido}")

if __name__ == "__main__":
    main()
