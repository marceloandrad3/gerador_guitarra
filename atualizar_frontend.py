import re

caminho_original = '/Users/marcelo/gerador_guitarra/index.html'
caminho_novo = '/Users/marcelo/gerador_guitarra/index_atualizado.html'

with open(caminho_original, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Substituição 1: Mudar slice(0,5) para slice(0,1)
conteudo = conteudo.replace(
    'const shapes=mostrarTodos?data.diagramas:data.diagramas.slice(0,5);',
    'const shapes=mostrarTodos?data.diagramas:data.diagramas.slice(0,1);'
)

# Substituição 2: Mudar texto do botão e condição
conteudo = conteudo.replace(
    "if(data.diagramas.length>5&&!mostrarTodos)",
    "if(data.diagramas.length>1&&!mostrarTodos)"
)

# Substituição 3: Mudar texto do botão
conteudo = conteudo.replace(
    "'Ver mais ('+(data.diagramas.length-5)+' shapes adicionais)'",
    "'+'+(data.diagramas.length-1)+' variações'"
)

with open(caminho_novo, 'w', encoding='utf-8') as f:
    f.write(conteudo)

print(f"✅ Arquivo atualizado salvo em: {caminho_novo}")
print(" Para aplicar: mv /Users/marcelo/gerador_guitarra/index_atualizado.html /Users/marcelo/gerador_guitarra/index.html")
