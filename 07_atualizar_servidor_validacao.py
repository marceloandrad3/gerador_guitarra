import shutil
import datetime

CAMINHO = "servidor.py"

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup = f"{CAMINHO}.bak_{ts}"
shutil.copy(CAMINHO, backup)
print(f"[OK] Backup criado: {backup}")

with open(CAMINHO, "r", encoding="utf-8") as f:
    conteudo = f.read()

# ---------- 1) gerar_relatorio_auditoria: regra rigorosa (tudo ou nada) ----------

ORIGINAL_AUDITORIA = '''def gerar_relatorio_auditoria():
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
    return {"fontes": [nome for _, nome in fontes], "acordes": linhas}'''

NOVO_AUDITORIA = '''def gerar_relatorio_auditoria():
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

if ORIGINAL_AUDITORIA not in conteudo:
    raise SystemExit("[ERRO] Bloco de gerar_relatorio_auditoria nao encontrado exatamente como esperado. Nada foi alterado.")
conteudo = conteudo.replace(ORIGINAL_AUDITORIA, NOVO_AUDITORIA)
print("[OK] gerar_relatorio_auditoria() atualizada (regra tudo-ou-nada).")

# ---------- 2) complementar_com_shapes_validados: marca confiavel por shape exibido ----------

MARCADOR_INICIO = "def complementar_com_shapes_validados(resultado):"
MARCADOR_FIM = 'resultado["total_diagramas"] = len(resultado["diagramas"])\n    return resultado'

idx_inicio = conteudo.find(MARCADOR_INICIO)
idx_fim = conteudo.find(MARCADOR_FIM, idx_inicio)
if idx_inicio == -1 or idx_fim == -1:
    raise SystemExit("[ERRO] Nao encontrei os limites de complementar_com_shapes_validados. Nada foi alterado nesta parte.")
idx_fim_completo = idx_fim + len(MARCADOR_FIM)

NOVA_FUNCAO = '''def complementar_com_shapes_validados(resultado):
    """Adiciona shapes que fontes externas (JGuitar, chords_db) confirmam
    para este acorde mas que o nosso algoritmo CAGED nao gera sozinho, e
    marca em TODO diagrama exibido (gerado internamente ou complementado)
    o status real de validacao do shape especifico, consultando o banco
    de auditoria. So conta como validado (>=2 fontes) quando essas fontes
    tem confiavel=1 - uma fonte marcada nao-confiavel para aquele shape
    nao conta, precisa de uma 3a fonte confiavel. Nunca assume que um
    shape gerado pelo nosso proprio algoritmo e' automaticamente confiavel."""
    tonica = resultado.get("tonica", "")
    tipo = resultado.get("tipo", "")
    if not tonica or "/" in str(tipo):
        for d in resultado.get("diagramas", []):
            d["shape_validado"] = None  # slash chords sem cobertura de auditoria ainda
        return resultado

    acorde_db = tonica + tipo
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    try:
        cur = con.execute(
            "SELECT shape, fonte_id, confiavel FROM CONFIRMACOES WHERE acorde = ?",
            (acorde_db,)
        )
        linhas_brutas = cur.fetchall()
    except sqlite3.OperationalError:
        con.close()
        for d in resultado.get("diagramas", []):
            d["shape_validado"] = None
        return resultado
    con.close()

    status_por_shape = {}
    for shape_str, fonte_id, confiavel in linhas_brutas:
        chave = ",".join(p.strip().upper() for p in shape_str.split(","))
        info = status_por_shape.setdefault(chave, {"confiaveis": set(), "nao_confiaveis": set()})
        if confiavel == 1:
            info["confiaveis"].add(fonte_id)
        elif confiavel == 0:
            info["nao_confiaveis"].add(fonte_id)

    from dedicacao import calcular_dedos_e_pestana
    from dificuldade import avaliar_dificuldade

    ja_temos = {
        tuple(str(x).upper() for x in d["diagrama"])
        for d in resultado["diagramas"]
    }

    for shape_chave, info in status_por_shape.items():
        if len(info["confiaveis"]) < 2:
            continue
        partes = tuple(shape_chave.split(","))
        if partes in ja_temos or len(partes) != 6:
            continue
        diagrama = list(partes)
        conv = [None if v == "X" else int(v) for v in diagrama]
        dedos, pestana = calcular_dedos_e_pestana(conv)
        dif = avaliar_dificuldade(diagrama, dedos, pestana, tonica, tipo)
        resultado["diagramas"].append({
            "diagrama": diagrama,
            "dedos": dedos,
            "pestana": pestana,
            "score": dif["score"],
            "dificuldade": dif,
            "fonte_externa": True,
        })
        ja_temos.add(partes)

    for d in resultado["diagramas"]:
        chave = ",".join(str(x).upper() for x in d["diagrama"])
        info = status_por_shape.get(chave)
        if info is None:
            d["shape_validado"] = None
        elif len(info["confiaveis"]) >= 2:
            d["shape_validado"] = True
        else:
            d["shape_validado"] = False

    resultado["diagramas"].sort(
        key=lambda d: ((d.get("dificuldade") or {}).get("nivel", 9),
                       (d.get("dificuldade") or {}).get("score", 99))
    )
    resultado["total_diagramas"] = len(resultado["diagramas"])
    return resultado'''

conteudo = conteudo[:idx_inicio] + NOVA_FUNCAO + conteudo[idx_fim_completo:]
print("[OK] complementar_com_shapes_validados() atualizada (marca shape_validado por diagrama).")

with open(CAMINHO, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("\n[OK] servidor.py salvo com as duas correcoes.")
