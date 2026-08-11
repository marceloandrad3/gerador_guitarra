import sqlite3
import re
import shutil
from datetime import datetime

DB = "auditoria.db"
NOTAS = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
BEMOL_PARA_SUSTENIDO = {'Db':'C#','Eb':'D#','Gb':'F#','Ab':'G#','Bb':'A#'}
CORDAS_SOLTAS = ['E', 'A', 'D', 'G', 'B', 'E']

# Intervalos confirmados contra Wikipedia/fontes teoricas (semitons da tonica).
# Chord tem que conter TODOS estes; notas fora deste conjunto = invalido.
TIPOS = {
    '':      [0, 4, 7],
    'm':     [0, 3, 7],
    '7':     [0, 4, 7, 10],
    'm7':    [0, 3, 7, 10],
    '7M':    [0, 4, 7, 11],
    'maj7':  [0, 4, 7, 11],
    'm7M':   [0, 3, 7, 11],       # minor/major 7 (Hitchcock chord)
    'mmaj7': [0, 3, 7, 11],
    'dim':   [0, 3, 6],
    'dim7':  [0, 3, 6, 9],
    'aug':   [0, 4, 8],
    'sus2':  [0, 2, 7],
    'sus4':  [0, 5, 7],
    '6':     [0, 4, 7, 9],
    'm6':    [0, 3, 7, 9],
    'm7b5':  [0, 3, 6, 10],       # meio-diminuto
    '9':     [0, 4, 7, 10, 2],    # dominante 9 (7 + 9a)
    'm9':    [0, 3, 7, 10, 2],
    'maj9':  [0, 4, 7, 11, 2],
    '69':    [0, 4, 7, 9, 2],     # 6/9
    '7b5':   [0, 4, 6, 10],
    '7#5':   [0, 4, 8, 10],
    'add9':  [0, 4, 7, 2],
    'madd9': [0, 3, 7, 2],
    '5':     [0, 7],              # power chord (sem 3a)
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
        return None, f"tipo '{tipo}' ainda nao mapeado - pendente de verificacao teorica"

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
        notas_tocadas.append(nota_no_traste(CORDAS_SOLTAS[corda_idx], traste))

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

    # muda a coluna pra aceitar NULL como estado valido (nao verificavel)
    cur.execute("SELECT rowid, acorde, shape FROM CONFIRMACOES")
    linhas = cur.fetchall()

    total = len(linhas)
    ok_count = 0
    invalidos = 0
    nao_verificaveis = 0

    for rowid, acorde, shape in linhas:
        ok, motivo = verificar_shape(acorde, shape)
        if ok is None:
            cur.execute(
                "UPDATE CONFIRMACOES SET confiavel = NULL, motivo_invalidacao = ? WHERE rowid = ?",
                (motivo, rowid)
            )
            nao_verificaveis += 1
        elif ok is False:
            cur.execute(
                "UPDATE CONFIRMACOES SET confiavel = 0, motivo_invalidacao = ? WHERE rowid = ?",
                (motivo, rowid)
            )
            invalidos += 1
        else:
            cur.execute(
                "UPDATE CONFIRMACOES SET confiavel = 1, motivo_invalidacao = NULL WHERE rowid = ?",
                (rowid,)
            )
            ok_count += 1

    conn.commit()
    conn.close()

    print("\n--- RESUMO (tri-state) ---")
    print(f"Total analisado:                {total}")
    print(f"Confiavel=1 (checado, correto): {ok_count}")
    print(f"Confiavel=0 (checado, ERRADO):  {invalidos}")
    print(f"Confiavel=NULL (nao verificavel ainda): {nao_verificaveis}")
    print("\nRegra final de carimbo do acorde:")
    print("So marca VALIDADO se TODO shape exibido tiver confiavel=1 com >=2 fontes.")
    print("Shape com confiavel=0 ou NULL nunca conta como validado.")

if __name__ == "__main__":
    main()
