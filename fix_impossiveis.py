with open('index.html', encoding='utf-8') as f:
    content = f.read()

orig_len = len(content)

# --- 1. mostrarAba: impossiveis entra no painel unificado ---
marker1 = '''function mostrarAba(aba){
  const isPainel = ['aprovados','auditoria','reprovados'].includes(aba);
  document.getElementById('secao-painel').style.display = isPainel ? '' : 'none';
  document.getElementById('secao-impossiveis').style.display = aba==='impossiveis' ? '' : 'none';
  ['aprovados','auditoria','reprovados','impossiveis'].forEach(function(a){
    document.getElementById('tab-'+a).classList.toggle('ativa', aba===a);
  });
  if(aba==='impossiveis') carregarImpossiveis();
  if(isPainel) carregarPainel(aba);
}'''
assert content.count(marker1) == 1, "mostrarAba não encontrada de forma única"

novo1 = '''function mostrarAba(aba){
  const isPainel = ['aprovados','auditoria','reprovados','impossiveis'].includes(aba);
  document.getElementById('secao-painel').style.display = isPainel ? '' : 'none';
  ['aprovados','auditoria','reprovados','impossiveis'].forEach(function(a){
    document.getElementById('tab-'+a).classList.toggle('ativa', aba===a);
  });
  if(isPainel) carregarPainel(aba);
}'''
content = content.replace(marker1, novo1, 1)

# --- 2. remove secao-impossiveis (agora dead markup) ---
start_marker = '<div id="secao-impossiveis" style="display:none">'
end_marker = '<script>'
i1 = content.index(start_marker)
i2 = content.index(end_marker, i1)
content = content[:i1] + content[i2:]

# --- 3. remove função antiga carregarImpossiveis ---
start_marker2 = 'async function carregarImpossiveis(){'
end_marker2 = 'async function carregarAuditoria(){'
i1b = content.index(start_marker2)
i2b = content.index(end_marker2, i1b)
content = content[:i1b] + content[i2b:]

# --- 4. CSS: cor do chip para impossiveis (mesma severidade de reprovados) ---
css_extra = """
.painel-chip-impossiveis{background:var(--danger-soft);color:var(--danger)}
"""
end_style_marker = "</style>"
assert content.count(end_style_marker) == 1
content = content.replace(end_style_marker, css_extra + "\n" + end_style_marker, 1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("OK - bytes:", orig_len, "->", len(content))
