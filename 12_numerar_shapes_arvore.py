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

NOVO = '''function renderArvoreShapes(a){
  const itens = (a.shapes_detalhe||[]).map(function(sh, idx){
    const cls = sh.validado ? 'ok' : 'nao';
    const rotulo = 'Shape '+(idx+1);
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
print("[OK] renderArvoreShapes() agora numera 'Shape 1', 'Shape 2'...")

with open(CAMINHO, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("\n[OK] index.html salvo.")
