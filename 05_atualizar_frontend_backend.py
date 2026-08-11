#!/usr/bin/env python3
"""Atualiza servidor.py (nova logica de auditoria) e index.html
(tabela dinamica por fonte) para o schema novo de auditoria.db."""
import re
import shutil
import datetime

def backup(path):
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = f"{path}.bak_{stamp}"
    shutil.copy(path, dest)
    print(f"[OK] Backup: {dest}")

# ---------------- servidor.py ----------------
backup("servidor.py")
with open("servidor.py") as f:
    src = f.read()

nova_funcao = '''def gerar_relatorio_auditoria():
    """Le o banco (schema N-fontes) e calcula validacao por shape:
    um shape e' validado quando >=2 fontes independentes confirmam
    exatamente o mesmo diagrama. O acorde e' validado quando tem
    pelo menos 1 shape validado."""
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    cur = con.execute("SELECT id, nome FROM FONTES ORDER BY id")
    fontes = cur.fetchall()

    cur = con.execute("SELECT acorde, shape, fonte_id FROM CONFIRMACOES")
    dados = {}
    for acorde, shape, fonte_id in cur.fetchall():
        dados.setdefault(acorde, {}).setdefault(shape, set()).add(fonte_id)
    con.close()

    linhas = []
    for acorde in sorted(dados):
        shapes = dados[acorde]
        total_shapes = len(shapes)
        validados = sum(1 for s in shapes.values() if len(s) >= 2)
        fontes_presentes = set()
        for s in shapes.values():
            fontes_presentes |= s
        por_fonte = {nome: (fid in fontes_presentes) for fid, nome in fontes}
        linhas.append({
            "acorde": acorde,
            "por_fonte": por_fonte,
            "total_shapes": total_shapes,
            "shapes_validados": validados,
            "validado": validados > 0,
        })
    return {"fontes": [nome for _, nome in fontes], "acordes": linhas}
'''

padrao = re.compile(r"def gerar_relatorio_auditoria\(\):.*?(?=\ndef run\(port=8000\):)", re.DOTALL)
if not padrao.search(src):
    raise SystemExit("[ERRO] Nao encontrei a funcao gerar_relatorio_auditoria em servidor.py — abortando sem alterar nada.")
src = padrao.sub(nova_funcao + "\n", src)

with open("servidor.py", "w") as f:
    f.write(src)
print("[OK] servidor.py atualizado.")

# ---------------- index.html ----------------
backup("index.html")
with open("index.html") as f:
    html = f.read()

velho_thead = '<thead><tr><th>Acorde</th><th>Nosso gerador</th><th>JGuitar</th><th>Caged</th><th>Validado</th></tr></thead>'
novo_thead = '<thead><tr id="audHead"></tr></thead>'
if velho_thead not in html:
    raise SystemExit("[ERRO] Nao encontrei o <thead> esperado em index.html — abortando sem alterar nada.")
html = html.replace(velho_thead, novo_thead)

velho_js = '''async function carregarAuditoria(){
  const resp = await fetch('/auditoria');
  const data = await resp.json();
  AUD_DADOS = data.acordes;
  renderAuditoria();
}
function renderAuditoria(){
  const ok = AUD_DADOS.filter(a=>a.validado).length;
  const nao = AUD_DADOS.length - ok;
  const pct = AUD_DADOS.length ? (ok/AUD_DADOS.length*100) : 0;
  document.getElementById('audOk').textContent = '\\u2714 '+ok+' validados';
  document.getElementById('audNao').textContent = '\\u2718 '+nao+' n\\u00e3o validados';
  document.getElementById('audPct').textContent = pct.toFixed(1)+'% de 100%';
  const linhas = AUD_DADOS.filter(a => AUD_FILTRO==='todos' || (AUD_FILTRO==='ok' ? a.validado : !a.validado));
  const tick = v => v ? '<span class="tick-ok">\\u2714</span>' : '<span class="tick-x">\\u2718</span>';
  document.getElementById('audBody').innerHTML = linhas.map(a =>
    '<tr><td><b>'+a.acorde+'</b></td><td>'+tick(a.nosso)+'</td><td>'+tick(a.jguitar)+'</td><td>'+tick(a.caged)+'</td><td>'+tick(a.validado)+'</td></tr>'
  ).join('');
}'''

# Fallback: encontrar via regex, tolerando pequenas diferencas de aspas/acentos.
if velho_js not in html:
    padrao_js = re.compile(r"async function carregarAuditoria\(\)\{.*?\n\}\n", re.DOTALL)
    m = padrao_js.search(html)
    if not m:
        raise SystemExit("[ERRO] Nao encontrei o bloco JS de auditoria em index.html — abortando sem alterar nada.")
    # tambem precisa pegar a funcao renderAuditoria seguinte
    padrao_js2 = re.compile(r"async function carregarAuditoria\(\)\{.*?\nfunction renderAuditoria\(\)\{.*?\n\}\n", re.DOTALL)
    m2 = padrao_js2.search(html)
    alvo = m2.group(0) if m2 else m.group(0)
else:
    alvo = velho_js

novo_js = '''var AUD_FONTES = [];
async function carregarAuditoria(){
  const resp = await fetch('/auditoria');
  const data = await resp.json();
  AUD_FONTES = data.fontes;
  AUD_DADOS = data.acordes;
  renderCabecalhoAuditoria();
  renderAuditoria();
}
function renderCabecalhoAuditoria(){
  let html = '<th>Acorde</th>';
  AUD_FONTES.forEach(f => { html += '<th>'+f+'</th>'; });
  html += '<th>Shapes validados</th><th>Validado</th>';
  document.getElementById('audHead').innerHTML = html;
}
function renderAuditoria(){
  const ok = AUD_DADOS.filter(a=>a.validado).length;
  const nao = AUD_DADOS.length - ok;
  const pct = AUD_DADOS.length ? (ok/AUD_DADOS.length*100) : 0;
  document.getElementById('audOk').textContent = '\\u2714 '+ok+' validados';
  document.getElementById('audNao').textContent = '\\u2718 '+nao+' n\\u00e3o validados';
  document.getElementById('audPct').textContent = pct.toFixed(1)+'% de 100%';
  const linhas = AUD_DADOS.filter(a => AUD_FILTRO==='todos' || (AUD_FILTRO==='ok' ? a.validado : !a.validado));
  const tick = v => v ? '<span class="tick-ok">\\u2714</span>' : '<span class="tick-x">\\u2718</span>';
  document.getElementById('audBody').innerHTML = linhas.map(a => {
    let cols = '<td><b>'+a.acorde+'</b></td>';
    AUD_FONTES.forEach(f => { cols += '<td>'+tick(a.por_fonte[f])+'</td>'; });
    cols += '<td>'+a.shapes_validados+'/'+a.total_shapes+'</td>';
    cols += '<td>'+tick(a.validado)+'</td>';
    return '<tr>'+cols+'</tr>';
  }).join('');
}'''

html = html.replace(alvo, novo_js + "\n")

with open("index.html", "w") as f:
    f.write(html)
print("[OK] index.html atualizado.")
print("[OK] Tudo pronto. Reinicie o servidor: python3 servidor.py")
