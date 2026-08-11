import shutil
import datetime

CAMINHO = "index.html"

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup = f"{CAMINHO}.bak_{ts}"
shutil.copy(CAMINHO, backup)
print(f"[OK] Backup criado: {backup}")

with open(CAMINHO, "r", encoding="utf-8") as f:
    conteudo = f.read()

ORIGINAL = '''function renderArvoreShapes(a){
  const itens = (a.shapes_detalhe||[]).map(function(sh){
    const cls = sh.validado ? 'ok' : 'nao';
    return '<div class="arvore-item">'
      + '<span class="arvore-ponto '+cls+'"></span>'
      + '<span class="arvore-shape-codigo">'+sh.shape+'</span>'
      + '<span class="arvore-motivo">'+motivoResumido(sh)+'</span>'
      + '</div>';
  }).join('');
  return '<div class="arvore-shapes">'+itens+'</div>';
}'''

NOVO = '''function rotuloPosicaoShape(shapeStr){
  const partes = shapeStr.split(',').map(function(p){ return p.trim().toUpperCase(); });
  const trastes = partes
    .filter(function(p){ return p !== 'X'; })
    .map(function(p){ return parseInt(p, 10); })
    .filter(function(n){ return !isNaN(n); });
  if(!trastes.length) return '';
  const minTraste = Math.min.apply(null, trastes);
  const maxTraste = Math.max.apply(null, trastes);
  if(maxTraste === 0) return 'Aberto';
  if(minTraste === 0) return 'Aberto (c/ pestana)';
  return (minTraste===1?'1\\u00aa':minTraste+'\\u00aa') + ' casa';
}
function renderArvoreShapes(a){
  const itens = (a.shapes_detalhe||[]).map(function(sh){
    const cls = sh.validado ? 'ok' : 'nao';
    const rotulo = rotuloPosicaoShape(sh.shape);
    return '<div class="arvore-item">'
      + '<span class="arvore-ponto '+cls+'"></span>'
      + '<span class="arvore-shape-posicao">'+rotulo+'</span>'
      + '<span class="arvore-shape-codigo">'+sh.shape+'</span>'
      + '<span class="arvore-motivo">'+motivoResumido(sh)+'</span>'
      + '</div>';
  }).join('');
  return '<div class="arvore-shapes">'+itens+'</div>';
}'''

if ORIGINAL not in conteudo:
    raise SystemExit("[ERRO] Funcao renderArvoreShapes nao encontrada exatamente como esperado. Nada foi alterado.")
conteudo = conteudo.replace(ORIGINAL, NOVO)
print("[OK] renderArvoreShapes() atualizada com rotulo de posicao.")

CSS_ORIGINAL = '.arvore-shape-codigo{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#1d1d1f;min-width:150px}'
CSS_NOVO = '''.arvore-shape-posicao{
  font-size:11px;font-weight:600;color:#6e6e73;min-width:82px;flex:0 0 auto;
  background:#eef0f2;border-radius:8px;padding:2px 8px;text-align:center;
}
.arvore-shape-codigo{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#1d1d1f;min-width:150px}'''

if CSS_ORIGINAL not in conteudo:
    raise SystemExit("[ERRO] CSS .arvore-shape-codigo nao encontrado. Funcao JS ja foi atualizada, mas o CSS do rotulo nao foi aplicado.")
conteudo = conteudo.replace(CSS_ORIGINAL, CSS_NOVO)
print("[OK] CSS do rotulo de posicao adicionado.")

with open(CAMINHO, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("\n[OK] index.html salvo.")
