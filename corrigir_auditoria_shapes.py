import sqlite3
import re
import shutil
from datetime import datetime

DB = "auditoria.db"
NOTAS = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
BEMOL_PARA_SUSTENIDO = {'Db':'C#','Eb':'D#','Gb':'F#','Ab':'G#','Bb':'A#'}
CORDAS_SOLTAS = ['E', 'A', 'D', 'G', 'B', 'E']

TIPOS = {
    '':      [0, 4, 7],
    'm':     [0, 3, 7],
    '7':     [0, 4, 7, 10],
    'm7':    [0, 3, 7, 10],
    '7M':    [0, 4, 7, 11],
    'maj7':  [0, 4, 7, 11],
    'dim':   [0, 3, 6],
    'dim7':  [0, 3, 6, 9],
    'aug':   [0, 4, 8],
    'sus2':  [0, 2, 7],
    'sus4':  [0, 5, 7],
    '6':     [0, 4, 7, 9],
    'm6':    [0, 3, 7, 9],
    'm7b5':  [0, 3, 6, 10],
}

def indice_nota(nome):
    nome = BEMOL_PARA_SUSTENIDO.get(nome, nome)
    return NOTAS.index(nome)

def parse_acorde(acorde):
    base = acorde.split('/')[0]
    m = re.match(r'^([A-G])(#|b)?(.*)$', base)
    if not m:
        return None, None
    tonica = m.group(1) + (m.group(2) or '')
    tipo = m.group(3)
    return tonica, tipo

def nota_no_traste(corda_solta, traste):
    return NOTAS[(indice_nota(corda_solta) + traste) % 12]

def verificar_shape(acorde, shape_str):
    tonica, tipo = parse_acorde(acorde)
    if tonica is None or tipo not in TIPOS:
        return None, f"tipo '{tipo}' nao mapeado - checar manualmente"

    tonica_idx = indice_nota(tonica)
    intervalos_validos = {(tonica_idx + iv) % 12 for iv in TIPOS[tipo]}

    posicoes = [p.strip() for p in shape_str.split(',')]
    if len(posicoes) != 6:
        return False, f"shape malformado: '{shape_str}'"

    notas_tocadas = []
    for corda_idx, pos in enumerate(posicoes):
        if pos.upper() == 'X':
            continue
        try:
            traste = int(pos)
        except ValueError:
            return False, f"posicao invalida '{pos}' na corda {corda_idx+1}"
        nota = nota_no_traste(CORDAS_SOLTAS[corda_idx], traste)
        notas_tocadas.append(nota)

    if not notas_tocadas:
        return False, "shape sem nenhuma nota tocada"

    notas_idx_tocadas = {indice_nota(n) for n in notas_tocadas}
    fora = notas_idx_tocadas - intervalos_validos
    if fora:
        nomes_fora = [NOTAS[i] for i in fora]
        return False, f"nota(s) fora do acorde: {', '.join(nomes_fora)} nao pertence(m) a {acorde}"

    if tonica_idx not in notas_idx_tocadas:
        return False, f"tonica {tonica} ausente no shape"

    return True, None


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{DB}.bak_{ts}"
    shutil.copy(DB, backup_name)
    print(f"Backup criado: {backup_name}")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(confirmacoes)")
    colunas_existentes = {row[1] for row in cur.fetchall()}
    if 'confiavel' not in colunas_existentes:
        cur.execute("ALTER TABLE CONFIRMACOES ADD COLUMN confiavel INTEGER NOT NULL DEFAULT 1")
        print("Coluna 'confiavel' adicionada.")
    if 'motivo_invalidacao' not in colunas_existentes:
        cur.execute("ALTER TABLE CONFIRMACOES ADD COLUMN motivo_invalidacao TEXT")
        print("Coluna 'motivo_invalidacao' adicionada.")
    conn.commit()

    cur.execute("SELECT rowid, acorde, shape, fonte_id FROM CONFIRMACOES")
    linhas = cur.fetchall()

    total = len(linhas)
    marcados_invalidos = 0
    nao_verificaveis = 0

    for rowid, acorde, shape, fonte_id in linhas:
        ok, motivo = verificar_shape(acorde, shape)
        if ok is None:
            nao_verificaveis += 1
            continue
        if ok is False:
            cur.execute(
                "UPDATE CONFIRMACOES SET confiavel = 0, motivo_invalidacao = ? WHERE rowid = ?",
                (motivo, rowid)
            )
            marcados_invalidos += 1
            print(f"[INVALIDADO] {acorde} | {shape} | fonte_id={fonte_id} | {motivo}")
        else:
            cur.execute(
                "UPDATE CONFIRMACOES SET confiavel = 1, motivo_invalidacao = NULL WHERE rowid = ?",
                (rowid,)
            )

    conn.commit()
    conn.close()

    print("\n--- RESUMO ---")
    print(f"Total de confirmacoes analisadas: {total}")
    print(f"Marcadas como NAO confiaveis: {marcados_invalidos}")
    print(f"Nao verificaveis automaticamente (tipo nao mapeado): {nao_verificaveis}")

if __name__ == "__main__":
    main()
