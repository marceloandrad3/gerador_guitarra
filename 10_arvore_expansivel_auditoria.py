import shutil
import datetime

CAMINHO = "index.html"

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup = f"{CAMINHO}.bak_{ts}"
shutil.copy(CAMINHO, backup)
print(f"[OK] Backup criado: {backup}")

with open(CAMINHO, "r", encoding="utf-8") as f:
    conteudo = f.read()

# ---------- 1) CSS da arvore ----------

CSS_ANCORA = ".ver-mais-container{text-align:center;margin:32px 0}"

CSS_ARVORE = '''.linha-shapes-detalhe{background:#fafafa}
.linha-shapes-detalhe td{padding:0!important}
.arvore-shapes{padding:10px 14px 14px 42px;font-size:12.5px}
.arvore-item{
  display:flex;align-items:center;gap:8px;padding:5px 0;
  border-bottom:1px solid var(--border);
}
.arvore-item:last-child{border-bottom:none}
.arvore-ponto{width:7px;height:7px;border-radius:50%;flex:0 0 auto}
.arvore-ponto.ok{background:#30d158}
.arvore-ponto.nao{background:#ff453a}
.arvore-shape-codigo{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#1d1d1f;min-width:150px}
.arvore-motivo{color:#6e6e73;flex:1}
.arvore-motivo b{color:#1d1d1f;font-weight:600}
.toggle-arvore{cursor:pointer;user-select:none;display:inline-block;width:14px;text-align:center;color:#a1a1a6;font-size:11px}

''' + CSS_ANCORA

if CSS_ANCORA not in conteudo:
    raise SystemExit("[ERRO] Ancora de CSS nao encontrada. Nada foi alterado.")
conteudo = conteudo.replace(CSS_ANCORA, CSS_ARVORE, 1)
print("[OK] CSS da arvore adicionado.")

# ---------- 2) JS: renderAuditoria com arvore expansivel ----------

JS_ORIGINAL = '''function renderAuditoria(){
  const ok = AUD_DADOS.filter(a=>a.validado).length;
  const nao = AUD_DADOS.length - ok;
  const pct = AUD_DADOS.length ? (ok/AUD_DADOS.length*100) : 0;
  document.getElementById('audOk').textContent = '\\u2714 '+ok+' validados';
  document.getElementById('audNao').textContent = '\\u2718 '+nao+' n\\u00e3o validados';
  document.getElementById('audPct').textContent = pct.toFixed(1)+'% de 100%';
  const linhas = AUD_DADOS.filter(a => {
    const passaFiltro = AUD_FILTRO==='todos' || (AUD_FILTRO==='ok' ? a.validado : !a.validado);
    const passaBusca = !AUD_BUSCA || a.acorde.toUpperCase().includes(AUD_BUSCA);
    return passaFiltro && passaBusca;
  });
  const tick = v => v ? '<span class="tick-ok">\\u2714</span>' : '<span class="tick-x">\\u2718</span>';
  document.getElementById('audBody').innerHTML = linhas.map(a => {
    let cols = '<td class="clicavel" data-modo="unico"><b>'+a.acorde+'</b></td>';
    AUD_FONTES.forEach(f => { cols += '<td>'+tick(a.por_fonte[f])+'</td>'; });
    cols += '<td class="clicavel" data-modo="todos">'+a.shapes_validados+'/'+a.total_shapes+'</td>';
    cols += '<td>'+tick(a.validado)+'</td>';
    return '<tr data-acorde="'+a.acorde+'">'+cols+'</tr>';
  }).join('');
}
document.getElementById('audBody').addEventListener('click', function(e){
  const td = e.target.closest('td.clicavel');
  if(!td) return;
  const tr = td.closest('tr');
  const acorde = tr.dataset.acorde;
  const modo = td.dataset.modo;
  selecionarAcorde(acorde, modo==='todos');
});'''

JS_NOVO = '''function motivoResumido(shapeDet){
  if(shapeDet.validado) return 'Validado';
  if(shapeDet.fontes_reprovando && shapeDet.fontes_reprovando.length){
    return shapeDet.fontes_reprovando.map(function(r){
      return '<b>'+r.fonte+'</b>: '+r.motivo;
    }).join(' &middot; ');
  }
  const nConf = (shapeDet.fontes_confirmando||[]).length;
  if(nConf < 2){
    const fontesTxt = nConf ? shapeDet.fontes_confirmando.join(', ') : 'nenhuma';
    return 'Falta 2\\u00aa fonte independente confirmando este shape (confirmado s\\u00f3 por: <b>'+fontesTxt+'</b>)';
  }
  return 'N\\u00e3o validado';
}
function renderArvoreShapes(a){
  const itens = (a.shapes_detalhe||[]).map(function(sh){
    const cls = sh.validado ? 'ok' : 'nao';
    return '<div class="arvore-item">'
      + '<span class="arvore-ponto '+cls+'"></span>'
      + '<span class="arvore-shape-codigo">'+sh.shape+'</span>'
      + '<span class="arvore-motivo">'+motivoResumido(sh)+'</span>'
      + '</div>';
  }).join('');
  return '<div class="arvore-shapes">'+itens+'</div>';
}
function renderAuditoria(){
  const ok = AUD_DADOS.filter(a=>a.validado).length;
  const nao = AUD_DADOS.length - ok;
  const pct = AUD_DADOS.length ? (ok/AUD_DADOS.length*100) : 0;
  document.getElementById('audOk').textContent = '\\u2714 '+ok+' validados';
  document.getElementById('audNao').textContent = '\\u2718 '+nao+' n\\u00e3o validados';
  document.getElementById('audPct').textContent = pct.toFixed(1)+'% de 100%';
  const linhas = AUD_DADOS.filter(a => {
    const passaFiltro = AUD_FILTRO==='todos' || (AUD_FILTRO==='ok' ? a.validado : !a.validado);
    const passaBusca = !AUD_BUSCA || a.acorde.toUpperCase().includes(AUD_BUSCA);
    return passaFiltro && passaBusca;
  });
  const tick = v => v ? '<span class="tick-ok">\\u2714</span>' : '<span class="tick-x">\\u2718</span>';
  document.getElementById('audBody').innerHTML = linhas.map(a => {
    // reprovado comeca aberto (mostra o motivo direto), aprovado comeca fechado
    const aberto = !a.validado;
    const seta = '<span class="toggle-arvore">'+(aberto?'\\u25be':'\\u25b8')+'</span>';
    let cols = '<td class="clicavel" data-modo="unico">'+seta+' <b>'+a.acorde+'</b></td>';
    AUD_FONTES.forEach(f => { cols += '<td>'+tick(a.por_fonte[f])+'</td>'; });
    cols += '<td class="clicavel" data-modo="todos">'+a.shapes_validados+'/'+a.total_shapes+'</td>';
    cols += '<td>'+tick(a.validado)+'</td>';
    let html = '<tr data-acorde="'+a.acorde+'" class="linha-acorde">'+cols+'</tr>';
    html += '<tr class="linha-shapes-detalhe" data-acorde-detalhe="'+a.acorde+'" style="display:'+(aberto?'table-row':'none')+'">'
      + '<td colspan="'+(AUD_FONTES.length+3)+'">'+renderArvoreShapes(a)+'</td></tr>';
    return html;
  }).join('');
}
document.getElementById('audBody').addEventListener('click', function(e){
  const setaEl = e.target.closest('.toggle-arvore');
  if(setaEl){
    const tr = setaEl.closest('tr');
    const acorde = tr.dataset.acorde;
    const linhaDetalhe = document.querySelector('tr[data-acorde-detalhe="'+acorde+'"]');
    if(linhaDetalhe){
      const abrindo = linhaDetalhe.style.display === 'none';
      linhaDetalhe.style.display = abrindo ? 'table-row' : 'none';
      setaEl.textContent = abrindo ? '\\u25be' : '\\u25b8';
    }
    return;
  }
  const td = e.target.closest('td.clicavel');
  if(!td) return;
  const tr = td.closest('tr');
  if(!tr.dataset.acorde) return;
  const acorde = tr.dataset.acorde;
  const modo = td.dataset.modo;
  selecionarAcorde(acorde, modo==='todos');
});'''

if JS_ORIGINAL not in conteudo:
    raise SystemExit("[ERRO] Funcao renderAuditoria (bloco original) nao encontrada exatamente como esperado. Nada foi alterado nesta parte.")
conteudo = conteudo.replace(JS_ORIGINAL, JS_NOVO)
print("[OK] renderAuditoria() atualizada com arvore expansivel (reprovado aberto, aprovado fechado).")

with open(CAMINHO, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("\n[OK] index.html salvo com a arvore de auditoria.")
