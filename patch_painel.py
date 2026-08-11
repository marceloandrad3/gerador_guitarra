import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

orig_len = len(content)

# --- 1. CSS: variáveis e classes novas antes de </style> ---
CSS_NOVO = """
--warning:#b45f06;
--warning-soft:rgba(255,159,10,.15);
</style>""".replace("</style>", "")  # placeholder, montado abaixo

css_vars = "--warning:#b45f06;\n--warning-soft:rgba(255,159,10,.15);\n"
assert content.count(":root{") == 1 or content.count("--danger-soft:rgba(255,59,48,.12);") == 1, "âncora --danger-soft não encontrada"
marker = "--danger-soft:rgba(255,59,48,.12);"
assert content.count(marker) == 1
content = content.replace(marker, marker + "\n" + css_vars, 1)

css_classes = """
.painel-resumo{max-width:1040px;margin:16px auto 14px;padding:0 20px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.painel-busca{max-width:1040px;margin:0 auto 18px;padding:0 20px}
.painel-busca input{width:100%;max-width:340px;padding:10px 14px;border-radius:12px;border:1px solid var(--border);font-size:14px;font-family:inherit}
.painel-lista{max-width:1040px;margin:0 auto 40px;padding:0 20px}
.painel-acorde{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-md);margin-bottom:8px;overflow:hidden;box-shadow:var(--shadow-sm)}
.painel-acorde-header{display:flex;align-items:center;gap:10px;padding:13px 16px;cursor:pointer;transition:background .15s var(--ease)}
.painel-acorde-header:hover{background:var(--surface-alt)}
.painel-acorde-seta{font-size:11px;color:var(--text-secondary);width:12px;flex:0 0 auto}
.painel-acorde-nome{font-weight:650;font-size:15px;min-width:70px}
.painel-acorde-count{color:var(--text-secondary);font-size:13px;margin-left:auto}
.painel-shapes{display:none;border-top:1px solid var(--border);padding:6px 16px 10px 42px}
.painel-shapes.aberto{display:block}
.painel-shape-row{display:flex;align-items:center;gap:14px;padding:8px 0;border-bottom:1px solid var(--border);font-size:12.5px;cursor:pointer;transition:color .15s var(--ease)}
.painel-shape-row:last-child{border-bottom:none}
.painel-shape-row:hover{color:var(--accent)}
.painel-shape-codigo{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:var(--text);min-width:150px}
.painel-shape-info{color:var(--text-secondary);flex:1}
.painel-vazio{text-align:center;color:var(--text-secondary);padding:30px;font-size:14px}
.painel-modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:100;align-items:center;justify-content:center}
.painel-modal-overlay.aberto{display:flex}
.painel-modal{background:var(--surface);border-radius:var(--radius-lg);padding:24px;max-width:320px;width:90%;box-shadow:var(--shadow-lg);text-align:center}
.painel-modal h3{font-size:17px;font-weight:650;margin-bottom:14px}
.painel-modal-info{font-size:12.5px;color:var(--text-secondary);margin-top:14px;line-height:1.7;text-align:left}
.painel-modal-info b{color:var(--text);font-weight:600}
.painel-modal-fechar{margin-top:18px;padding:9px 22px;border-radius:12px;background:var(--text);color:#fff;border:none;font-size:13px;font-weight:600;cursor:pointer}
.painel-chip{padding:8px 16px;border-radius:20px;font-weight:600;font-size:13px}
.painel-chip-aprovados{background:var(--success-soft);color:var(--success)}
.painel-chip-auditoria{background:var(--warning-soft);color:var(--warning)}
.painel-chip-reprovados{background:var(--danger-soft);color:var(--danger)}
"""
end_style_marker = "</style>"
assert content.count(end_style_marker) >= 1
content = content.replace(end_style_marker, css_classes + "\n" + end_style_marker, 1)

# --- 2. Tabs: substitui os 3 botões antigos por 5 novos ---
tabs_old = ('<button id="tab-diagramas" class="tab-btn ativa" onclick="mostrarAba(\'diagramas\')">Diagramas</button>\n'
            '<button id="tab-cobertura" class="tab-btn" onclick="mostrarAba(\'cobertura\')">Cobertura</button>\n'
            '<button id="tab-impossiveis" class="tab-btn" onclick="mostrarAba(\'impossiveis\')">Diagramas Impossíveis</button>')
tabs_new = ('<button id="tab-aprovados" class="tab-btn ativa" onclick="mostrarAba(\'aprovados\')">Diagramas Aprovados</button>\n'
            '<button id="tab-auditoria" class="tab-btn" onclick="mostrarAba(\'auditoria\')">Em Auditoria</button>\n'
            '<button id="tab-reprovados" class="tab-btn" onclick="mostrarAba(\'reprovados\')">Reprovados</button>\n'
            '<button id="tab-cobertura" class="tab-btn" onclick="mostrarAba(\'cobertura\')">Cobertura</button>\n'
            '<button id="tab-impossiveis" class="tab-btn" onclick="mostrarAba(\'impossiveis\')">Diagramas Impossíveis</button>')
assert content.count(tabs_old) == 1, "bloco de tabs não encontrado (verificar espaços/quebras de linha)"
content = content.replace(tabs_old, tabs_new, 1)

# --- 3. Substitui secao-diagramas inteira pela nova secao-painel + modal ---
start_marker = '<div id="secao-diagramas">'
end_marker = '<div id="secao-impossiveis" style="display:none">'
i1 = content.index(start_marker)
i2 = content.index(end_marker, i1)

secao_nova = """<div id="secao-painel">
<div class="painel-busca">
<input type="text" id="painelBuscaInput" placeholder="Filtrar por acorde... Ex: C, Am, F#7M" oninput="filtrarPainel()">
</div>
<div class="painel-resumo">
<span class="painel-chip" id="painelResumoAcordes">0 acordes</span>
<span class="painel-chip" id="painelResumoShapes">0 shapes</span>
</div>
<div class="painel-lista" id="painelLista"><p class="painel-vazio">Carregando...</p></div>
</div>

<div class="painel-modal-overlay" id="painelModalOverlay" onclick="if(event.target===this)fecharDiagramaPainel()">
<div class="painel-modal">
<h3 id="painelModalTitulo"></h3>
<div id="painelModalSvg"></div>
<div class="painel-modal-info" id="painelModalInfo"></div>
<button class="painel-modal-fechar" onclick="fecharDiagramaPainel()">Fechar</button>
</div>
</div>

"""
content = content[:i1] + secao_nova + content[i2:]

# --- 4. mostrarAba: reescreve para os 5 tabs ---
start_marker = 'function mostrarAba(aba){'
end_marker = 'async function carregarImpossiveis(){'
i1 = content.index(start_marker)
i2 = content.index(end_marker, i1)

mostrarAba_novo = """function mostrarAba(aba){
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
}

"""
content = content[:i1] + mostrarAba_novo + content[i2:]

# --- 5. Funções novas do painel + troca chamada inicial ---
call_marker = 'carregarAuditoria();'
assert content.count(call_marker) == 1, "chamada inicial carregarAuditoria() não encontrada de forma única"

funcs_novas = """const PAINEL_CACHE={};
let PAINEL_ATIVO='aprovados';
let PAINEL_LISTA_ATUAL=[];

async function carregarPainel(status){
  PAINEL_ATIVO=status;
  if(!PAINEL_CACHE[status]){
    document.getElementById('painelLista').innerHTML='<p class="painel-vazio">Carregando...</p>';
    const resp=await fetch('/painel?status='+status);
    PAINEL_CACHE[status]=await resp.json();
  }
  renderPainel();
}

function filtrarPainel(){
  renderPainel();
}

function renderPainel(){
  const data=PAINEL_CACHE[PAINEL_ATIVO];
  if(!data) return;
  const busca=document.getElementById('painelBuscaInput').value.trim().toUpperCase();
  const acordes=busca ? data.acordes.filter(function(a){return a.acorde.toUpperCase().includes(busca)}) : data.acordes;
  document.getElementById('painelResumoAcordes').className='painel-chip painel-chip-'+PAINEL_ATIVO;
  document.getElementById('painelResumoShapes').className='painel-chip painel-chip-'+PAINEL_ATIVO;
  document.getElementById('painelResumoAcordes').textContent=data.total_acordes+' acordes';
  document.getElementById('painelResumoShapes').textContent=data.total_shapes+' shapes';
  if(!acordes.length){
    document.getElementById('painelLista').innerHTML='<p class="painel-vazio">Nenhum acorde encontrado.</p>';
    PAINEL_LISTA_ATUAL=[];
    return;
  }
  document.getElementById('painelLista').innerHTML=acordes.map(function(a,ai){
    return '<div class="painel-acorde">'
      + '<div class="painel-acorde-header" onclick="togglePainelAcorde(this)">'
      + '<span class="painel-acorde-seta">\\u25b8</span>'
      + '<span class="painel-acorde-nome">'+a.acorde+'</span>'
      + '<span class="painel-acorde-count">'+a.total_shapes+' shape'+(a.total_shapes!==1?'s':'')+'</span>'
      + '</div>'
      + '<div class="painel-shapes">'+a.shapes.map(function(sh,si){
          return '<div class="painel-shape-row" onclick="abrirDiagramaPainel('+ai+','+si+')">'
            + '<span class="painel-shape-codigo">'+sh.shape+'</span>'
            + '<span class="painel-shape-info">'+infoResumoPainel(sh)+'</span>'
            + '</div>';
        }).join('')+'</div>'
      + '</div>';
  }).join('');
  PAINEL_LISTA_ATUAL=acordes;
}

function infoResumoPainel(sh){
  if(PAINEL_ATIVO==='aprovados'){
    return sh.dificuldade.rotulo+' \\u00b7 '+sh.n_fontes_confiaveis+' fonte(s)';
  }
  if(PAINEL_ATIVO==='auditoria'){
    return sh.motivo || 'Sem 2 fontes confirmando';
  }
  return (sh.motivos||[]).map(function(m){return m.codigo}).join(', ');
}

function togglePainelAcorde(header){
  const shapes=header.nextElementSibling;
  const seta=header.querySelector('.painel-acorde-seta');
  const abrindo=!shapes.classList.contains('aberto');
  shapes.classList.toggle('aberto',abrindo);
  seta.textContent=abrindo?'\\u25be':'\\u25b8';
}

function abrirDiagramaPainel(ai,si){
  const a=PAINEL_LISTA_ATUAL[ai];
  const sh=a.shapes[si];
  document.getElementById('painelModalTitulo').textContent=a.acorde;
  document.getElementById('painelModalSvg').innerHTML=gerarSVG(sh.diagrama,sh.dedos,sh.pestana);
  document.getElementById('painelModalInfo').innerHTML=infoDetalhePainel(sh);
  document.getElementById('painelModalOverlay').classList.add('aberto');
}

function infoDetalhePainel(sh){
  let h='<b>Digitação:</b> '+sh.shape+'<br><b>Dificuldade:</b> '+sh.dificuldade.rotulo+'<br>';
  if(PAINEL_ATIVO==='aprovados'){
    h+='<b>Fontes confiáveis:</b> '+sh.n_fontes_confiaveis+'<br><b>Veredito:</b> '+sh.veredito_original;
  } else if(PAINEL_ATIVO==='auditoria'){
    h+='<b>Motivo:</b> '+(sh.motivo||'-');
  } else {
    h+='<b>Veredito:</b> '+sh.veredito_original+'<br><b>Motivos:</b><br>'+(sh.motivos||[]).map(function(m){return '&bull; '+m.detalhe}).join('<br>');
  }
  return h;
}

function fecharDiagramaPainel(){
  document.getElementById('painelModalOverlay').classList.remove('aberto');
}

"""
content = content.replace(call_marker, funcs_novas + "carregarPainel('aprovados');", 1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("OK - patch aplicado. bytes:", orig_len, "->", len(content))
