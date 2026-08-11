import itertools
import json

AFINACAO_PADRAO = [4, 9, 2, 7, 11, 4]
NOMES_NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
INTERVALOS = {'1': 0, 'b2': 1, '2': 2, 'b3': 3, '3': 4, '4': 5, 'b5': 6, '5': 7, '#5': 8, '6': 9, 'b7': 10, '7': 11}

FORMULAS = {
    "Maior": ['1', '3', '5'],
    "Menor": ['1', 'b3', '5'],
    "Diminuta": ['1', 'b3', 'b5'],
    "Aumentada": ['1', '3', '#5'],
    "7": ['1', '3', '5', 'b7'],
    "m7": ['1', 'b3', '5', 'b7'],
    "maj7": ['1', '3', '5', '7']
}

def construir_matriz(afinacao, n_casas):
    return [[(c_raiz + casa) % 12 for casa in range(n_casas + 1)] for c_raiz in afinacao]

def obter_notas_formula(tonica_str, formula):
    t_id = NOMES_NOTAS.index(tonica_str)
    return {(t_id + INTERVALOS[i]) % 12 for i in formula}

def calcular_score(comb):
    casas = [c for c in comb if c != 'X' and c > 0]
    return sum(casas) + (max(casas) - min(casas) if casas else 0)

def gerar_todos_acordes(matriz):
    resultado = []
    for tonica in NOMES_NOTAS:
        for nome_form, formula in FORMULAS.items():
            notas_req = obter_notas_formula(tonica, formula)
            opcoes = [['X'] + [c for c in range(13) if matriz[i][c] in notas_req] for i in range(6)]
            
            combinacoes = []
            for comb in itertools.product(*opcoes):
                casas = [c for c in comb if c != 'X' and c != 0]
                if not casas or (max(casas) - min(casas) + 1) > 4: 
                    continue
                
                if not notas_req.issubset({matriz[i][c] for i, c in enumerate(comb) if c != 'X'}): 
                    continue
                
                dedos = len(casas)
                pestana = min(casas)
                if casas.count(pestana) > 1: 
                    dedos = dedos - casas.count(pestana) + 1
                if dedos > 4: 
                    continue
                
                combinacoes.append({
                    "diagrama": [str(x) for x in comb],
                    "score": calcular_score(comb)
                })
            
            unicos = {tuple(d["diagrama"]): d for d in combinacoes}.values()
            ordenados = sorted(unicos, key=lambda x: x["score"])
            
            resultado.append({
                "acorde": f"{tonica} {nome_form}",
                "total_diagramas": len(ordenados),
                "diagramas": ordenados
            })
    return resultado

if __name__ == "__main__":
    matriz = construir_matriz(AFINACAO_PADRAO, 12)
    todos_acordes = gerar_todos_acordes(matriz)
    
    with open("todos_acordes.json", "w", encoding="utf-8") as f:
        json.dump({"catalogo": todos_acordes}, f, indent=4, ensure_ascii=False)
        
    total_geral = sum(a["total_diagramas"] for a in todos_acordes)
    print("GERAÇÃO EM MASSA CONCLUÍDA")
    print(f"Total de acordes processados: {len(todos_acordes)}")
    print(f"Total geral de diagramas gerados: {total_geral}")
