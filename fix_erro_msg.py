import re

with open('index.html', 'r', encoding='utf-8') as f:
    conteudo = f.read()

antigo = """    const resp=await fetch('/gerar?acorde='+encodeURIComponent(acorde));
    if(!resp.ok)throw new Error('HTTP '+resp.status);
    const data=await resp.json();
    if(!data.diagramas||!data.diagramas.length){ct.innerHTML='<p class="mensagem">Nenhum diagrama encontrado para "'+acorde+'".</p>';return}"""

novo = """    const resp=await fetch('/gerar?acorde='+encodeURIComponent(acorde));
    const data=await resp.json().catch(function(){return null});
    if(!resp.ok){
      const msg=(data&&data.erro)?data.erro:'Cifra não localizada no banco de dados.';
      ct.innerHTML='<p class="mensagem">'+msg+' Verifique sua digitação.</p>';
      return;
    }
    if(!data.diagramas||!data.diagramas.length){ct.innerHTML='<p class="mensagem">Nenhum diagrama encontrado para "'+acorde+'".</p>';return}"""

if antigo not in conteudo:
    print("ERRO: trecho antigo não encontrado. Nenhuma alteração feita.")
else:
    conteudo = conteudo.replace(antigo, novo)
    conteudo = conteudo.replace(
        "}catch(e){ct.innerHTML='<p class=\"mensagem\">Erro: '+e.message+'. Verifique se o servidor está rodando.</p>'}",
        "}catch(e){ct.innerHTML='<p class=\"mensagem\">Erro: servidor fora do ar ou sem conexão.</p>'}"
    )
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print("Patch aplicado com sucesso.")
