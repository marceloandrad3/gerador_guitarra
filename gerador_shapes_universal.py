"""
Motor unico e autocontido de geracao de shapes de acordes de violao/guitarra.

Empacota, numa unica funcao publica (`gerar_shapes_acorde`), toda a
inteligencia ja validada neste projeto - sem depender de nenhum outro
arquivo dele (nada de sqlite3/auditoria.db, nada de importar dedicacao.py,
validacao.py, dificuldade.py ou servidor.py). So biblioteca padrao do
Python. Pode ser copiado para outro app e usado isoladamente.

O QUE ESTA FUNCAO FAZ (por forca bruta + teoria musical, nao por templates
nem scraping): dado um nome de acorde (ex.: "E7(4)", "Bbm7b5", "C#dim7"),
enumera toda combinacao fisicamente possivel de casas nas 6 cordas dentro
de uma janela movel, valida a harmonia contra os intervalos reais da
qualidade do acorde, calcula a dedicacao (dedos e pestana), pontua a
dificuldade (rubrica ISMIR 2023) e descarta apenas o que e FISICAMENTE
IMPOSSIVEL - o resto (todos os diagramas validos) e retornado.

FONTES DAS REGRAS (nenhuma inventada; todas ja auditadas neste projeto e/ou
verificadas contra fonte externa confiavel nesta conversa):

  - Intervalos de cada qualidade de acorde: tabela TIPOS_DE_ACORDE do
    projeto (auditoria.db), copiada aqui como TIPOS_DE_ACORDE dict.
  - Tolerancia de "5a ausente": Wikipedia "Guitar chord" - "When playing
    seventh chords, guitarists often play only a subset of notes... The
    fifth is often omitted" + Guitar World, "Why omitting the 5th in
    guitar chords is a good idea". So se aplica a acordes com setima que
    NAO sao triade nem 5a alterada (flag `triade_ou_5a_alterada` abaixo,
    tambem copiada de TIPOS_DE_ACORDE) - a propria regua_v21.py do projeto
    ja fazia essa distincao fina.
  - Ergonomia/dedicacao (regras R1-R3: pestana so' quando >4 cordas
    tocadas; mini-pestana so' em ultimo caso; max 4 posicoes de dedo):
    dedicacao.py deste projeto.
  - traste_alto (casa pressionada >= 12 e' bloqueada sem excecao - corpo
    do instrumento impede o acesso da mao) e double_barre (2+ dedos
    diferentes cobrindo 2+ cordas cada e' fisicamente impossivel):
    REGRAS_DE_REPROVACAO do projeto (auditoria.db), verificadas na mao
    pelo usuario musico em 2026-08-07 e 2026-08-08.
  - Dificuldade: rubrica ISMIR 2023 (Vasquez et al., "Quantifying the
    Ease of Playing Song Chords on the Guitar"), ja em producao em
    dificuldade.py deste projeto.
  - "7sus4" (usado por notacoes tipo "7(4)"): nao existia em TIPOS_DE_ACORDE
    ate esta conversa. Intervalos (0,5,7,10) confirmados decodificando
    pixel a pixel um diagrama real do Cifra Club (acorde "E7(4)") e
    conferindo as notas resultantes contra teoria musical.

LIMITACAO DELIBERADA: nao trata slash chords (C/G etc.) - levanta
ValueError se houver "/" no nome. Isso e' um problema separado
(construcao de inversao), fora do escopo desta funcao.
"""
import itertools
from collections import Counter


def gerar_shapes_acorde(nome_acorde, casa_maxima=11):
    """Gera TODOS os shapes fisicamente possiveis e tocaveis de um acorde.

    Parametros
    ----------
    nome_acorde : str
        Nome do acorde em notacao de cifra (ex.: "E", "Am7", "Bbm7b5",
        "C#dim7", "G7(4)", "Ddim"). Bemois e sinonimos comuns de notacao
        (4=sus4, +/+5=aug, °/o=dim, °7/o7=dim7, 7(9)//9=9, 7(4)=7sus4)
        sao normalizados internamente.
    casa_maxima : int
        Casa mais alta considerada na busca (default 11 - regra
        traste_alto do projeto bloqueia casa >= 12 sem excecao; nao faz
        sentido buscar acima disso).

    Retorna
    -------
    list[dict]
        Ordenada por (casa_base, score de dificuldade, menor soma de
        casas). Cada item:
        {
          "acorde": "Bm7b5", "tonica": "B", "tipo": "m7b5",
          "diagrama": ["X","2","3","2","3","X"],  # 6 valores, "X" = muda
          "dedos": [0,1,2,1,3,0],                  # 0 = corda nao tocada
          "pestana": {"casa": int, "cordas": [i0..iN]} ou None,
          "casa_base": int,   # menor casa pressionada (0 = aberto)
          "dificuldade": {"score": int, "nivel": 1-5, "rotulo": str,
                          "detalhes": {"UC":.., "CFP":.., "CFD":.., "RHC":..}},
        }

    Levanta ValueError se o acorde nao puder ser interpretado (tipo
    desconhecido, slash chord) - nunca adivinha intervalos.
    """
    NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    CORDAS_AFINACAO = [40, 45, 50, 55, 59, 64]  # E A D G B e, grave->agudo
    LIMITE_ABERTURA = 4   # fisica.abertura (span max de casas presas)
    LIMITE_TRASTE_ALTO = 12  # traste_alto: casa >= 12 sempre bloqueada

    # codigo -> (intervalos em semitons a partir da tonica, e' triade ou
    # tem 5a alterada). Copiado de TIPOS_DE_ACORDE (auditoria.db).
    TIPOS_DE_ACORDE = {
        "":       ([0, 4, 7],            True),
        "5":      ([0, 7],                False),
        "6":      ([0, 4, 7, 9],          False),
        "69":     ([0, 4, 7, 9, 2],       False),
        "7":      ([0, 4, 7, 10],         False),
        "7#5":    ([0, 4, 8, 10],         True),
        "7M":     ([0, 4, 7, 11],         False),
        "7b5":    ([0, 4, 6, 10],         True),
        "7sus4":  ([0, 5, 7, 10],         False),
        "9":      ([0, 4, 7, 10, 2],      False),
        "add9":   ([0, 4, 7, 2],          False),
        "aug":    ([0, 4, 8],             True),
        "dim":    ([0, 3, 6],             True),
        "dim7":   ([0, 3, 6, 9],          True),
        "m":      ([0, 3, 7],             True),
        "m6":     ([0, 3, 7, 9],          False),
        "m7":     ([0, 3, 7, 10],         False),
        "m7M":    ([0, 3, 7, 11],         False),
        "m7b5":   ([0, 3, 6, 10],         True),
        "m9":     ([0, 3, 7, 10, 2],      False),
        "madd9":  ([0, 3, 7, 2],          False),
        "maj7":   ([0, 4, 7, 11],         False),
        "maj9":   ([0, 4, 7, 11, 2],      False),
        "mmaj7":  ([0, 3, 7, 11],         False),
        "sus2":   ([0, 2, 7],             True),
        "sus4":   ([0, 5, 7],             True),
    }

    BEMOL_MAP = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
    TIPO_SINONIMOS = {
        "°": "dim", "o": "dim", "O": "dim",
        "°7": "dim7", "o7": "dim7", "O7": "dim7",
        "+": "aug", "+5": "aug",
        "4": "sus4",
        "7(9)": "9", "7/9": "9",
        "7(4)": "7sus4",
    }

    # ---------- 1. parse do nome do acorde ----------
    def _parse(nome):
        nome = nome.strip()
        if "/" in nome:
            raise ValueError(
                f"{nome!r}: slash chords (inversao) nao sao tratados por "
                "esta funcao - escopo separado.")
        if len(nome) >= 2 and nome[1] in ("#", "b"):
            tonica_bruta, tipo = nome[:2], nome[2:]
        else:
            tonica_bruta, tipo = nome[:1], nome[1:]
        tonica = BEMOL_MAP.get(tonica_bruta, tonica_bruta)
        if tonica not in NOTAS:
            raise ValueError(f"{nome!r}: tonica {tonica_bruta!r} invalida.")
        tipo = TIPO_SINONIMOS.get(tipo, tipo)
        if tipo not in TIPOS_DE_ACORDE:
            raise ValueError(
                f"{nome!r}: tipo de acorde {tipo!r} desconhecido. "
                "Nao adivinho intervalos: cadastre em TIPOS_DE_ACORDE antes "
                "de gerar.")
        return tonica, tipo

    # ---------- 2. harmonia ----------
    def _notas_tocadas(casas):
        return {(CORDAS_AFINACAO[i] + c) % 12
                for i, c in enumerate(casas) if c is not None}

    def _shape_valido(casas, notas_acorde, toleradas):
        tocadas = _notas_tocadas(casas)
        return (tocadas.issubset(notas_acorde)
                and notas_acorde.issubset(tocadas | toleradas))

    # ---------- 3. ergonomia / dedicacao (dedicacao.py, R1-R3) ----------
    def _grupos_separados(tocadas):
        return [(c, [i]) for i, c in sorted(tocadas, key=lambda t: (t[1], t[0]))]

    def _esticar_pestana_ate_corda_fina(cordas_pestana, casas):
        cordas = list(cordas_pestana)
        proxima = max(cordas) + 1
        while proxima <= 5:
            if casas[proxima] == 0:
                break
            cordas.append(proxima)
            proxima += 1
        return cordas

    def _grupos_minimo(casas, tocadas):
        min_casa = min(c for _, c in tocadas)
        cordas_min = sorted(i for i, c in tocadas if c == min_casa)
        primeira, ultima = cordas_min[0], cordas_min[-1]
        vao_completo = all(
            casas[i] is not None and casas[i] > 0
            for i in range(primeira, ultima + 1))

        pestana = None
        if len(cordas_min) >= 2 and vao_completo:
            pestana = {"casa": min_casa, "cordas": list(range(primeira, ultima + 1))}
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

    def _grupos_de_dedo(casas):
        tocadas = [(i, c) for i, c in enumerate(casas) if c is not None and c > 0]
        if not tocadas:
            return None, []
        if len(tocadas) <= 4:
            return None, _grupos_separados(tocadas)

        min_casa = min(c for _, c in tocadas)
        cordas_min = sorted(i for i, c in tocadas if c == min_casa)
        primeira, ultima = cordas_min[0], cordas_min[-1]
        vao_completo = all(
            casas[i] is not None and casas[i] > 0
            for i in range(primeira, ultima + 1))
        resto = [(i, c) for i, c in tocadas if c != min_casa]

        if len(cordas_min) >= 2 and vao_completo and 1 + len(resto) <= 4:
            cordas_pestana = _esticar_pestana_ate_corda_fina(
                list(range(primeira, ultima + 1)), casas)
            return ({"casa": min_casa, "cordas": cordas_pestana},
                    _grupos_separados(resto))
        return _grupos_minimo(casas, tocadas)

    def _shape_tocavel(casas):
        pestana, grupos = _grupos_de_dedo(casas)
        return (1 if pestana else 0) + len(grupos) <= 4

    def _calcular_dedos_e_pestana(casas):
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

    # ---------- 4. filtros de impossibilidade fisica ----------
    def _traste_alto(diagrama):
        for v in diagrama:
            s = str(v).upper()
            if s in ("X", "-1", "0"):
                continue
            try:
                if int(s) >= LIMITE_TRASTE_ALTO:
                    return True
            except ValueError:
                continue
        return False

    def _tem_pestana_dupla(dedos):
        c = Counter(d for d in dedos if d and d > 0)
        return len([d for d, n in c.items() if n >= 2]) >= 2

    # ---------- 5. dificuldade (rubrica ISMIR 2023, dificuldade.py) ----------
    TONICAS_COMUNS = {"C", "D", "E", "F", "G", "A", "B"}
    TIPOS_COMUNS = {"", "m", "7", "m7"}
    TIPOS_RAROS = {"dim", "dim7", "aug", "9", "m7M"}
    NIVEIS = [(1, 1, "Muito Facil"), (6, 2, "Facil"), (11, 3, "Medio"),
              (20, 4, "Dificil"), (30, 5, "Muito Dificil")]

    def _nivel_uc(tonica, tipo):
        if tipo in TIPOS_RAROS:
            return 3
        t_comum, p_comum = tonica in TONICAS_COMUNS, tipo in TIPOS_COMUNS
        if t_comum and p_comum:
            return 0
        if t_comum or p_comum:
            return 1
        return 2

    def _nivel_cfp(casas, pestana):
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
            nivel = 0 if (tem_solta and casa_min <= 4) else 1
        if spread >= 4:
            nivel += 1
        if casa_min >= 10:
            nivel += 1
        return min(nivel, 3)

    def _nivel_cfd(dedos, pestana):
        if pestana:
            n = len(pestana.get("cordas", []))
            return 3 if n >= 5 else (2 if n >= 3 else 1)
        n = len({d for d in dedos if d > 0})
        if n <= 2:
            return 0
        return 1 if n == 3 else 3

    def _nivel_rhc(diagrama):
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
        return 2 if len(internas) == 1 else 3

    def _padrao_dois_blocos(diagrama, dedos, pestana):
        if pestana:
            return False
        casa_por_dedo = {}
        for v, d in zip(diagrama or [], dedos or []):
            s = str(v).upper()
            if s in ("X", "-1", "0") or not d or d == 0:
                continue
            try:
                casa_por_dedo[d] = int(s)
            except ValueError:
                continue
        if len(casa_por_dedo) < 4:
            return False
        por_casa = {}
        for d, c in casa_por_dedo.items():
            por_casa.setdefault(c, []).append(d)
        pares = sorted(c for c, ds in por_casa.items() if len(ds) >= 2)
        if len(pares) < 2:
            return False
        return any(pares[i + 1] - pares[i] - 1 >= 1 for i in range(len(pares) - 1))

    def _avaliar_dificuldade(diagrama, dedos, pestana, tonica, tipo):
        casas = []
        for v in diagrama:
            try:
                c = int(v)
            except (TypeError, ValueError):
                c = None
            casas.append(c if c is not None and c >= 0 else None)
        pressionadas = [c for c in casas if c is not None and c > 0]
        if not pressionadas:
            return {"score": 0, "nivel": 1, "rotulo": "Muito Facil",
                    "detalhes": {"UC": 0, "CFP": 0, "CFD": 0, "RHC": 0}}
        uc, cfp = _nivel_uc(tonica, tipo), _nivel_cfp(casas, pestana)
        cfd, rhc = _nivel_cfd(dedos, pestana), _nivel_rhc(diagrama)
        score = uc * 3 + cfp * 3 + cfd * 2 + rhc * 2
        nivel, rotulo = 5, "Muito Dificil"
        for max_s, n, r in NIVEIS:
            if score <= max_s:
                nivel, rotulo = n, r
                break
        if _padrao_dois_blocos(diagrama, dedos, pestana):
            nivel, rotulo = 5, "Muito Dificil"
        return {"score": score, "nivel": nivel, "rotulo": rotulo,
                "detalhes": {"UC": uc, "CFP": cfp, "CFD": cfd, "RHC": rhc}}

    # ---------- 6. geracao por forca bruta ----------
    tonica, tipo = _parse(nome_acorde)
    intervalos, triade_ou_5a_alterada = TIPOS_DE_ACORDE[tipo]
    tonica_idx = NOTAS.index(tonica)
    notas_acorde = {(tonica_idx + i) % 12 for i in intervalos}
    # Tolerancia de 5a ausente: so' para acordes com setima que NAO sao
    # triade nem tem 5a alterada (Wikipedia/Guitar World - ver docstring).
    toleradas = (
        {(tonica_idx + 7) % 12}
        if (7 in intervalos and not triade_ou_5a_alterada) else set()
    )

    casa_maxima = min(casa_maxima, LIMITE_TRASTE_ALTO - 1)
    vistos = set()
    resultados = []

    for base in range(1, casa_maxima - LIMITE_ABERTURA + 2):
        janela = [f for f in range(base, base + LIMITE_ABERTURA) if f <= casa_maxima]
        opcoes_por_corda = [[None, 0] + janela for _ in range(6)]

        for casas in itertools.product(*opcoes_por_corda):
            if all(c is None for c in casas):
                continue
            if casas in vistos:
                continue
            if not _shape_valido(list(casas), notas_acorde, toleradas):
                continue
            if not _shape_tocavel(list(casas)):
                continue

            diagrama = ["X" if c is None else str(c) for c in casas]
            if _traste_alto(diagrama):
                continue

            dedos, pestana = _calcular_dedos_e_pestana(list(casas))
            if _tem_pestana_dupla(dedos):
                continue

            vistos.add(casas)
            dif = _avaliar_dificuldade(diagrama, dedos, pestana, tonica, tipo)
            pressionadas = [c for c in casas if c is not None and c > 0]
            casa_base = min(pressionadas) if pressionadas else 0

            resultados.append({
                "acorde": tonica + tipo,
                "tonica": tonica,
                "tipo": tipo,
                "diagrama": diagrama,
                "dedos": dedos,
                "pestana": pestana,
                "casa_base": casa_base,
                "dificuldade": dif,
            })

    resultados.sort(key=lambda s: (
        s["casa_base"], s["dificuldade"]["score"],
        sum(int(c) for c in s["diagrama"] if c != "X")))
    return resultados


if __name__ == "__main__":
    import sys
    nome = sys.argv[1] if len(sys.argv) > 1 else "E7(4)"
    shapes = gerar_shapes_acorde(nome)
    print(f"{nome} -> acorde normalizado {shapes[0]['acorde'] if shapes else '?'}, "
          f"{len(shapes)} shapes")
    for s in shapes[:10]:
        print(",".join(s["diagrama"]).ljust(15), "dedos=", s["dedos"],
              "pestana=", s["pestana"], "dificuldade=", s["dificuldade"]["rotulo"])
