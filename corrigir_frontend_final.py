caminho = '/Users/marcelo/gerador_guitarra/index.html'
with open(caminho, 'r', encoding='utf-8') as f:
    conteudo = f.read()

antigo_btn = "'+'+(data.diagramas.length-1)+' variações'"
novo_btn = "'+'+(data.total_diagramas-1)+' variações'"

if antigo_btn in conteudo:
    conteudo = conteudo.replace(antigo_btn, novo_btn)
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print("✅ Frontend corrigido")
else:
    print("⚠️ Texto não encontrado")
