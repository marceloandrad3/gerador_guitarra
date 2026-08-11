import itertools
import json

AFINACAO_PADRAO = [4, 9, 2, 7, 11, 4]
NOMES_NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

INTERVALOS_COMPLETO = {
    '1': 0, 'b2': 1, '2': 2, 'sus2': 2, 'b3': 3, '3': 4, '4': 5, 'sus4': 5,
    'b5': 6, '#4': 6, '5': 7, '#5': 8, 'b6': 8, '6': 9, 'bb7': 9, '13': 9,
    'b7': 10, '7': 10, 'maj7': 11, 'b9': 1, '9': 2, '#9': 3, '11': 5, '#11': 6, 'b13': 8
}

def parse_simbolo_acorde(simbolo):
    simbolo = simbolo.strip()
    # Separa inversão de baixo se houver (ex: F7M(#11)/C)
    baixo = None
    if '/' in simbolo:
        simbolo, baixo = simbolo.split('/')
        baixo = baixo.strip().upper()
        
    # Extrai tônica (ex: F, F#, C#)
    tonica = simbolo[0].upper()
    if len(simbolo) > 1 and simbolo[1] in ['#', 'b']:
        tonica += simbolo[1]
        qualidade_str = simbolo[2:]
    else:
        qualidade_str = simbolo[1:]
        
    qualidade_str = qualidade_str.strip()
    
    # Mapeia fórmulas comuns baseadas no texto digitado
    if qualidade_str == "" or qualidade_str.lower() in ["maior", "m"]:
        if qualidade_str.lower() == "m":
            formula = ['1', 'b3', '5']
        else:
            formula = ['1', '3', '5']
    elif qualidade_str in ["7M", "maj7", "7+"]:
        formula = ['1', '3', '5', '7']
    elif qualidade_str in ["7", "dom7"]:
        formula = ['1', '3', '5', 'b7']
    elif "7M(#11)" in qualidade_str or "7M(11+)" in qualidade_str:
        formula = ['1', '3', '5', '7', '#11']
    elif qualidade_str in ["m7"]:
        formula = ['1', 'b3', '5', 'b7']
    else:
        # Fallback genérico para tríade maior caso não reconheça exatamente
        formula = ['1', '3', '5']
        
    return tonica, formula, baixo

def construir_matriz(afinacao, n_casas):
    return [[(corda_raiz + casa) % 12 for casa in range(n_casas + 1)] for corda_raiz in afinacao]

def gerar_para_busca(simbolo_input, max_casas=12, max_span=4):
    tonica_str, formula_lista, baixo_requerido = parse_simbolo_acorde(simbolo_input)
    tonica_id = NOMES_NOTAS.index(tonica_str)
    
    notas_permitidas = {(tonica_id + INTERVALOS_COMPLETO[inter]) % 12 for inter in formula_lista}
    matriz = construir_matriz(AFINACAO_PADRAO, max_casas)
    
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
        if casas_pressionadas:
            if (max(casas_pressionadas) - min(casas_pressionadas) + 1) > max_span:
                continue
                
        notas_no_acorde = {matriz[i][c] for i, c in enumerate(comb) if c != 'X'}
        if not notas_permitidas.issubset(notas_no_acorde):
            continue
            
        if baixo_requerido is not None:
            baixo_id = NOMES_NOTAS.index(baixo_requerido)
            primeira_nota_tocada = None
            for i, c in enumerate(comb):
                if c != 'X':
                    primeira_nota_tocada = matriz[i][c]
                    break
            if primeira_nota_tocada != baixo_id:
                continue
                
        diagramas_validos.append({
            "diagrama": [str(x) for x in comb],
            "score": sum(casas_pressionadas) + (max(casas_pressionadas) - min(casas_pressionadas) if casas_pressionadas else 0)
        })
        
    unicos = {tuple(d["diagrama"]): d for d in diagramas_validos}.values()
    ordenados = sorted(unicos, key=lambda x: x["score"])
    
    return {
        "acorde": simbolo_input,
        "total_diagramas": len(ordenados),
        "diagramas": ordenados
    }

if __name__ == "__main__":
    res = gerar_para_busca("F7M(11+)/C")
    print(f"Gerados {res['total_diagramas']} para F7M(11+)/C")
