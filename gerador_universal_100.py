import itertools
import json

AFINACAO_PADRAO = [4, 9, 2, 7, 11, 4]
NOMES_NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Dicionário completo de intervalos expandido (incluindo todas as extensões e alterações)
INTERVALOS_COMPLETO = {
    '1': 0, 'b2': 1, '2': 2, 'sus2': 2, 'b3': 3, '3': 4, '4': 5, 'sus4': 5,
    'b5': 6, '#4': 6, '5': 7, '#5': 8, 'b6': 8, '6': 9, 'bb7': 9, '13': 9,
    'b7': 10, '7': 10, 'maj7': 11, 'b9': 1, '9': 2, '#9': 3, '11': 5, '#11': 6, 'b13': 8
}

def construir_matriz(afinacao, n_casas):
    return [[(corda_raiz + casa) % 12 for casa in range(n_casas + 1)] for corda_raiz in afinacao]

def gerar_100_por_cento(tonica_str, formula_lista, max_casas=12, max_span=4):
    tonica_id = NOMES_NOTAS.index(tonica_str)
    notas_permitidas = {(tonica_id + INTERVALOS_COMPLETO[inter]) % 12 for inter in formula_lista}
    
    matriz = construir_matriz(AFINACAO_PADRAO, max_casas)
    
    # 100% de abrangência: permitimos qualquer casa de 0 a max_casas para cada corda
    opcoes_por_corda = []
    for corda in matriz:
        opcoes = ['X']
        for casa in range(max_casas + 1):
            if corda[casa] in notas_permitidas:
                opcoes.append(casa)
        opcoes_por_corda.append(opcoes)
        
    diagramas_validos = []
    for comb in itertools.product(*opcoes_por_corda):
        casas_pressionadas = [c for c in comb if c != 'X' and c > 0]
        
        # Regra de Span (abertura máxima dos dedos)
        if casas_pressionadas:
            span = max(casas_pressionadas) - min(casas_pressionadas) + 1
            if span > max_span:
                continue
                
        # Filtro de notas obrigatórias (garante que a harmonia está presente)
        notas_no_acorde = {matriz[i][c] for i, c in enumerate(comb) if c != 'X'}
        if not notas_permitidas.issubset(notas_no_acorde):
            continue
            
        diagramas_validos.append([str(x) for x in comb])
        
    return diagramas_validos

if __name__ == "__main__":
    # Testando o acorde específico mencionado: F 7M(#11)
    tonica = "F"
    formula = ['1', '3', '5', '7', '#11']
    
    resultados = gerar_100_por_cento(tonica, formula, max_casas=12, max_span=4)
    print(f"Total de diagramas 100% exaustivos gerados para {tonica} 7M(#11): {len(resultados)}")
    print("Exemplos encontrados:")
    for d in resultados[:5]:
        print(d)
