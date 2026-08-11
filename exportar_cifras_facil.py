#!/usr/bin/env python3
"""
Exporta o banco de acordes para o app Cifras Facil.

CONTRATO COM O CIFRAS FACIL (mandatorio, vale nos dois lados):

  Este projeto E' PARTE do Cifras Facil. Roda fora, mas e' o componente
  que resolve TODA a complexidade musical do produto. O app e' consumidor:
  le o JSON e desenha. Nada mais.

FONTE UNICA DE DADOS: tabela SHAPES_APROVADOS. Nao chama /gerar, nao
recalcula dedos/pestana/dificuldade - a tabela ja guarda o diagrama
pronto (garantido pelos scripts de ingestao e por liberar_fonte_unica.py).
Ler uma linha = montar um acorde e um diagrama 100% corretos.

Uso (servidor NAO precisa estar rodando):
    python3 exportar_cifras_facil.py
"""
import json
import sqlite3
from datetime import datetime, timezone

from gerador_web_dinamico import (
    NOTAS, TIPO_SINONIMOS, parse_acorde, normalizar_tipo, parsear_inversao,
)

DB = "auditoria.db"
REGRAS = ("v2.1-dedutiva", "v2.2-dedutiva")
SAIDA = "cifras_facil_chord_dictionary.json"


def linhas_aprovadas():
    """Le 100% dos shapes de SHAPES_APROVADOS - unica fonte de dados."""
    con = sqlite3.connect(DB)
    marcadores = ",".join("?" for _ in REGRAS)
    linhas = con.execute(
        f"SELECT acorde, shape, dedos, pestana_casa, pestana_corda_min, "
        f"pestana_corda_max, dificuldade_score, dificuldade_nivel, "
        f"dificuldade_rotulo, n_fontes_confiaveis, veredito_original "
        f"FROM SHAPES_APROVADOS WHERE regra_versao IN ({marcadores}) "
        f"ORDER BY acorde, id", REGRAS).fetchall()
    con.close()
    return linhas


def tonica_e_tipo(acorde):
    """Deriva tonica/tipo (root/quality) diretamente do nome do acorde,
    igual ao gerador faz internamente. Formula validada contra o /gerar
    real (C/E -> tonica=C tipo=/E ; Am7/G -> tonica=A tipo=m7/G)."""
    acorde_base, baixo = parsear_inversao(acorde)
    tonica, tipo = parse_acorde(acorde_base)
    tipo = normalizar_tipo(tipo)
    if baixo:
        tipo = tipo + "/" + baixo
    return tonica, tipo


def converter(shape, dedos, p_casa, p_min, p_max, dif_score, dif_nivel,
              dif_rotulo, n_fontes, veredito):
    """Monta o fingering pronto a partir de uma linha de SHAPES_APROVADOS."""
    partes = [p.strip().upper() for p in shape.split(",")]
    posicoes = [None if p == "X" else int(p) for p in partes]
    fingers = [int(d) for d in dedos.split(",")]

    NIVEL_LABEL = {1: "Muito Facil", 2: "Facil", 3: "Medio",
                   4: "Dificil", 5: "Muito Dificil"}

    return {
        "positions": posicoes,
        "fingers": fingers,
        "barre": ({"fret": p_casa, "fromString": p_min, "toString": p_max}
                  if p_casa is not None else None),
        "difficulty": {
            "level": dif_nivel,
            "label": dif_rotulo or NIVEL_LABEL.get(dif_nivel, "Medio"),
            "score": dif_score,
        },
        "baseFret": min([p for p in posicoes if p], default=0),
        # Todo shape em SHAPES_APROVADOS passou em harmonia_completa E
        # (2+ fontes confiaveis OU harmonia.baixo aprovado para slash).
        "shapeValidated": True,
        "externalSource": n_fontes >= 2,
        "verdict": veredito,
    }


def construir_indice(simbolos_no_dicionario):
    """Mapa 'grafia digitada' -> 'chave do dicionario'."""
    tonicas = list(NOTAS) + ["Db", "Eb", "Gb", "Ab", "Bb"]
    tipos = {q for q in (d["quality"] for d in simbolos_no_dicionario.values())}
    tipos |= set(TIPO_SINONIMOS)
    tipos |= {"7(9)", "7/9"}

    indice = {}
    for tonica in tonicas:
        for tipo in sorted(tipos):
            grafia = tonica + tipo
            try:
                raiz, qual = parse_acorde(grafia)
            except (ValueError, IndexError):
                continue
            chave = raiz + normalizar_tipo(qual)
            if chave in simbolos_no_dicionario and grafia != chave:
                indice[grafia] = chave
    return indice


def main():
    dicionario, total_shapes = {}, 0

    for acorde, shape, dedos, p_casa, p_min, p_max, dif_s, dif_n, dif_r, n_f, ver in linhas_aprovadas():
        fingering = converter(shape, dedos, p_casa, p_min, p_max, dif_s, dif_n, dif_r, n_f, ver)

        if acorde not in dicionario:
            tonica, tipo = tonica_e_tipo(acorde)
            dicionario[acorde] = {
                "symbol": acorde,
                "root": tonica,
                "quality": tipo,
                "fingerings": [],
            }
        dicionario[acorde]["fingerings"].append(fingering)
        total_shapes += 1

    for acorde, entry in dicionario.items():
        entry["fingerings"].sort(
            key=lambda f: (f["difficulty"]["level"], f["difficulty"]["score"]))

    saida = {
        "_meta": {
            "geradoEm": datetime.now(timezone.utc).isoformat(),
            "origem": "gerador_guitarra - tabela SHAPES_APROVADOS (fonte unica)",
            "criterio": (
                "Cada linha de SHAPES_APROVADOS ja e' um diagrama completo e "
                "validado: shape, dedos, pestana e dificuldade calculados no "
                "momento da aprovacao. O app nao decide, nao recalcula."
            ),
            "totalAcordes": len(dicionario),
            "totalDigitacoes": total_shapes,
        },
        "chords": dicionario,
        "aliases": construir_indice(dicionario),
    }

    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"Exportado: {SAIDA}")
    print(f"Acordes: {len(dicionario)}  |  Digitacoes: {total_shapes}"
          f"  |  Apelidos: {len(saida['aliases'])}")


if __name__ == "__main__":
    main()
