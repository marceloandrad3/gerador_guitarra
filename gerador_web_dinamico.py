"""
Gerador Dinâmico de Acordes - Backend
Regra de ordenação (padrão Cifra Club / JustinGuitar / CAGED):
1º Shape aberto canônico (se existir no catálogo)
2º Shapes abertos gerados (casa 0, sem pestana)
3º Pestana mais baixa
4º Demais por casa crescente
Empate: menor soma de casas

PREMISSA FUNDAMENTAL - DEDICAÇÃO DE ACORDES (NUNCA VIOLAR):
==========================================================
1. Cada dedo (1,2,3,4) pode pressionar NO MÁXIMO uma corda, EXCETO quando
   forma uma pestana (mini ou full) em cordas ADJACENTES na mesma casa.
2. Cordas NÃO ADJACENTES na mesma casa PRECISAM de dedos DIFERENTES.
3. Pestana (dedo 1) cobre da primeira à última corda tocada (full barre),
   não apenas as cordas que estão exatamente na casa da pestana.
4. Shapes canônicos hardcoded também devem respeitar estas regras.
==========================================================
"""

DEDILHADOS_CANONICOS = {
    "C":  {"diagrama": ["X","3","2","0","1","0"], "dedos": [0,3,2,0,1,0], "pestana": None},
    "D":  {"diagrama": ["X","X","0","2","3","2"], "dedos": [0,0,0,2,3,1], "pestana": None},
    "E":  {"diagrama": ["0","2","2","1","0","0"], "dedos": [0,2,3,1,0,0], "pestana": None},
    "F":  {"diagrama": ["1","3","3","2","1","1"], "dedos": [1,3,4,2,1,1], "pestana": {"casa":1,"cordas":[0,1,2,3,4,5]}},
    "G":  {"diagrama": ["3","2","0","0","0","3"], "dedos": [3,2,0,0,0,4], "pestana": None},
    "A":  {"diagrama": ["X","0","2","2","2","0"], "dedos": [0,0,1,2,3,0], "pestana": None},
    "B":  {"diagrama": ["X","2","4","4","4","2"], "dedos": [0,1,2,3,4,1], "pestana": {"casa":2,"cordas":[1,2,3,4,5]}},
    "Am": {"diagrama": ["X","0","2","2","1","0"], "dedos": [0,0,2,3,1,0], "pestana": None},
    "Em": {"diagrama": ["0","2","2","0","0","0"], "dedos": [0,2,3,0,0,0], "pestana": None},
    "Dm": {"diagrama": ["X","X","0","2","3","1"], "dedos": [0,0,0,2,3,1], "pestana": None},
    "B7": {"diagrama": ["X","2","1","2","0","2"], "dedos": [0,2,1,3,0,4], "pestana": None},
    "C7": {"diagrama": ["X","3","2","3","1","0"], "dedos": [0,3,2,4,1,0], "pestana": None},
    "C7M":{"diagrama": ["X","3","2","0","0","0"], "dedos": [0,3,2,0,0,0], "pestana": None},
    "C9": {"diagrama": ["X","3","2","3","3","X"], "dedos": [0,2,1,3,4,0], "pestana": None},
    "F#": {"diagrama": ["2","4","4","3","2","2"], "dedos": [1,3,4,2,1,1], "pestana": {"casa":2,"cordas":[0,1,2,3,4,5]}},
    "G#": {"diagrama": ["4","6","6","5","4","4"], "dedos": [1,3,4,2,1,1], "pestana": {"casa":4,"cordas":[0,1,2,3,4,5]}},
    "Bb": {"diagrama": ["X","1","3","3","3","1"], "dedos": [0,1,2,3,4,1], "pestana": {"casa":1,"cordas":[1,2,3,4,5]}},
    # --- Inversoes canonicas (fonte: Wikipedia "Guitar chord" / "Slash chord") ---
    "C/G":  {"diagrama": ["3","3","2","0","1","0"], "dedos": [3,3,2,0,1,0], "pestana": None},
    "C/E":  {"diagrama": ["0","3","2","0","1","0"], "dedos": [0,3,2,0,1,0], "pestana": None},
    "G/D":  {"diagrama": ["X","X","0","0","0","3"], "dedos": [0,0,0,0,0,3], "pestana": None},
    "Am/E": {"diagrama": ["0","0","2","2","1","0"], "dedos": [0,0,2,3,1,0], "pestana": None},
    "D/F#": {"diagrama": ["2","X","0","2","3","2"], "dedos": [1,0,0,2,3,4], "pestana": None},
    "Em/G": {"diagrama": ["3","2","2","0","0","0"], "dedos": [3,1,2,0,0,0], "pestana": None},
}

NOTAS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
CORDAS_AFINACAO = [40,45,50,55,59,64]

from dedicacao import calcular_dedos_e_pestana, shape_tocavel
from validacao import shape_valido, diagrama_valido
from dificuldade import avaliar_dificuldade

def parse_acorde(nome):
    nome = nome.strip()
    if len(nome) >= 2 and nome[1] in ['#','b']:
        tonica = nome[:2]
        tipo = nome[2:] if len(nome)>2 else ""
    else:
        tonica = nome[:1]
        tipo = nome[1:] if len(nome)>1 else ""
    bemol_map = {"Db":"C#","Eb":"D#","Gb":"F#","Ab":"G#","Bb":"A#"}
    tonica = bemol_map.get(tonica, tonica)
    return tonica, tipo

def parsear_inversao(nome_acorde):
    """Separa acorde e nota do baixo em acordes tipo C/G."""
    if '/' in nome_acorde:
        partes = nome_acorde.split('/')
        if len(partes) == 2 and len(partes[1]) <= 2:
            return partes[0], partes[1].strip()
    return nome_acorde, None

def filtrar_por_baixo(shapes, nota_baixo_str):
    """Filtra shapes onde a corda mais grave tocada e a nota do baixo."""
    if not nota_baixo_str or not shapes:
        return shapes
    try:
        idx_baixo = NOTAS.index(nota_baixo_str.upper())
    except ValueError:
        return []
    resultados = []
    for s in shapes:
        diag = s['diagrama']
        nota_mais_grave_idx = None
        for i, val in enumerate(diag):
            if str(val) not in ('X', 'x', '-1'):
                nota_real = (CORDAS_AFINACAO[i] + int(val)) % 12
                nota_mais_grave_idx = nota_real
                break
        if nota_mais_grave_idx is not None and nota_mais_grave_idx == idx_baixo:
            resultados.append(s)
    return resultados

def normalizar_tipo(tipo):
    """Notacoes equivalentes da nona de dominante: 7(9) = 7/9 = 9."""
    return "9" if tipo in ("7(9)", "7/9", "9") else tipo

BEMOL_INVERSO = {"C#":"Db","D#":"Eb","F#":"Gb","G#":"Ab","A#":"Bb"}

def nome_para_catalogo(tonica, tipo):
    """Retorna o nome correto para busca no catalogo (trata Bb vs A#)."""
    nome = tonica + tipo
    if nome in DEDILHADOS_CANONICOS:
        return nome
    alt = BEMOL_INVERSO.get(tonica, tonica) + tipo
    if alt in DEDILHADOS_CANONICOS:
        return alt
    return nome


def get_intervalos(tipo):
    tipos = {
        "":       [0,4,7],
        "m":      [0,3,7],
        "7":      [0,4,7,10],
        "m7":     [0,3,7,10],
        "7M":     [0,4,7,11],
        "m7M":    [0,3,7,11],
        "dim":    [0,3,6],
        "dim7":   [0,3,6,9],
        "aug":    [0,4,8],
        "sus2":   [0,2,7],
        "sus4":   [0,5,7],
        "6":      [0,4,7,9],
        "m6":     [0,3,7,9],
        "9":      [0,4,7,10,14],
        "add9":   [0,4,7,14],
    }
    return tipos.get(tipo)


CAGED_MAIOR = {
    "E": {"raiz_corda": 0, "offsets": [0, 2, 2, 1, 0, 0]},
    "A": {"raiz_corda": 1, "offsets": [None, 0, 2, 2, 2, 0]},
    "D": {"raiz_corda": 2, "offsets": [None, None, 0, 2, 3, 2]},
    "C": {"raiz_corda": 1, "offsets": [None, 0, -1, -3, -2, -3]},
    "G": {"raiz_corda": 0, "offsets": [0, -1, -3, -3, -3, 0]},
}

CAGED_MENOR = {
    "Em": {"raiz_corda": 0, "offsets": [0, 2, 2, 0, 0, 0]},
    "Am": {"raiz_corda": 1, "offsets": [None, 0, 2, 2, 1, 0]},
    "Dm": {"raiz_corda": 2, "offsets": [None, None, 0, 2, 3, 1]},
    "Cm": {"raiz_corda": 1, "offsets": [None, 0, -2, -3, -2, 0]},   # Cm X31013 (C-shape menor: 3a rebaixada, forma padrao de dicionario)
    "Gm": {"raiz_corda": 0, "offsets": [0, -2, -3, -3, 0, 0]},      # Gm 310033 (G-shape menor: 3a rebaixada p/ Bb na 5a corda)
}

# Templates por qualidade - offsets derivados das casas confirmadas na
# Wikipedia "Guitar chord" (acorde-fonte citado em cada linha).
CAGED_DOMINANTE7 = {
    "E7": {"raiz_corda": 0, "offsets": [0, 2, 0, 1, 0, 0]},          # E7  020100
    "A7": {"raiz_corda": 1, "offsets": [None, 0, 2, 0, 2, 0]},       # A7  X02020
    "D7": {"raiz_corda": 2, "offsets": [None, None, 0, 2, 1, 2]},    # D7  XX0212
    "G7": {"raiz_corda": 0, "offsets": [0, -1, -3, -3, -3, -2]},     # G7  320001
    "C7": {"raiz_corda": 1, "offsets": [None, 0, -1, 0, -2, -3]},    # C7  X32310     # G7  320001
}

CAGED_DOMINANTE9 = {
    "C9": {"raiz_corda": 1, "offsets": [None, 0, -1, 0, 0, None]},  # C9 X3233X (Cifra Club / Wikipedia Cm9 X3133X c/ 3a maior)
    "E9": {"raiz_corda": 0, "offsets": [0, 2, 0, 1, 0, 2]},          # E9 020102 (Wikipedia Gm9 353335 c/ 3a maior = G9 353435)
}

CAGED_MAIOR7 = {
    "C7M": {"raiz_corda": 1, "offsets": [None, 0, -1, -3, -3, -3]},  # Cmaj7 X32000
    "D7M": {"raiz_corda": 2, "offsets": [None, None, 0, 2, 2, 2]},   # Dmaj7 XX0222
    "E7M": {"raiz_corda": 0, "offsets": [0, 2, 1, 1, 0, 0]},         # Emaj7 021100
    "G7M": {"raiz_corda": 0, "offsets": [0, -1, -3, -3, -3, -1]},    # Gmaj7 320002
    "A7M": {"raiz_corda": 1, "offsets": [None, 0, 2, 1, 2, 0]},      # Amaj7 X02120
    "E7Mc": {"raiz_corda": 0, "offsets": [0, None, 1, 1, 0, None]},   # Gmaj7 3X443X (Cifra Club: E-shape recortado, sem notas dobradas)
}

CAGED_MENOR7 = {
    "Em7": {"raiz_corda": 0, "offsets": [0, 2, 0, 0, 0, 0]},         # Em7  020000
    "Am7": {"raiz_corda": 1, "offsets": [None, 0, 2, 0, 1, 0]},      # Am7  X02010
    "Dm7": {"raiz_corda": 2, "offsets": [None, None, 0, 2, 1, 1]},   # Dm7  XX0211
    "Bm7": {"raiz_corda": 1, "offsets": [None, 0, -2, 0, -2, 0]},    # Bm7  X20202
    "F#m7": {"raiz_corda": 0, "offsets": [0, -2, 0, 0, 0, -2]},      # F#m7 202220
}




def toleradas_faltando(tonica_idx, intervalos):
    """Classes de altura cuja ausencia e tolerada no shape.

    Unica tolerancia: a 5a justa (intervalo 7), pratica convencional do
    violao (Wikipedia "Guitar chord": "the fifth is often omitted").
    Acordes sem 5a justa (dim/aug) nao recebem tolerancia alguma.
    """
    return {(tonica_idx + 7) % 12} if 7 in intervalos else set()


def gerar_shapes_dinamicos(tonica, tipo):
    """Gera os 5 shapes CAGED usando templates verificados com calculo de dedos."""
    tonica_idx = NOTAS.index(tonica)
    intervalos = get_intervalos(tipo)
    if intervalos is None:
        return []
    notas_acorde = set((tonica_idx + i) % 12 for i in intervalos)
    toleradas = toleradas_faltando(tonica_idx, intervalos)

    if tipo in ("m", "menor"):
        templates = CAGED_MENOR
        ordem = ["Em", "Am", "Dm", "Cm", "Gm"]
    elif tipo == "7":
        templates = CAGED_DOMINANTE7
        ordem = ["E7", "A7", "D7", "C7", "G7"]
    elif tipo == "9":
        templates = CAGED_DOMINANTE9
        ordem = ["C9", "E9"]
    elif tipo == "7M":
        templates = CAGED_MAIOR7
        ordem = ["C7M", "D7M", "E7M", "E7Mc", "G7M", "A7M"]
    elif tipo == "m7":
        templates = CAGED_MENOR7
        ordem = ["Em7", "Am7", "Dm7", "Bm7", "F#m7"]
    else:
        templates = CAGED_MAIOR
        ordem = ["E", "A", "D", "C", "G"]

    shapes = []
    for nome_shape in ordem:
        tmpl = templates[nome_shape]
        raiz_corda = tmpl["raiz_corda"]
        offsets = tmpl["offsets"]
        afinacao_raiz = CORDAS_AFINACAO[raiz_corda]

        encontrado = False
        for casa_tonica in range(0, 16):
            nota_na_casa = (afinacao_raiz + casa_tonica) % 12
            if nota_na_casa != tonica_idx:
                continue

            casas = []
            valido = True
            for corda_idx in range(6):
                off = offsets[corda_idx]
                if off is None:
                    casas.append(None)
                else:
                    c = casa_tonica + off
                    if c < 0 or c > 15:
                        valido = False
                        break
                    casas.append(c)

            if not valido:
                continue

            if not shape_valido(casas, CORDAS_AFINACAO, notas_acorde, toleradas):
                continue

            if not shape_tocavel(casas):
                continue

            dedos, pestana = calcular_dedos_e_pestana(casas)

            casas_str = ["X" if c is None else str(c) for c in casas]
            dif = avaliar_dificuldade(casas_str, dedos, pestana, tonica, tipo)
            diagrama = casas_str

            casas_tocadas = [c for c in casas if c is not None and c > 0]
            casa_ref = min(casas_tocadas) if casas_tocadas else 0
            score = casa_ref + (10 if pestana else 0)
            eh_aberto = (casa_ref == 0 and not pestana)

            shapes.append({
                "nome": f"{nome_shape} Shape",
                "casas": casas_str,
                "dedos": dedos,
                "pestana": pestana,
                "diagrama": diagrama,
                "score": score,
                "dificuldade": dif,
                "_casa_base": casa_ref,
                "_eh_aberto": eh_aberto
            })

            encontrado = True
            break

    return shapes


def ordenar_shapes(shapes, tonica, tipo):
    nome_completo = nome_para_catalogo(tonica, tipo)
    canonico = DEDILHADOS_CANONICOS.get(nome_completo)
    def chave_ordenacao(s):
        eh_aberto = s.get("_eh_aberto", False) or (s["_casa_base"] == 0 and s["pestana"] is None)
        casa = s["_casa_base"]
        score = s["score"]
        if canonico and s["diagrama"] == canonico["diagrama"]:
            return (0, 0, 0)
        if eh_aberto:
            return (1, 0, score)
        return (2, casa, score)
    return sorted(shapes, key=chave_ordenacao)

# Teto de exibicao de slash chords: o gerador construtivo cobre a grade
# inteira; o UI mostra os N melhores (canonico sempre incluido no teto).
MAX_DIAGRAMAS_SLASH = 8


def gerar_slash_construtivo(tonica, tipo, nota_baixo_str):
    """Gerador construtivo de slash chords: regra global, sem hardcode por acorde.
    Fontes: Wikipedia 'Slash chord'/'Inversion (music)' (baixo = nota mais grave;
    1a inversao = 3a no baixo, 2a = 5a) e anatomia da mao (janela de 5 trastes,
    mesmo alcance usado no projeto). Para cada uma das 4 cordas mais graves,
    posiciona o baixo em cada casa viavel e preenche as cordas seguintes apenas
    com notas do acorde (ou mutadas), aplicando os mesmos portoes do ramo
    normal: diagrama_valido (sem notas erradas/faltando), >= 4 notas, vao <= 4,
    shape_tocavel e dedicao via calcular_dedos_e_pestana."""
    try:
        idx_baixo = NOTAS.index(nota_baixo_str.upper())
    except ValueError:
        return []
    tonica_idx = NOTAS.index(tonica)
    intervalos = get_intervalos(tipo)
    notas_acorde = set((tonica_idx + i) % 12 for i in intervalos)
    if idx_baixo not in notas_acorde:
        return []
    toleradas = toleradas_faltando(tonica_idx, intervalos)
    resultados = []
    vistos = set()

    def registrar(diag):
        diag = _reduzir_voicing_quatro_dedos(diag)
        chave = tuple(diag)
        if chave in vistos:
            return
        casas = [int(v) for v in diag if v != 'X']
        if len(casas) < 4 or max(casas) - min(casas) > 4:
            return
        if not diagrama_valido(list(diag), CORDAS_AFINACAO, notas_acorde, toleradas):
            return
        conv = [None if v == 'X' else int(v) for v in diag]
        dedos, pestana = calcular_dedos_e_pestana(conv)
        if dedos and shape_tocavel(conv):
            vistos.add(chave)
            resultados.append({'nome': tonica + tipo + '/' + nota_baixo_str,
                               'diagrama': list(diag),
                               'dedos': dedos, 'pestana': pestana})

    def preencher(diag, corda, lo, hi):
        if corda == 6:
            registrar(diag)
            return
        diag[corda] = 'X'  # opcao: mutar esta corda
        preencher(diag, corda + 1, lo, hi)
        for casa in range(max(0, lo), min(hi, 14) + 1):  # opcao: tocar na janela
            if (CORDAS_AFINACAO[corda] + casa) % 12 in notas_acorde:
                diag[corda] = str(casa)
                preencher(diag, corda + 1, lo, hi)
        diag[corda] = 'X'

    for corda_baixo in range(4):
        for casa_baixo in range(15):
            if (CORDAS_AFINACAO[corda_baixo] + casa_baixo) % 12 != idx_baixo:
                continue
            diag = ['X'] * 6
            diag[corda_baixo] = str(casa_baixo)
            preencher(diag, corda_baixo + 1, casa_baixo - 4, casa_baixo + 4)

    # Poda de dominancia: shape cujas cordas tocadas sao subconjunto estrito
    # de outro (mesmas casas) nao agrega informacao - o musico pode mutar
    # por conta propria. Excecao: o subconjunto sobrevive quando e
    # estritamente mais facil (sem pestana vs. com pestana, ou menos
    # posicoes de dedo) - ex.: x6x477 (estilo Cifra Club) vs. x64477.
    def tocadas(d):
        return {i: v for i, v in enumerate(d) if v != 'X'}

    def custo(d):
        conv = [None if v == 'X' else int(v) for v in d]
        dedos, pestana = calcular_dedos_e_pestana(conv)
        return (1 if pestana else 0, len(set(dedos) - {0}))

    finais = []
    for a in resultados:
        ta = tocadas(a['diagrama'])
        ca = custo(a['diagrama'])
        dominado = any(
            a is not b
            and set(ta) < set(tb := tocadas(b['diagrama']))
            and all(ta[i] == tb[i] for i in ta)
            and custo(b['diagrama']) <= ca
            for b in resultados
        )
        if not dominado:
            finais.append(a)
    return finais


def gerar_dinamico(nome_acorde):
    acorde_base, nota_baixo = parsear_inversao(nome_acorde)
    # jguitar.com: se o baixo = tonica, a notacao slash e redundante:
    # trata como o acorde normal (Em/E -> Em), sem caminho de slash.
    if nota_baixo:
        _tonica_chk, _ = parse_acorde(acorde_base)
        if nota_baixo.upper() == _tonica_chk.upper():
            nota_baixo = None
            nome_acorde = acorde_base
    
    if nota_baixo:
        tonica, tipo = parse_acorde(acorde_base)
        tipo = normalizar_tipo(tipo)
        intervalos = get_intervalos(tipo)
        if intervalos is None:
            return {"acorde": nome_acorde, "tonica": tonica, "tipo": tipo,
                    "diagramas": [], "total_diagramas": 0}
        diagramas_finais = []
        # 1. Catalogo canonico primeiro (se existir)
        diag_canonico = None
        if nome_acorde in DEDILHADOS_CANONICOS:
            c = DEDILHADOS_CANONICOS[nome_acorde]
            dif = avaliar_dificuldade(c["diagrama"], c["dedos"], c.get("pestana"), tonica, tipo)
            diagramas_finais.append({
                "nome": nome_acorde,
                "diagrama": c["diagrama"],
                "dedos": c["dedos"],
                "pestana": c.get("pestana"),
                "score": dif["score"],
                "dificuldade": dif
            })
            diag_canonico = [str(x).upper() for x in c["diagrama"]]
        # 2. Voicings construtivos como complementares (sem duplicar o canonico)
        shapes_filtrados = gerar_slash_construtivo(tonica, tipo, nota_baixo)
        for s in shapes_filtrados:
            if diag_canonico and [str(x).upper() for x in s['diagrama']] == diag_canonico:
                continue
            dif = avaliar_dificuldade(s['diagrama'], s['dedos'], s.get('pestana'), tonica, tipo)
            diagramas_finais.append({**s, "score": dif['score'], "dificuldade": dif})
        # 3. Ordenar adaptativos pela MESMA regra do ramo normal
        #    (ordenar_shapes = fonte unica; canonico fixo em 1o lugar)
        for s in diagramas_finais:
            if "_casa_base" not in s:
                casas = [int(v) for v in s["diagrama"] if str(v) not in ("X", "x", "-1")]
                s["_casa_base"] = min(casas) if casas else 0
                s["_eh_aberto"] = any(str(v) == "0" for v in s["diagrama"])
        inicio = 1 if diag_canonico else 0
        diagramas_finais[inicio:] = ordenar_shapes(diagramas_finais[inicio:], tonica, tipo)
        diagramas_finais = diagramas_finais[:MAX_DIAGRAMAS_SLASH]
        for s in diagramas_finais:
            s.pop("_casa_base", None)
            s.pop("_eh_aberto", None)
        return {
            "acorde": nome_acorde,
            "tonica": tonica,
            "tipo": f"{tipo}/{nota_baixo}",
            "diagramas": diagramas_finais,
            "total_diagramas": len(diagramas_finais)
        }

    tonica, tipo = parse_acorde(nome_acorde)
    tipo = normalizar_tipo(tipo)
    intervalos = get_intervalos(tipo)
    if intervalos is None:
        return {"acorde": nome_acorde, "tonica": tonica, "tipo": tipo,
                "diagramas": [], "total_diagramas": 0}
    tonica_idx = NOTAS.index(tonica)
    notas_acorde = set((tonica_idx + i) % 12 for i in intervalos)
    toleradas = toleradas_faltando(tonica_idx, intervalos)
    shapes = gerar_shapes_dinamicos(tonica, tipo)
    # Portao unico de confiabilidade: todo shape, de qualquer origem,
    # so chega ao usuario sem notas erradas e sem notas faltando
    # (ausencia tolerada apenas para a 5a justa, pratica do violao).
    shapes = [s for s in shapes if diagrama_valido(s["diagrama"], CORDAS_AFINACAO, notas_acorde, toleradas)]
    shapes = ordenar_shapes(shapes, tonica, tipo)
    for s in shapes:
        s.pop("_casa_base", None)
        s.pop("_eh_aberto", None)
    nome_completo = nome_para_catalogo(tonica, tipo)
    if nome_completo in DEDILHADOS_CANONICOS and diagrama_valido(DEDILHADOS_CANONICOS[nome_completo]["diagrama"], CORDAS_AFINACAO, notas_acorde, toleradas):
        c = DEDILHADOS_CANONICOS[nome_completo]
        canonico_shape = {
            "nome_exato": nome_completo,
            "diagrama": c["diagrama"],
            "dedos": c["dedos"],
            "pestana": c["pestana"],
            "score": 0,
            "dificuldade": avaliar_dificuldade(c["diagrama"], c["dedos"], c["pestana"], tonica, tipo)
        }
        ja_existe = any(s["diagrama"] == c["diagrama"] for s in shapes)
        if not ja_existe:
            shapes.insert(0, canonico_shape)
        else:
            shapes = [s for s in shapes if s["diagrama"] != c["diagrama"]]
            shapes.insert(0, canonico_shape)
    return {
        "acorde": nome_acorde,
        "tonica": tonica,
        "tipo": tipo,
        "diagramas": shapes,
        "total_diagramas": len(shapes)
    }

if __name__ == "__main__":
    for teste in ["A", "D", "G", "F#", "B7", "C", "Am", "B"]:
        r = gerar_dinamico(teste)
        p = r["diagramas"][0] if r["diagramas"] else {}
        print(f"{teste}: {p.get('diagrama')} | dedos={p.get('dedos')} | pestana={p.get('pestana')} | total={r['total_diagramas']}")
def _reduzir_voicing_quatro_dedos(diag):
    """Omite notas dobradas ate o shape caber em 4 dedos separados.

    Fontes: Wikipedia 'Voicing (music)' (dobramentos sao opcionais),
    Greg Howlett 'Voicing 101' (evitar dobramento sem motivo) e
    pratica Cifra Club (B/D# = X6X477). Nunca omite a corda do baixo
    nem a unica ocorrencia de uma nota do acorde.
    """
    from collections import Counter
    tocadas = [c for c in range(6) if str(diag[c]) not in ("X", "x", "-1")]
    fretadas = [c for c in tocadas if int(diag[c]) > 0]
    if len(fretadas) <= 4:
        return list(diag)
    casas = {c: int(diag[c]) for c in tocadas}
    notas = {c: (CORDAS_AFINACAO[c] + casas[c]) % 12 for c in tocadas}
    contagem = Counter(notas.values())
    baixo = min(tocadas)
    mesma_casa = Counter(casas[c] for c in fretadas)
    candidatas = sorted(
        (c for c in fretadas if c != baixo and contagem[notas[c]] > 1),
        key=lambda c: (0 if mesma_casa[casas[c]] > 1 else 1, c))
    novo = list(diag)
    restantes = len(fretadas)
    for c in candidatas:
        if restantes <= 4:
            break
        if contagem[notas[c]] <= 1:
            continue
        novo[c] = "X"
        contagem[notas[c]] -= 1
        restantes -= 1
    return novo
