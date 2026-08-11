#!/usr/bin/env python3
"""
Ingere a fonte queroaprenderagora.com.br (QAA).

Regras (definidas por Marcelo):
  - traste maximo <= 12
  - sem pestana dupla: 2+ dedos DIFERENTES cobrindo 2+ cordas cada um.
    Uma pestana unica (dedo 1 atravessando varias cordas) e' normal.
    A deteccao usa calcular_dedos_e_pestana() do proprio projeto, para
    ficar coerente com o que o app desenha.
  - shapes abertos (corda solta) nao transpoem
  - moldes moveis transpoem para as 12 tonicas (deducao valida)
"""
import sqlite3
from collections import Counter
from datetime import datetime
from dedicacao import calcular_dedos_e_pestana

DATA = datetime.now().isoformat(timespec="seconds")
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

LIDOS = {
    "Csus4": ["X,3,5,5,6,3", "X,3,3,0,1,3", "X,3,3,0,1,1",
              "8,8,10,10,8,8", "8,10,10,10,8,8", "X,3,3,5,6,3"],
    "Esus4": ["0,2,2,2,0,0", "0,0,2,2,0,0", "X,7,7,9,10,7",
              "X,7,9,9,10,7", "12,12,9,9,12,X", "12,12,9,9,10,X",
              "12,12,14,14,12,12", "12,14,14,14,12,12", "X,X,2,4,5,5"],
    "Asus4": ["X,0,2,2,3,0", "X,0,0,2,3,0", "5,5,7,7,5,5",
              "X,12,12,14,15,12", "5,7,7,7,5,5", "X,12,14,14,15,12",
              "5,5,2,2,3,X", "X,X,7,9,10,10", "5,5,2,2,5,X"],
}

# offsets a partir da casa da pestana, corda 6 -> 1
MOLDES_MOVEIS = [
    ("forma_E_sus4", [0, 0, 2, 2, 0, 0], 6),
    ("forma_A_sus4", [None, 0, 2, 2, 3, 0], 5),
]
SOLTA_IDX = {6: 4, 5: 9}


def parse(shape):
    return [None if p.strip().upper() == "X" else int(p.strip())
            for p in shape.split(",")]


def traste_max(shape):
    v = [x for x in parse(shape) if x is not None and x > 0]
    return max(v) if v else 0


def tem_pestana_dupla(shape):
    casas = parse(shape)
    dedos, _ = calcular_dedos_e_pestana(casas)
    cont = Counter(d for d in dedos if d and d > 0)
    barras = [d for d, n in cont.items() if n >= 2]
    return len(barras) >= 2


def aceita(shape):
    if traste_max(shape) > 12:
        return False, "traste acima de 12"
    if tem_pestana_dupla(shape):
        return False, "pestana dupla (2 dedos em barra)"
    return True, ""


def transpor(offsets, corda_tonica, tonica_alvo):
    idx_alvo = NOTAS.index(tonica_alvo)
    casa = (idx_alvo - SOLTA_IDX[corda_tonica]) % 12
    if casa == 0:
        casa = 12
    return ",".join("X" if o is None else str(casa + o) for o in offsets)


def main():
    conn = sqlite3.connect("auditoria.db")
    cur = conn.cursor()

    cur.execute("SELECT id FROM FONTES WHERE nome = 'queroaprenderagora'")
    row = cur.fetchone()
    if row:
        fonte_id = row[0]
        print(f"Fonte ja existia (id={fonte_id})")
    else:
        cur.execute("INSERT INTO FONTES (nome, tipo, url) VALUES (?, ?, ?)",
                    ("queroaprenderagora", "site",
                     "https://queroaprenderagora.com.br/acorde-c4-violao/"))
        fonte_id = cur.lastrowid
        print(f"Fonte cadastrada (id={fonte_id})")

    candidatos = {}
    for acorde, shapes in LIDOS.items():
        candidatos.setdefault(acorde, set()).update(shapes)
    for _, offsets, corda in MOLDES_MOVEIS:
        for tonica in NOTAS:
            candidatos.setdefault(tonica + "sus4", set()).add(
                transpor(offsets, corda, tonica))

    inseridos = ja_tinha = 0
    rejeitados = []
    for acorde in sorted(candidatos):
        for shape in sorted(candidatos[acorde]):
            ok, motivo = aceita(shape)
            if not ok:
                rejeitados.append((acorde, shape, motivo))
                continue
            cur.execute("SELECT COUNT(*) FROM CONFIRMACOES "
                        "WHERE acorde=? AND shape=? AND fonte_id=?",
                        (acorde, shape, fonte_id))
            if cur.fetchone()[0]:
                ja_tinha += 1
                continue
            cur.execute("INSERT INTO CONFIRMACOES "
                        "(acorde, shape, fonte_id, data, confiavel) "
                        "VALUES (?, ?, ?, ?, 1)",
                        (acorde, shape, fonte_id, DATA))
            inseridos += 1
    conn.commit()

    print(f"\nInseridos: {inseridos}   Ja existiam: {ja_tinha}   "
          f"Rejeitados: {len(rejeitados)}")
    for a, s, m in rejeitados:
        print(f"   {a:10s} {s:22s} -> {m}")

    print("\n--- Cobertura sus4 ---")
    for tonica in NOTAS:
        acorde = tonica + "sus4"
        cur.execute("SELECT COUNT(DISTINCT shape) FROM CONFIRMACOES "
                    "WHERE acorde=?", (acorde,))
        tot = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT fonte_id) FROM CONFIRMACOES "
                    "WHERE acorde=? AND confiavel=1", (acorde,))
        print(f"  {acorde:8s} shapes={tot:3d}  fontes={cur.fetchone()[0]}")
    conn.close()


if __name__ == "__main__":
    main()
