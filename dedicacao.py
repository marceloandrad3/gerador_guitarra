"""
Modulo de dedicacao de acordes de guitarra.

Regras (premissa fundamental do projeto):
1. Cada dedo (1-4) pressiona no maximo uma corda, exceto pestana.
2. Pestana (dedo 1): full barre da primeira a ultima corda pressionada
   na menor casa (so quando fisica: vao completo).
3. Mini-pestana (cordas adjacentes na mesma casa compartilhando dedo)
   apenas em ULTIMO CASO, quando dedos separados nao cabem em 4 posicoes.
4. Cordas NAO adjacentes na mesma casa precisam de dedos diferentes.
5. Tocabilidade: no maximo 4 posicoes de dedo (pestana conta 1, cada
   grupo de mini-pestana conta 1). Shapes acima disso sao impossiveis
   e o gerador deve descarta-los.

Politica de estilo (fundamentada na Wikipedia 'Barre chord', que
documenta tanto 'one finger frets each string' quanto o barre; e no
Cifra Club, que usa dedos separados quando cabem):
R1. <= 4 cordas pressionadas -> dedos separados, sem pestana.
R2. > 4 cordas -> pestana do dedo 1 (vao completo) + restantes
    separados, se couber em 4 posicoes.
R3. Senao -> mini-pestana em adjacentes (ultimo recurso).
Atribuicao dos dedos: casa crescente, desempate pela corda mais grave.
"""


def _grupos_separados(tocadas):
    """Um grupo por corda, ordenado por (casa crescente, corda grave)."""
    return [(c, [i]) for i, c in sorted(tocadas, key=lambda t: (t[1], t[0]))]


def _grupos_minimo(casas, tocadas):
    """Pestana + mini-pestana em adjacentes (ultimo recurso, R3)."""
    min_casa = min(c for _, c in tocadas)
    cordas_min = sorted(i for i, c in tocadas if c == min_casa)
    primeira, ultima = cordas_min[0], cordas_min[-1]
    vao_completo = all(
        casas[i] is not None and casas[i] > 0
        for i in range(primeira, ultima + 1))

    pestana = None
    if len(cordas_min) >= 2 and vao_completo:
        pestana = {"casa": min_casa,
                   "cordas": list(range(primeira, ultima + 1))}
        resto = [(i, c) for i, c in tocadas if c != min_casa]
    else:
        resto = tocadas

    grupos = []
    for casa_val in sorted({c for _, c in resto}):
        cordas = sorted(i for i, c in resto if c == casa_val)
        grupo = [cordas[0]]
        for i in cordas[1:]:
            if i == grupo[-1] + 1:
                grupo.append(i)
            else:
                grupos.append((casa_val, grupo))
                grupo = [i]
        grupos.append((casa_val, grupo))
    return pestana, grupos


def _esticar_pestana_ate_corda_fina(cordas_pestana, casas):
    """Regra ergonomica (validada pelo usuario, musico, em 2026-08-07):
    na vida real o dedo 1 (pestana) naturalmente cobre tambem as cordas
    mais finas vizinhas quando isso NAO muda o som, porque segurar so
    as cordas exatas do acorde e' mais dificil e desconfortavel. Isso
    vale quando a corda vizinha:
      - esta muda (X) -> nao soa de qualquer jeito, ou
      - ja esta pressionada por outro dedo em outra casa -> quem decide
        o som dessa corda e' o dedo mais proximo do corpo do violao,
        nao o dedo 1 por baixo.
    So' PARA quando encontra uma corda solta TOCADA (casa 0), porque
    aí a pestana abafaria uma nota que precisa soar aberta.
    Nunca estica para o lado da corda mais grossa (regra do usuario)."""
    cordas = list(cordas_pestana)
    proxima = max(cordas) + 1
    while proxima <= 5:
        if casas[proxima] == 0:
            break
        cordas.append(proxima)
        proxima += 1
    return cordas


def _grupos_de_dedo(casas):
    """Fonte unica de verdade da dedicacao (R1-R3).

    Retorna (pestana, grupos): `pestana` e o dict da regra 2 (ou None) e
    `grupos` e a lista de (casa, [cordas]) onde cada grupo exige um dedo.
    """
    tocadas = [(i, c) for i, c in enumerate(casas) if c is not None and c > 0]
    if not tocadas:
        return None, []

    # R1: dedos separados cabem -> sem pestana.
    if len(tocadas) <= 4:
        return None, _grupos_separados(tocadas)

    min_casa = min(c for _, c in tocadas)
    cordas_min = sorted(i for i, c in tocadas if c == min_casa)
    primeira, ultima = cordas_min[0], cordas_min[-1]
    vao_completo = all(
        casas[i] is not None and casas[i] > 0
        for i in range(primeira, ultima + 1))
    resto = [(i, c) for i, c in tocadas if c != min_casa]

    # R2: pestana + restantes separados, se couber em 4 posicoes.
    if len(cordas_min) >= 2 and vao_completo and 1 + len(resto) <= 4:
        cordas_pestana = _esticar_pestana_ate_corda_fina(
            list(range(primeira, ultima + 1)), casas)
        return ({"casa": min_casa, "cordas": cordas_pestana},
                _grupos_separados(resto))

    # R3: ultimo recurso.
    return _grupos_minimo(casas, tocadas)


def shape_tocavel(casas):
    """True se o shape cabe em 4 dedos (regra 5)."""
    pestana, grupos = _grupos_de_dedo(casas)
    return (1 if pestana else 0) + len(grupos) <= 4


def calcular_dedos_e_pestana(casas):
    """Calcula dedos (1-4) e pestana; corda nao tocada recebe 0."""
    pestana, grupos = _grupos_de_dedo(casas)
    dedos = [0] * 6
    if pestana is not None:
        for i in pestana["cordas"]:
            if casas[i] == pestana["casa"]:
                dedos[i] = 1
    dedo_atual = 2 if pestana else 1
    for _casa, grupo in sorted(grupos, key=lambda g: (g[0], g[1][0])):
        if dedo_atual > 4:
            break
        for i in grupo:
            dedos[i] = dedo_atual
        dedo_atual += 1
    return dedos, pestana
