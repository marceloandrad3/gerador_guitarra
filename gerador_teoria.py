"""
Gerador de shapes por teoria musical (forca bruta sobre o braco).

Diferenca para gerador_web_dinamico.gerar_shapes_dinamicos: aquele so produz
shape quando existe um template CAGED cadastrado a mao para a qualidade do
acorde (CAGED_MAIOR, CAGED_MENOR7, etc.) - por isso tipos como m7b5, 7b5,
7#5, 69, m9, madd9, maj9 e "5" (power chord) nao tem NENHUM shape em NENHUM
tom no banco atual (confirmado em cifras_facil_chord_dictionary.json).

Esta funcao nao depende de templates nem de scraping: enumera por forca
bruta toda combinacao fisicamente possivel de casas nas 6 cordas dentro de
uma janela movel de 4 casas (mesmo limite fisico.abertura ja usado pela
regua v2.1), e filtra o resultado usando exclusivamente as regras JA
validadas e em producao no projeto:

  - harmonia:   validacao.shape_valido        (notas do acorde == TIPOS_DE_ACORDE do banco)
  - fisica:     limites fisica.abertura / fisica.alcance (tabela REGRAS_DE_VALIDACAO, auditoria.db)
  - ergonomia:  dedicacao.shape_tocavel + calcular_dedos_e_pestana (regras R1-R3 do projeto)
  - traste_alto: servidor._traste_alto - casa pressionada >= 12 e' bloqueada
    sem excecao (REGRAS_DE_REPROVACAO: corpo do instrumento impede o acesso
    da mao a partir dai; verificado na mao pelo usuario musico em 2026-08-07).
  - double_barre: servidor._tem_pestana_dupla - 2+ dedos diferentes cobrindo
    2+ cordas cada e' fisicamente impossivel (REGRAS_DE_REPROVACAO,
    confirmado pelo usuario musico em 2026-08-08).
  - dificuldade: dificuldade.avaliar_dificuldade (rubrica ISMIR 2023 ja usada no projeto)

Nenhum criterio de aprovacao/reprovacao e' inventado aqui; todos vem de
modulos ja auditados do proprio projeto. A definicao de intervalos de cada
qualidade de acorde vem do banco (TIPOS_DE_ACORDE), a mesma fonte que
regua_v21.py usa e documenta como "fonte unica de verdade".
"""
import itertools
import os
import sqlite3
from datetime import datetime, timezone

from dedicacao import calcular_dedos_e_pestana, shape_tocavel
from validacao import shape_valido
from dificuldade import avaliar_dificuldade
from servidor import _traste_alto, _tem_pestana_dupla
import regua_v21

NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
CORDAS_AFINACAO = [40, 45, 50, 55, 59, 64]  # E A D G B E, grave->agudo
DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(DIR, "auditoria.db")

# Identificador desta leva de geracao, gravado em regra_versao. Distinto de
# v2.1-dedutiva/v2.2-dedutiva (regua manual) para manter rastreabilidade de
# que este lote veio do gerador por forca bruta, nao de auditoria humana.
REGRA_VERSAO_TEORIA = "v-teoria-forca-bruta-1.0"


def gerar_shapes_por_teoria(tonica, tipo, casa_maxima=None):
    """Gera, por forca bruta e teoria musical, todos os shapes validos e
    tocaveis de `tonica`+`tipo` (ex.: "B", "m7b5").

    `tonica` deve estar em notacao sustenido (C, C#, D, ... conforme NOTAS),
    a mesma convencao usada em gerar_shapes_dinamicos - normalize bemois
    antes de chamar (ja existe essa normalizacao no projeto, em
    gerador_web_dinamico.parse_acorde / BEMOL_INVERSO).

    `casa_maxima` limita a busca (default: fisica.alcance do banco, 15).

    Retorna lista de dicts, ordenada por (casa_base, score de dificuldade):
    {"tonica", "tipo", "diagrama": [...6 valores, "X"/"0"/"N"...],
     "dedos": [...6 valores 0-4...], "pestana": {...} ou None,
     "casa_base": int, "dificuldade": {...}}
    """
    con = sqlite3.connect(DB)
    linha = con.execute(
        "SELECT intervalos FROM TIPOS_DE_ACORDE WHERE codigo=?", (tipo,)
    ).fetchone()
    limites = dict(con.execute(
        "SELECT codigo, limite_numerico FROM REGRAS_DE_VALIDACAO "
        "WHERE limite_numerico IS NOT NULL"))
    con.close()

    if linha is None:
        raise ValueError(
            f"Tipo de acorde {tipo!r} nao existe em TIPOS_DE_ACORDE (auditoria.db). "
            "Nao adivinho intervalos: cadastre o tipo no banco antes de gerar.")
    intervalos = [int(x) for x in linha[0].split(",")]

    limite_abertura = int(limites.get("fisica.abertura", 4))
    limite_alcance = int(limites.get("fisica.alcance", 15))
    # traste_alto (REGRAS_DE_REPROVACAO) bloqueia casa >= 12 sem excecao,
    # regra mais restritiva que fisica.alcance e que prevalece sobre ela.
    limite_efetivo = min(limite_alcance, 11)
    casa_maxima = limite_efetivo if casa_maxima is None else min(casa_maxima, limite_efetivo)

    tonica_idx = NOTAS.index(tonica.upper())
    notas_acorde = {(tonica_idx + i) % 12 for i in intervalos}
    # Unica tolerancia de nota ausente ja validada no projeto: a 5a justa
    # (Wikipedia "Guitar chord": "the fifth is often omitted").
    toleradas = {(tonica_idx + 7) % 12} if 7 in intervalos else set()

    vistos = set()
    resultados = []

    for base in range(1, casa_maxima - limite_abertura + 2):
        janela = [f for f in range(base, base + limite_abertura) if f <= casa_maxima]
        opcoes_por_corda = [[None, 0] + janela for _ in range(6)]

        for casas in itertools.product(*opcoes_por_corda):
            if all(c is None for c in casas):
                continue
            if casas in vistos:
                continue
            if not shape_valido(list(casas), CORDAS_AFINACAO, notas_acorde, toleradas):
                continue
            if not shape_tocavel(list(casas)):
                continue

            diagrama = ["X" if c is None else str(c) for c in casas]
            if _traste_alto(diagrama):
                continue

            dedos, pestana = calcular_dedos_e_pestana(list(casas))
            if _tem_pestana_dupla(dedos):
                continue

            vistos.add(casas)
            dif = avaliar_dificuldade(diagrama, dedos, pestana, tonica, tipo)

            pressionadas = [c for c in casas if c is not None and c > 0]
            casa_base = min(pressionadas) if pressionadas else 0

            resultados.append({
                "tonica": tonica,
                "tipo": tipo,
                "diagrama": diagrama,
                "dedos": dedos,
                "pestana": pestana,
                "casa_base": casa_base,
                "dificuldade": dif,
            })

    resultados.sort(key=lambda s: (s["casa_base"], s["dificuldade"]["score"]))
    return resultados


def gravar_shapes_validados(tonica, tipo, casa_maxima=None):
    """Gera TODOS os shapes de `tonica`+`tipo` (gerar_shapes_por_teoria) e
    grava cada um em SHAPES_APROVADOS, no mesmo formato ja usado pelos 3745
    shapes de 'valido_inversao_raro' (tambem gerados por regra, sem fonte
    externa): n_fontes_confiaveis=0, regras_validacao_atendidas=
    'harmonia_completa'. veredito_original='valido_teoria' distingue a
    origem (forca bruta) da inversao construtiva, mantendo rastreabilidade.

    span/traste_max vem de regua_v21.avaliar(), a regua ja auditada do
    projeto - nao recalculados aqui para evitar logica duplicada.

    Idempotente: UNIQUE(acorde, shape, regra_versao) na tabela ja evita
    duplicar linha se rodar de novo.

    Retorna (gerados, gravados) - total gerado e total efetivamente inserido
    (gravados pode ser menor se algumas linhas ja existiam).
    """
    shapes = gerar_shapes_por_teoria(tonica, tipo, casa_maxima=casa_maxima)
    acorde = tonica + tipo
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")

    con = sqlite3.connect(DB)
    gravados = 0
    for s in shapes:
        shape_str = ",".join(s["diagrama"])
        veredito, falhos, _notas, span, traste_max = regua_v21.avaliar(acorde, shape_str)
        if veredito not in ("valido", "valido_raro"):
            # Defesa em profundidade: se a regua discordar da harmonia (nao
            # deveria, ja checamos com validacao.shape_valido), nao grava.
            continue

        pestana = s["pestana"]
        pestana_casa = pestana["casa"] if pestana else None
        pestana_corda_min = min(pestana["cordas"]) if pestana else None
        pestana_corda_max = max(pestana["cordas"]) if pestana else None
        dif = s["dificuldade"]

        cur = con.execute(
            "INSERT OR IGNORE INTO SHAPES_APROVADOS "
            "(acorde, shape, regra_versao, span, traste_max, n_fontes_confiaveis, "
            " regras_validacao_atendidas, data, veredito_original, dedos, "
            " pestana_casa, pestana_corda_min, pestana_corda_max, "
            " dificuldade_score, dificuldade_nivel, dificuldade_rotulo, "
            " dificuldade_travada, aprovado_manual, aprovado_manual_data) "
            "VALUES (?,?,?,?,?,0,'harmonia_completa',?, 'valido_teoria', ?, "
            "?,?,?, ?,?,?, 0,0,NULL)",
            (acorde, shape_str, REGRA_VERSAO_TEORIA, span, traste_max, agora,
             ",".join(str(d) for d in s["dedos"]),
             pestana_casa, pestana_corda_min, pestana_corda_max,
             dif["score"], dif["nivel"], dif["rotulo"]))
        gravados += cur.rowcount
    con.commit()
    con.close()
    return len(shapes), gravados


if __name__ == "__main__":
    import sys
    tonica_arg = sys.argv[1] if len(sys.argv) > 1 else "B"
    tipo_arg = sys.argv[2] if len(sys.argv) > 2 else "m7b5"
    gerados, gravados = gravar_shapes_validados(tonica_arg, tipo_arg)
    print(f"{tonica_arg}{tipo_arg}: {gerados} gerados, {gravados} gravados em SHAPES_APROVADOS "
          f"(regra_versao={REGRA_VERSAO_TEORIA})")
