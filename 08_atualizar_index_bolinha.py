import shutil
import datetime

CAMINHO = "index.html"

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup = f"{CAMINHO}.bak_{ts}"
shutil.copy(CAMINHO, backup)
print(f"[OK] Backup criado: {backup}")

with open(CAMINHO, "r", encoding="utf-8") as f:
    conteudo = f.read()

# ---------- 1) CSS: position:relative no card + estilo da bolinha ----------

CSS_ORIGINAL = '''.card-acorde{
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-md);
  padding:12px 14px 12px;text-align:center;box-shadow:var(--shadow-md);
  transition:transform .25s var(--ease),box-shadow .25s var(--ease);
}
.card-acorde:hover{transform:translateY(-4px);box-shadow:var(--shadow-lg)}
.card-acorde h3{font-size:15px;font-weight:600;letter-spacing:-.01em;margin-bottom:2px}'''

CSS_NOVO = '''.card-acorde{
  position:relative;
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-md);
  padding:12px 14px 12px;text-align:center;box-shadow:var(--shadow-md);
  transition:transform .25s var(--ease),box-shadow .25s var(--ease);
}
.card-acorde:hover{transform:translateY(-4px);box-shadow:var(--shadow-lg)}
.card-acorde h3{font-size:15px;font-weight:600;letter-spacing:-.01em;margin-bottom:2px}

.selo-validacao{
  position:absolute;top:9px;right:10px;width:7px;height:7px;border-radius:50%;
  box-shadow:0 0 0 2px var(--surface);
}
.selo-validacao.ok{background:#30d158}
.selo-validacao.nao{background:#ff453a}
.selo-validacao.pendente{background:#c7c7cc}'''

if CSS_ORIGINAL not in conteudo:
    raise SystemExit("[ERRO] Bloco CSS .card-acorde nao encontrado exatamente como esperado. Nada foi alterado.")
conteudo = conteudo.replace(CSS_ORIGINAL, CSS_NOVO)
print("[OK] CSS da bolinha adicionado.")

# ---------- 2) JS: funcao Diagrama monta a bolinha por shape ----------

JS_ORIGINAL = '''function Diagrama(sh,acorde,i){
  const titulo=acorde+(i>0?' (Shape '+(i+1)+')':'');
  let badge='';
  if(sh.dificuldade&&sh.dificuldade.nivel){
    const n=sh.dificuldade.nivel;
    badge='<div class="badge-dificuldade nivel-'+n+'" title="Score '+sh.dificuldade.score+'/30 - Rubrica ISMIR 2023 (UC/CFP/CFD/RHC)">Dif. '+n+'/5 - '+sh.dificuldade.rotulo+'</div>';
  }
  return `<div class="card-acorde"><h3>${titulo}</h3>${gerarSVG(sh.diagrama,sh.dedos,sh.pestana)}${badge}</div>`;
}'''

JS_NOVO = '''function Diagrama(sh,acorde,i){
  const titulo=acorde+(i>0?' (Shape '+(i+1)+')':'');
  let badge='';
  if(sh.dificuldade&&sh.dificuldade.nivel){
    const n=sh.dificuldade.nivel;
    badge='<div class="badge-dificuldade nivel-'+n+'" title="Score '+sh.dificuldade.score+'/30 - Rubrica ISMIR 2023 (UC/CFP/CFD/RHC)">Dif. '+n+'/5 - '+sh.dificuldade.rotulo+'</div>';
  }
  let selo='';
  if(sh.shape_validado===true){
    selo='<div class="selo-validacao ok" title="Validado: confirmado por 2+ fontes independentes"></div>';
  }else if(sh.shape_validado===false){
    selo='<div class="selo-validacao nao" title="Nao validado: falta confirmacao de uma 2a fonte confiavel para este shape especifico"></div>';
  }else{
    selo='<div class="selo-validacao pendente" title="Ainda nao auditado para este tipo de acorde"></div>';
  }
  return `<div class="card-acorde">${selo}<h3>${titulo}</h3>${gerarSVG(sh.diagrama,sh.dedos,sh.pestana)}${badge}</div>`;
}'''

if JS_ORIGINAL not in conteudo:
    raise SystemExit("[ERRO] Funcao Diagrama nao encontrada exatamente como esperado. Nada foi alterado nesta parte.")
conteudo = conteudo.replace(JS_ORIGINAL, JS_NOVO)
print("[OK] Funcao Diagrama() atualizada com a bolinha de validacao.")

with open(CAMINHO, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("\n[OK] index.html salvo com a bolinha de validacao por shape.")
