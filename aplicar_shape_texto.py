#!/usr/bin/env python3
import shutil

ARQ = "index.html"
shutil.copy(ARQ, ARQ + ".bak_antes_shape_texto")

with open(ARQ, "r", encoding="utf-8") as f:
    conteudo = f.read()

old = '''  return `<div class="card-acorde">${selo}<h3>${titulo}</h3>${aka}${gerarSVG(sh.diagrama,sh.dedos,sh.pestana)}${badge}</div>`;'''

new = '''  const shapeTexto = '<div class="shape-texto-diagrama" style="font-family:ui-monospace,Menlo,monospace;font-size:12px;color:#6e6e73;text-align:center;margin-top:4px;">'+sh.diagrama.join(',')+'</div>';
  return `<div class="card-acorde">${selo}<h3>${titulo}</h3>${aka}${gerarSVG(sh.diagrama,sh.dedos,sh.pestana)}${shapeTexto}${badge}</div>`;'''

if old not in conteudo:
    print("ERRO: trecho original nao encontrado. Nenhuma alteracao feita.")
else:
    conteudo = conteudo.replace(old, new)
    with open(ARQ, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print("OK: shape em texto adicionado ao card. Backup salvo em index.html.bak_antes_shape_texto")
