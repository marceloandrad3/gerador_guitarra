import re

caminho = "/Users/marcelo/gerador_guitarra/gerador_web_dinamico.py"

with open(caminho, "r") as f:
    conteudo = f.read()

# Templates CAGED completos (maior e menor)
templates_code = '''
# =============================================================================
# TEMPLATES CAGED VERIFICADOS
# =============================================================================

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
    "Cm": {"raiz_corda": 1, "offsets": [None, 0, -1, -3, -2, -3]},
    "Gm": {"raiz_corda": 0, "offsets": [0, -1, -3, -3, -3, 0]},
}

'''

nova_funcao = '''
def gerar_shapes_dinamicos(tonica, tipo):
    """Gera os 5 shapes CAGED usando templates verificados."""
    tonica_idx = NOTAS.index(tonica)
    intervalos = get_intervalos(tipo)
    notas_acorde = set((tonica_idx + i) % 12 for i in intervalos)

    if tipo in ("m", "menor"):
        templates = CAGED_MENOR
        ordem = ["Em", "Am", "Dm", "Cm", "Gm"]
    else:
        templates = CAGED_MAIOR
        ordem = ["E", "A", "D", "C", "G"]

    shapes = []
    for nome_shape in ordem:
        tmpl = templates[nome_shape]
        raiz_corda = tmpl["raiz_corda"]
        offsets = tmpl["offsets"]
        afinacao_raiz = CORDAS_AFINACAO[raiz_corda]

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

            todas_ok = True
            notas_presentes = set()
            for corda_idx in range(6):
                if casas[corda_idx] is None:
                    continue
                midi = CORDAS_AFINACAO[corda_idx] + casas[corda_idx]
                nota = midi % 12
                if nota not in notas_acorde:
                    todas_ok = False
                    break
                notas_presentes.add(nota)

            if not todas_ok or notas_presentes != notas_acorde:
                continue

            diagrama = []
            for corda_idx in range(6):
                if casas[corda_idx] is None:
                    diagrama.append("X")
                else:
                    diagrama.append(str(casas[corda_idx]))

            min_casa = min((c for c in casas if c is not None and c > 0), default=0)
            pestana = None
            if min_casa > 0:
                cordas_p = [i for i in range(6) if casas[i] == min_casa]
                if len(cordas_p) >= 2:
                    pestana = {"casa": min_casa, "cordas": cordas_p}

            score = sum(c for c in casas if c is not None)
            shapes.append({
                "nome_exato": f"{tonica}{tipo} ({nome_shape})",
                "diagrama": diagrama,
                "dedos": [0] * 6,
                "pestana": pestana,
                "score": score,
            })
            break

    return shapes

'''

# Encontrar e substituir a funcao antiga
padrao = r'def gerar_shapes_dinamicos\(tonica, tipo\):.*?(?=\ndef |\Z)'
match = re.search(padrao, conteudo, re.DOTALL)

if match:
    # Inserir templates antes da funcao e substituir a funcao
    pos_inicio = match.start()
    novo_conteudo = (
        conteudo[:pos_inicio] +
        templates_code +
        nova_funcao +
        "\n" +
        conteudo[match.end():]
    )
    with open(caminho, "w") as f:
        f.write(novo_conteudo)
    print("SUCESSO: Arquivo atualizado com templates CAGED.")
else:
    print("ERRO: Funcao gerar_shapes_dinamicos nao encontrada no arquivo.")
