with open('index.html', encoding='utf-8') as f:
    content = f.read()

orig_len = len(content)

# --- CSS ---
css_extra = """
.painel-acorde-btn{background:none;border:none;padding:0;font:inherit;color:var(--accent);cursor:pointer;text-decoration:underline;text-underline-offset:2px}
.painel-galeria-modal{background:var(--surface);border-radius:var(--radius-lg);padding:24px;max-width:900px;width:92%;max-height:85vh;box-shadow:var(--shadow-lg);display:flex;flex-direction:column}
.painel-galeria-modal h3{font-size:18px;font-weight:650;margin-bottom:16px}
.painel-galeria-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:18px;overflow-y:auto;padding-right:4px}
.painel-galeria-item{text-align:center}
.painel-galeria-item-label{font-size:11.5px;color:var(--text-secondary);margin-top:6px;font-family:ui-monospace,Menlo,monospace}
.painel-galeria-item-rotulo{font-size:11px;color:var(--text-secondary);margin-top:2px}
.painel-modal-fechar{align-self:center}
"""
end_style_marker = "</style>"
assert content.count(end_style_marker) == 1
content = content.replace(end_style_marker, css_extra + "\n" + end_style_marker, 1)

# --- HTML: nova overlay de galeria, logo apos a overlay existente ---
marker_html = '''<div class="painel-modal-overlay" id="painelModalOverlay" onclick="if(event.target===this)fecharDiagramaPainel()">
<div class="painel-modal">
<h3 id="painelModalTitulo"></h3>
<div id="painelModalSvg"></div>
<div class="painel-modal-info" id="painelModalInfo"></div>
<button class="painel-modal-fechar" onclick="fecharDiagramaPainel()">Fechar</button>
</div>
</div>'''
assert content.count(marker_html) == 1, "âncora do modal overlay não encontrada"

novo_html = marker_html + '''

<div class="painel-modal-overlay" id="painelGaleriaOverlay" onclick="if(event.target===this)fecharGaleriaAcorde()">
<div class="painel-galeria-modal">
<h3 id="painelGaleriaTitulo"></h3>
<div class="painel-galeria-grid" id="painelGaleriaGrid"></div>
<button class="painel-modal-fechar" onclick="fecharGaleriaAcorde()">Fechar</button>
</div>
</div>'''
content = content.replace(marker_html, novo_html, 1)

# --- JS: acordeCell vira botão clicável ---
marker_cell = "? '<td class=\\\"painel-acorde-cell\\\" rowspan=\\\"'+a.shapes.length+'\\\"><b>'+a.acorde+'</b><span class=\\\"painel-acorde-total\\\">'+a.total_shapes+' shape'+(a.total_shapes!==1?'s':'')+'</span></td>'"
assert content.count(marker_cell) == 1, "âncora da célula do acorde não encontrada"

novo_cell = "? '<td class=\\\"painel-acorde-cell\\\" rowspan=\\\"'+a.shapes.length+'\\\"><b>'+a.acorde+'</b><br><button class=\\\"painel-acorde-btn\\\" onclick=\\\"event.stopPropagation();abrirGaleriaAcorde('+ai+')\\\">'+a.total_shapes+' shape'+(a.total_shapes!==1?'s':'')+'</button></td>'"
content = content.replace(marker_cell, novo_cell, 1)

# --- JS: novas funções de galeria, inseridas antes de fecharDiagramaPainel ---
marker_func = "function fecharDiagramaPainel(){\n  document.getElementById('painelModalOverlay').classList.remove('aberto');\n}"
assert content.count(marker_func) == 1

galeria_funcs = '''function abrirGaleriaAcorde(ai){
  const a=PAINEL_LISTA_ATUAL[ai];
  document.getElementById('painelGaleriaTitulo').textContent=a.acorde+' \\u2014 '+a.shapes.length+' shapes';
  document.getElementById('painelGaleriaGrid').innerHTML=a.shapes.map(function(sh){
    return '<div class="painel-galeria-item">'
      + gerarSVG(sh.diagrama,sh.dedos,sh.pestana)
      + '<div class="painel-galeria-item-label">'+sh.shape+'</div>'
      + '<div class="painel-galeria-item-rotulo">'+sh.dificuldade.rotulo+'</div>'
      + '</div>';
  }).join('');
  document.getElementById('painelGaleriaOverlay').classList.add('aberto');
}

function fecharGaleriaAcorde(){
  document.getElementById('painelGaleriaOverlay').classList.remove('aberto');
}

'''
content = content.replace(marker_func, galeria_funcs + marker_func, 1)

# --- JS: ESC fecha as duas overlays ---
marker_esc = "document.addEventListener('keydown', function(e){\n  if(e.key==='Escape') fecharDiagramaPainel();\n});"
assert content.count(marker_esc) == 1, "âncora do listener de ESC não encontrada"

novo_esc = "document.addEventListener('keydown', function(e){\n  if(e.key==='Escape'){\n    fecharDiagramaPainel();\n    fecharGaleriaAcorde();\n  }\n});"
content = content.replace(marker_esc, novo_esc, 1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("OK - bytes:", orig_len, "->", len(content))
