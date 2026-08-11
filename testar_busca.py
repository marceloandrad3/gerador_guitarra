from gerador_universal_100 import gerar_100_por_cento

resultados = gerar_100_por_cento("F", ['1', '3', '5', '7', '#11'], max_casas=12, max_span=4)
print(f"Total de diagramas exatos gerados para F7M(#11): {len(resultados)}")
for d in resultados[:3]:
    print(d)
