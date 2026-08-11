import shutil
import datetime

CAMINHO = "servidor.py"

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup = f"{CAMINHO}.bak_{ts}"
shutil.copy(CAMINHO, backup)
print(f"[OK] Backup criado: {backup}")

with open(CAMINHO, "r", encoding="utf-8") as f:
    conteudo = f.read()

ORIGINAL = '''def gerar_relatorio_auditoria():
    """Le o banco (schema N-fontes, com granularidade de confiabilidade
    por shape+fonte) e calcula validacao RIGOROSA:
    - um shape e' validado quando >=2 fontes independentes confirmam
      exatamente o mesmo diagrama E essas confirmacoes tem confiavel=1
      (aprovadas pela verificacao de teoria musical). Uma confirmacao
      marcada confiavel=0 para aquele shape especifico NAO conta -
      precisa de uma 3a fonte confiavel pra aquele shape validar.
    - o acorde so recebe o carimbo VALIDADO quando TODOS os shapes
      distintos registrados para ele estao validados. Um unico shape
      nao confiavel ou ainda nao verificado derruba o carimbo do
      acorde inteiro - nao existe "quase validado"."""
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    cur = con.execute("SELECT id, nome FROM FONTES ORDER BY id")
    fontes = cur.fetchall()

    cur = con.execute(
        "SELECT acorde, shape, fonte_id, confiavel FROM CONFIRMACOES"
    )
    dados = {}
    for acorde, shape, fonte_id, confiavel in cur.fetchall():
        info = dados.setdefault(acorde, {}).setdefault(shape, {
            "confiaveis": set(), "nao_confiaveis": set(), "pendentes": set()
        })
        if confiavel == 1:
            info["confiaveis"].add(fonte_id)
        elif confiavel == 0:
            info["nao_confiaveis"].add(fonte_id)
        else:
            info["pendentes"].add(fonte_id)
    con.close()

    linhas = []
    for acorde in sorted(dados):
        shapes = dados[acorde]
        total_shapes = len(shapes)
        shapes_validados = 0
        fontes_presentes = set()
        for info in shapes.values():
            fontes_presentes |= (info["confiaveis"] | info["nao_confiaveis"]
                                  | info["pendentes"])
            if len(info["confiaveis"]) >= 2:
                shapes_validados += 1
        por_fonte = {nome: (fid in fontes_presentes) for fid, nome in fontes}
        linhas.append({
            "acorde": acorde,
            "por_fonte": por_fonte,
            "total_shapes": total_shapes,
            "shapes_validados": shapes_validados,
            "validado": total_shapes > 0 and shapes_validados == total_shapes,
        })
    return {"fontes": [nome for _, nome in fontes], "acordes": linhas}'''

NOVO = '''def gerar_relatorio_auditoria():
    """Le o banco (schema N-fontes, com granularidade de confiabilidade
    por shape+fonte) e calcula validacao RIGOROSA:
    - um shape e' validado quando >=2 fontes independentes confirmam
      exatamente o mesmo diagrama E essas confirmacoes tem confiavel=1
      (aprovadas pela verificacao de teoria musical). Uma confirmacao
      marcada confiavel=0 para aquele shape especifico NAO conta -
      precisa de uma 3a fonte confiavel pra aquele shape validar.
    - o acorde so recebe o carimbo VALIDADO quando TODOS os shapes
      distintos registrados para ele estao validados. Um unico shape
      nao confiavel ou ainda nao verificado derruba o carimbo do
      acorde inteiro - nao existe "quase validado".
    Tambem retorna o detalhe shape-a-shape (shapes_detalhe) com o motivo
    exato de cada reprovacao, pra' UI expandir a arvore de auditoria."""
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    cur = con.execute("SELECT id, nome FROM FONTES ORDER BY id")
    fontes = cur.fetchall()
    nome_por_id = {fid: nome for fid, nome in fontes}

    cur = con.execute(
        "SELECT acorde, shape, fonte_id, confiavel, motivo_invalidacao "
        "FROM CONFIRMACOES"
    )
    dados = {}
    for acorde, shape, fonte_id, confiavel, motivo in cur.fetchall():
        info = dados.setdefault(acorde, {}).setdefault(shape, {
            "confiaveis": set(), "nao_confiaveis": set(), "pendentes": set(),
            "motivos": {}
        })
        if confiavel == 1:
            info["confiaveis"].add(fonte_id)
        elif confiavel == 0:
            info["nao_confiaveis"].add(fonte_id)
            if motivo:
                info["motivos"][fonte_id] = motivo
        else:
            info["pendentes"].add(fonte_id)
    con.close()

    linhas = []
    for acorde in sorted(dados):
        shapes = dados[acorde]
        total_shapes = len(shapes)
        shapes_validados = 0
        fontes_presentes = set()
        shapes_detalhe = []
        for shape_str, info in sorted(shapes.items()):
            fontes_presentes |= (info["confiaveis"] | info["nao_confiaveis"]
                                  | info["pendentes"])
            shape_validado = len(info["confiaveis"]) >= 2
            if shape_validado:
                shapes_validados += 1
            shapes_detalhe.append({
                "shape": shape_str,
                "validado": shape_validado,
                "fontes_confirmando": sorted(
                    nome_por_id[fid] for fid in info["confiaveis"]
                ),
                "fontes_reprovando": [
                    {"fonte": nome_por_id[fid],
                     "motivo": info["motivos"].get(fid, "nao especificado")}
                    for fid in sorted(info["nao_confiaveis"])
                ],
                "fontes_pendentes": sorted(
                    nome_por_id[fid] for fid in info["pendentes"]
                ),
            })
        por_fonte = {nome: (fid in fontes_presentes) for fid, nome in fontes}
        linhas.append({
            "acorde": acorde,
            "por_fonte": por_fonte,
            "total_shapes": total_shapes,
            "shapes_validados": shapes_validados,
            "validado": total_shapes > 0 and shapes_validados == total_shapes,
            "shapes_detalhe": shapes_detalhe,
        })
    return {"fontes": [nome for _, nome in fontes], "acordes": linhas}'''

if ORIGINAL not in conteudo:
    raise SystemExit("[ERRO] Bloco de gerar_relatorio_auditoria nao encontrado exatamente como esperado (pode ja ter sido alterado de outra forma). Nada foi mudado.")
conteudo = conteudo.replace(ORIGINAL, NOVO)

with open(CAMINHO, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("[OK] gerar_relatorio_auditoria() agora retorna shapes_detalhe com motivo de reprovacao.")
