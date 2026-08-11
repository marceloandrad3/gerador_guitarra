with open('index.html', encoding='utf-8') as f:
    content = f.read()

orig_len = len(content)

# --- 1. remove botão da aba ---
marker1 = '<button id="tab-cobertura" class="tab-btn" onclick="mostrarAba(\'cobertura\')">Cobertura</button>\n'
assert content.count(marker1) == 1, "botão Cobertura não encontrado"
content = content.replace(marker1, '', 1)

# --- 2. remove seção secao-cobertura inteira ---
start_marker = '<div id="secao-cobertura" style="display:none">'
end_marker = '<script>'
i1 = content.index(start_marker)
i2 = content.index(end_marker, i1)
content = content[:i1] + content[i2:]

# --- 3. mostrarAba: remove referências a cobertura ---
marker3 = '''function mostrarAba(aba){
  const isPainel = ['aprovados','auditoria','reprovados'].includes(aba);
  document.getElementById('secao-painel').style.display = isPainel ? '' : 'none';
  document.getElementById('secao-cobertura').style.display = aba==='cobertura' ? '' : 'none';
  document.getElementById('secao-impossiveis').style.display = aba==='impossiveis' ? '' : 'none';
  ['aprovados','auditoria','reprovados','cobertura','impossiveis'].forEach(function(a){
    document.getElementById('tab-'+a).classList.toggle('ativa', aba===a);
  });
  if(aba==='cobertura') carregarCobertura();
  if(aba==='impossiveis') carregarImpossiveis();
  if(isPainel) carregarPainel(aba);
}'''
assert content.count(marker3) == 1, "mostrarAba não encontrada de forma única"

novo_mostrarAba = '''function mostrarAba(aba){
  const isPainel = ['aprovados','auditoria','reprovados'].includes(aba);
  document.getElementById('secao-painel').style.display = isPainel ? '' : 'none';
  document.getElementById('secao-impossiveis').style.display = aba==='impossiveis' ? '' : 'none';
  ['aprovados','auditoria','reprovados','impossiveis'].forEach(function(a){
    document.getElementById('tab-'+a).classList.toggle('ativa', aba===a);
  });
  if(aba==='impossiveis') carregarImpossiveis();
  if(isPainel) carregarPainel(aba);
}'''
content = content.replace(marker3, novo_mostrarAba, 1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("OK - bytes:", orig_len, "->", len(content))
