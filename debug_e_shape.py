import sys
sys.path.insert(0, '.')
from gerador_web_dinamico import gerar_shapes_dinamicos, NOTAS, CORDAS_AFINACAO

print("=" * 70)
print("DIAGNOSTICO: Geracao de shapes para A maior")
print("=" * 70)

shapes = gerar_shapes_dinamicos("A", "")
print(f"\nTotal de shapes retornados: {len(shapes)}\n")

e_shape_encontrado = False
for i, shape in enumerate(shapes):
    diagrama = shape.get("diagrama", [])
    nome = shape.get("nome_exato", "sem nome")
    esperado = ["5", "7", "7", "6", "5", "5"]
    eh_e_shape = (diagrama == esperado)
    if eh_e_shape:
        e_shape_encontrado = True
    status = "E SHAPE ENCONTRADO" if eh_e_shape else "NAO E SHAPE"
    print(f"Shape {i+1}: {diagrama} | Nome: {nome} | {status}")

print("\n" + "=" * 70)
if e_shape_encontrado:
    print("RESULTADO: E shape (5 7 7 6 5 5) ESTA sendo gerado.")
else:
    print("RESULTADO: E shape (5 7 7 6 5 5) NAO esta sendo gerado.")
print("=" * 70)

print("\nANALISE DETALHADA DAS NOTAS EM CADA SHAPE:")
print("-" * 70)
for i, shape in enumerate(shapes):
    diagrama = shape.get("diagrama", [])
    notas_shape = []
    for corda_idx in range(6):
        val = diagrama[corda_idx]
        if val == "X":
            notas_shape.append("X")
        else:
            casa = int(val)
            midi = CORDAS_AFINACAO[corda_idx] + casa
            nota_nome = NOTAS[midi % 12]
            notas_shape.append(f"{nota_nome}({casa})")
    print(f"Shape {i+1}: {diagrama} -> Notas: {notas_shape}")

print("\n" + "=" * 70)
print("FIM DO DIAGNOSTICO")
print("=" * 70)
