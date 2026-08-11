#!/usr/bin/env python3
import re, shutil, datetime

def backup(path):
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = f"{path}.bak_{stamp}"
    shutil.copy(path, dest)
    print(f"[OK] Backup: {dest}")

# ==================== servidor.py ====================
backup("servidor.py")
with open("servidor.py") as f:
    src = f.read()

velha_rota = '''        if path == "/auditoria":
            self._send_json(gerar_relatorio_auditoria())
            return
'''
nova_rota = velha_rota + '''
        if path == "/cobertura":
            self._send_json(gerar_relatorio_cobertura())
            return
'''
if velha_rota not in src:
    raise SystemExit("[ERRO] Nao encontrei a rota /auditoria em servidor.py — abortando.")
src = src.replace(velha_rota, nova_rota)

nova_funcao_cobertura = '''
# Padrao de referencia: uniao das qualidades de acorde usadas pelos
# principais dicionarios abertos (chords-db/tombatossals no GitHub e
# guitar-chord.org). A notacao de acordes e aberta (alteracoes como
# 7#5b9 sao combinaveis quase sem limite), entao nao existe uma lista
# "100% completa" no sentido literal - este e o padrao pratico que
# dicionarios de acordes serios convergem para.
TIPOS_REFERENCIA = {
    "major": "Maior", "minor": "Menor", "dim": "Diminuto (triade)",
    "dim7": "Diminuto 7", "sus": "Suspenso (generico)", "sus2": "Sus2",
    "sus4": "Sus4", "sus2sus4": "Sus2+Sus4", "7sus4": "7sus4",
    "alt": "Alterado (generico)", "aug": "Aumentado",
    "5": "Power chord (5)", "6": "Sexta", "69": "6/9",
    "7": "Dominante 7", "7b5": "7 b5", "aug7": "7 Aumentado (7#5)",
    "9": "Nona dominante", "9b5": "9 b5", "aug9": "9 Aumentado",
    "7b9": "7 b9", "7#9": "7 #9", "11": "Decima-primeira (11)",
    "9#11": "9 #11", "13": "Decima-terceira (13)",
    "maj7": "Maior com 7M", "maj7b5": "7M b5", "maj7#5": "7M #5",
    "maj7sus2": "7M sus2", "maj9": "Nona maior", "maj11": "11 maior",
    "maj13": "13 maior", "m6": "Menor 6", "m69": "Menor 6/9",
    "m7": "Menor 7", "m7b5": "Meio-diminuto (m7b5)", "m9": "Menor 9",
    "m11": "Menor 11", "mmaj7": "Menor com 7M", "mmaj7b5": "Menor 7M b5",
    "mmaj9": "Menor 9M", "mmaj11": "Menor 11M", "add9": "Add9",
    "madd9": "Menor add9", "add11": "Add11",
}

TIPOS_SUPORTADOS_MAP = {
    "major": "", "minor": "m", "7": "7", "m7": "m7", "maj7": "7M",
    "mmaj7": "m7M", "dim": "dim", "dim7": "dim7", "aug": "aug",
    "sus2": "sus2", "sus4": "sus4", "6": "6", "m6": "m6", "9": "9",
    "add9": "add9",
}


def gerar_relatorio_cobertura():
    """Compara os tipos de acorde que o gerador suporta com o padrao de
    referencia (uniao chords-db + guitar-chord.org). Retorna contagens
    reais e a lista do que falta, com o m7b5 marcado como prioridade
    (e o tipo mais comum entre os ausentes - meio-diminuto, usado o
    tempo todo em ii-V-I de jazz e tambem em pop/rock)."""
    faltando = []
    for suf, label in TIPOS_REFERENCIA.items():
        if suf not in TIPOS_SUPORTADOS_MAP:
            faltando.append({
                "suffix": suf,
                "label": label,
                "prioritario": suf == "m7b5",
            })
    faltando.sort(key=lambda x: (not x["prioritario"], x["label"]))

    total_ref = len(TIPOS_REFERENCIA)
    total_sup = len(TIPOS_SUPORTADOS_MAP)
    return {
        "total_referencia": total_ref,
        "total_suportados": total_sup,
        "percentual": round(100 * total_sup / total_ref, 1),
        "tipos_suportados": sorted(TIPOS_SUPORTADOS_MAP.keys()),
        "tipos_faltando": faltando,
    }

'''

if "def run(port=8000):" not in src:
    raise SystemExit("[ERRO] Nao encontrei def run(port=8000) em servidor.py — abortando.")
src = src.replace("def run(port=8000):", nova_funcao_cobertura + "def run(port=8000):")

with open("servidor.py", "w") as f:
    f.write(src)
print("[OK] servidor.py atualizado (rota /cobertura + funcao).")

# ==================== index.html ====================
backup("index.html")
with open("index.html") as f:
    html = f.read()

if ".tick-x{color:#c7c7cc;font-weight:700}" not in html:
    raise SystemExit("[ERRO] Nao encontrei a regra .tick-x em index.html — abortando.")
html = html.replace(
    ".tick-x{color:#c7c7cc;font-weight:700}",
    ".tick-x{color:#ff3b30;font-weight:700}"
)

css_cobertura = '''
/* ---------- Cobertura ---------- */
.cov-topo{max-width:900px;margin:0 auto;padding:0 20px}
.cov-resumo{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0 28px}
.cov-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-md);padding:18px 22px;box-shadow:var(--shadow-sm);flex:1;min-width:160px}
.cov-card .cov-num{font-size:28px;font-weight:700;letter-spacing:-.02em}
.cov-card .cov-label{font-size:13px;color:var(--text-secondary);margin-top:2px}
.cov-lista{max-width:900px;margin:0 auto 40px;padding:0 20px}
.cov-item{display:flex;justify-content:space-between;align-items:center;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px 16px;margin-bottom:8px;box-shadow:var(--shadow-sm)}
.cov-item.prioritario{border-color:#ff9f0a;background:rgba(255,159,10,.06)}
.cov-item .cov-nome{font-weight:600;font-size:14px}
.cov-item .cov-suffix{font-size:12px;color:var(--text-secondary);margin-left:8px}
.cov-badge-prioridade{font-size:11px;font-weight:700;color:#c1690a;background:rgba(255,159,10,.18);padding:3px 10px;border-radius:12px}
'''
html = html.replace("</style>", css_cobertura + "</style>")

html = html.replace(
    '<button id="tab-auditoria" class="tab-btn" onclick="mostrarAba(\'auditoria\')">Auditoria</button>',
    '<button id="tab-auditoria" class="tab-btn" onclick="mostrarAba(\'auditoria\')">Auditoria</button>\n<button id="tab-cobertura" class="tab-btn" onclick="mostrarAba(\'cobertura\')">Cobertura</button>'
)

marcador_fim_auditoria = '''<div class="aud-tabela-wrap">
<table class="aud">
<thead><tr id="audHead"></tr></thead>
<tbody id="audBody"></tbody>
</table>
</div>
</div>'''
secao_cobertura = marcador_fim_auditoria + '''

<div id="secao-cobertura" style="display:none">
<div class="cov-topo">
<h2 style="text-align:center;font-size:20px;font-weight:650;margin-bottom:4px">Cobertura de tipos de acorde</h2>
<p style="text-align:center;color:var(--text-secondary);font-size:13px;max-width:560px;margin:8px auto 0">
Padrao de referencia = uniao das qualidades de acorde usadas pelos principais dicionarios abertos (chords-db, guitar-chord.org). A notacao musical e aberta, entao nao existe um "100%" absoluto - este e o alvo pratico que dicionarios serios adotam.
</p>
<div class="cov-resumo">
<div class="cov-card"><div class="cov-num" id="covSuportados">-</div><div class="cov-label">tipos suportados</div></div>
<div class="cov-card"><div class="cov-num" id="covReferencia">-</div><div class="cov-label">tipos no padrao de referencia</div></div>
<div class="cov-card"><div class="cov-num" id="covPct">-</div><div class="cov-label">cobertura</div></div>
</div>
</div>
<div class="cov-lista" id="covLista"></div>
</div>'''
if marcador_fim_auditoria not in html:
    raise SystemExit("[ERRO] Nao encontrei o fechamento da secao-auditoria em index.html — abortando.")
html = html.replace(marcador_fim_auditoria, secao_cobertura)

velho_mostraraba = '''function mostrarAba(aba){
  document.getElementById('secao-diagramas').style.display = aba==='diagramas' ? '' : 'none';
  document.getElementById('secao-auditoria').style.display = aba==='auditoria' ? '' : 'none';
  document.getElementById('tab-diagramas').classList.toggle('ativa', aba==='diagramas');
  document.getElementById('tab-auditoria').classList.toggle('ativa', aba==='auditoria');
  if(aba==='auditoria') carregarAuditoria();
}'''
novo_mostraraba = '''function mostrarAba(aba){
  document.getElementById('secao-diagramas').style.display = aba==='diagramas' ? '' : 'none';
  document.getElementById('secao-auditoria').style.display = aba==='auditoria' ? '' : 'none';
  document.getElementById('secao-cobertura').style.display = aba==='cobertura' ? '' : 'none';
  document.getElementById('tab-diagramas').classList.toggle('ativa', aba==='diagramas');
  document.getElementById('tab-auditoria').classList.toggle('ativa', aba==='auditoria');
  document.getElementById('tab-cobertura').classList.toggle('ativa', aba==='cobertura');
  if(aba==='auditoria') carregarAuditoria();
  if(aba==='cobertura') carregarCobertura();
}
async function carregarCobertura(){
  const resp = await fetch('/cobertura');
  const data = await resp.json();
  document.getElementById('covSuportados').textContent = data.total_suportados;
  document.getElementById('covReferencia').textContent = data.total_referencia;
  document.getElementById('covPct').textContent = data.percentual + '%';
  document.getElementById('covLista').innerHTML = data.tipos_faltando.map(t =>
    '<div class="cov-item' + (t.prioritario ? ' prioritario' : '') + '">' +
      '<span><span class="cov-nome">' + t.label + '</span><span class="cov-suffix">(' + t.suffix + ')</span></span>' +
      (t.prioritario ? '<span class="cov-badge-prioridade">Prioridade alta</span>' : '') +
    '</div>'
  ).join('');
}'''
if velho_mostraraba not in html:
    raise SystemExit("[ERRO] Nao encontrei a funcao mostrarAba em index.html — abortando.")
html = html.replace(velho_mostraraba, novo_mostraraba)

with open("index.html", "w") as f:
    f.write(html)
print("[OK] index.html atualizado (X vermelho + aba Cobertura).")
print("[OK] Tudo pronto. Reinicie o servidor.")
