"""
Modulo de avaliacao de dificuldade de acordes de guitarra.

Rubrica ISMIR 2023 (Vasquez, Baelemans, Driedger, Zuidema & Burgoyne,
"Quantifying the Ease of Playing Song Chords on the Guitar", Univ. de
Amsterda / Chordify). Pesos oficiais: UC=3, CFP=3, CFD=2, RHC=2.
Cada criterio recebe nivel 0-3. Score maximo = 30.

Operacionalizacao dos criterios (consenso JustinGuitar / Cifra Club):
  UC  - raridade da tonica/tipo (tonica+tipo comuns = 0; tipo raro = 3)
  CFP - pestana 5-6 cordas = 3; 3-4 cordas = 2; 2 cordas = 1;
        acorde aberto confortavel = 0; spread>=4 ou casa>=10 soma +1
  CFD - 4 dedos ou pestana cheia = 3 (ISMIR "very difficult");
        3 dedos = 1; pestana 3-4 cordas = 2; pestana 2 cordas = 1
  RHC - X entre cordas tocadas (mute interno) = 2 ou 3;
        X so nas bordas = 1; sem X = 0

Faixas: 0-1 Muito Facil | 2-6 Facil | 7-11 Medio | 12-20 Dificil | 21+ Muito Dificil
"""

TONICAS_COMUNS = {"C", "D", "E", "F", "G", "A", "B"}
TIPOS_COMUNS = {"", "m", "7", "m7"}
TIPOS_RAROS = {"dim", "dim7", "aug", "9", "m7M"}

NIVEIS = [
    (1, 1, "Muito Facil"),
    (6, 2, "Facil"),
    (11, 3, "Medio"),
    (20, 4, "Dificil"),
    (30, 5, "Muito Dificil"),
]


def _parse(diagrama):
    casas = []
    for v in diagrama:
        try:
            c = int(v)
        except (TypeError, ValueError):
            c = None
        casas.append(c if c is not None and c >= 0 else None)
    return casas


def _nivel_uc(tonica, tipo):
    """UC (peso 3): raridade do acorde."""
    if tipo in TIPOS_RAROS:
        return 3
    t_comum = tonica in TONICAS_COMUNS
    p_comum = tipo in TIPOS_COMUNS
    if t_comum and p_comum:
        return 0
    if t_comum or p_comum:
        return 1
    return 2


def _nivel_cfp(casas, pestana):
    """CFP (peso 3): conforto do posicionamento.

    Pestana domina: 5-6 cordas = 3, 3-4 = 2, 2 = 1.
    Aberto confortavel (corda solta + casas <= 4) = 0.
    Spread >= 4 ou casa >= 10 soma +1 (teto 3).
    """
    pressionadas = [c for c in casas if c is not None and c > 0]
    if not pressionadas:
        return 0
    casa_min = min(pressionadas)
    spread = max(pressionadas) - casa_min
    tem_solta = any(c == 0 for c in casas if c is not None)

    if pestana:
        n = len(pestana.get("cordas", []))
        nivel = 3 if n >= 5 else (2 if n >= 3 else 1)
    else:
        eh_aberto = tem_solta and casa_min <= 4
        nivel = 0 if eh_aberto else 1

    if spread >= 4:
        nivel += 1
    if casa_min >= 10:
        nivel += 1
    return min(nivel, 3)


def _nivel_cfd(dedos, pestana):
    """CFD (peso 2): dificuldade de digitacao.

    Sem pestana: <=2 dedos = 0, 3 dedos = 1, 4 dedos = 3
    (ISMIR: "four-finger chords" = very difficult).
    Com pestana: 5-6 cordas = 3, 3-4 = 2, 2 = 1
    (ISMIR: pestana curta tipo A/E = easy).
    """
    if pestana:
        n = len(pestana.get("cordas", []))
        return 3 if n >= 5 else (2 if n >= 3 else 1)
    n = len({d for d in dedos if d > 0})
    if n <= 2:
        return 0
    if n == 3:
        return 1
    return 3


def _nivel_rhc(diagrama):
    """RHC (peso 2): cordas abafadas.

    X entre cordas tocadas = mute interno (dificil).
    X so fora do intervalo tocado = mute de borda (facil).
    """
    tocadas = [i for i, v in enumerate(diagrama) if str(v) != "X"]
    x_pos = [i for i, v in enumerate(diagrama) if str(v) == "X"]
    if not x_pos:
        return 0
    if not tocadas:
        return 3
    primeira, ultima = min(tocadas), max(tocadas)
    internas = [i for i in x_pos if primeira < i < ultima]
    if not internas:
        return 1
    if len(internas) == 1:
        return 2
    return 3


def avaliar_dificuldade(diagrama, dedos=None, pestana=None,
                        tonica=None, tipo=None):
    """Avalia dificuldade pela rubrica ISMIR 2023. Score 0-30, nivel 1-5."""
    casas = _parse(diagrama)
    pressionadas = [c for c in casas if c is not None and c > 0]
    if not pressionadas:
        return {"score": 0, "nivel": 1, "rotulo": "Muito Facil",
                "detalhes": {"UC": 0, "CFP": 0, "CFD": 0, "RHC": 0}}

    uc  = _nivel_uc(tonica or "C", tipo or "")
    cfp = _nivel_cfp(casas, pestana)
    cfd = _nivel_cfd(dedos or [0] * 6, pestana)
    rhc = _nivel_rhc(diagrama)

    score = uc * 3 + cfp * 3 + cfd * 2 + rhc * 2

    nivel, rotulo = 5, "Muito Dificil"
    for max_s, n, r in NIVEIS:
        if score <= max_s:
            nivel, rotulo = n, r
            break

    return {"score": score, "nivel": nivel, "rotulo": rotulo,
            "detalhes": {"UC": uc, "CFP": cfp, "CFD": cfd, "RHC": rhc}}
