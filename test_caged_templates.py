import sys
sys.path.insert(0, '.')
from gerador_web_dinamico import NOTAS, CORDAS_AFINACAO, get_intervalos

CAGED_MAIOR = {
    "E": {"raiz_corda": 0, "offsets": [0, 2, 2, 1, 0, 0]},
    "A": {"raiz_corda": 1, "offsets": [None, 0, 2, 2, 2, 0]},
    "D": {"raiz_corda": 2, "offsets": [None, None, 0, 2, 3, 2]},
    "C": {"raiz_corda": 1, "offsets": [None, 0, -1, -3, -2, -3]},
    "G": {"raiz_corda": 0, "offsets": [0, -1, -3, -3, -3, 0]},
}

def gerar_shapes_caged(tonica, tipo):
    tonica_idx = NOTAS.index(tonica)
    intervalos = get_intervalos(tipo)
    notas_acorde = set((tonica_idx + i) % 12 for i in intervalos)
    templates = CAGED_MAIOR if tipo not in ("m", "menor") else {}
    shapes = []
    ordem_caged = ["E", "A", "D", "C", "G"]

    for nome_shape in ordem_caged:
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
                "dedos": [0]*6,
                "pestana": pestana,
                "score": score,
            })
            break
    return shapes

print("=" * 70)
print("TESTE: Templates CAGED para A maior")
print("=" * 70)

shapes = gerar_shapes_caged("A", "")
print(f"Shapes gerados: {len(shapes)}\n")

esperados = {
    "E": ["5","7","7","6","5","5"],
    "A": ["X","0","2","2","2","0"],
    "D": ["X","X","7","9","10","9"],
    "C": ["X","12","11","9","10","9"],
    "G": ["5","4","2","2","2","5"],
}

todos_corretos = True
for s in shapes:
    nome = s["nome_exato"]
    diag = s["diagrama"]
    shape_letra = nome.split("(")[1].rstrip(")")
    exp = esperados.get(shape_letra, [])
    ok = diag == exp
    if not ok:
        todos_corretos = False
    status = "OK" if ok else "ERRO"
    print(f"{nome}: {diag} | Esperado: {exp} | {status}")

print("\n" + "=" * 70)
if todos_corretos and len(shapes) == 5:
    print("SUCESSO: Todos os 5 shapes CAGED estao corretos.")
else:
    print("FALHA: Shapes incorretos ou faltando.")
print("=" * 70)
