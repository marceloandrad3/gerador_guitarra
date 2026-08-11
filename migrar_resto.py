import ast

# ============ 1. servidor.py: gerar_relatorio_auditoria ============
with open("servidor.py") as f:
    src = f.read()

OLD = '''    REGRA = "v2.1-dedutiva"
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    fontes = con.execute("SELECT id, nome FROM FONTES ORDER BY id").fetchall()
    nome_por_id = {fid: nome for fid, nome in fontes}

    presenca = {}
    for acorde, shape, fonte_id in con.execute(
            "SELECT acorde, shape, fonte_id FROM CONFIRMACOES"):
        presenca.setdefault(acorde, {}).setdefault(shape, set()).add(fonte_id)

    vereditos = {}
    for acorde, shape, ver, falhos, notas, span, tmax, nf in con.execute(
            "SELECT acorde, shape, veredito, criterios_falhos, notas_apuradas, "
            "span, traste_max, fontes_externas FROM VEREDITOS "
            "WHERE regra_versao = ?", (REGRA,)):
        vereditos.setdefault(acorde, {})[shape] = {
            "veredito": ver, "falhos": falhos or "", "notas": notas or "",
            "span": span, "traste_max": tmax, "fontes_externas": nf}

    descricoes = {cod: desc for cod, desc in con.execute(
        "SELECT codigo, descricao FROM CRITERIOS WHERE regra_versao = ?", (REGRA,))}

    # Shapes fisicamente impossiveis (traste >= 12, validado pelo usuario
    # musico em 2026-08-07) saem INTEIRAMENTE da conta: nao entram no
    # numerador nem no denominador, porque nao sao oferecidos ao usuario.
    # Seguem consultaveis na aba "Diagramas Impossiveis" (/impossiveis).
    try:
        impossiveis = {(a, s) for a, s in con.execute(
            "SELECT acorde, shape FROM PROBLEMAS_ERGONOMIA")}
    except sqlite3.OperationalError:
        impossiveis = set()
    con.close()'''

NEW = '''    REGRA = "v2.1-dedutiva"
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    fontes = con.execute("SELECT id, nome FROM FONTES ORDER BY id").fetchall()
    nome_por_id = {fid: nome for fid, nome in fontes}

    presenca = {}
    for acorde, shape, fonte_id in con.execute(
            "SELECT acorde, shape, fonte_id FROM CONFIRMACOES"):
        presenca.setdefault(acorde, {}).setdefault(shape, set()).add(fonte_id)

    # Reconstroi o veredito consultando as 3 tabelas de shape: aprovado,
    # reprovado (com motivo/regra) ou em auditoria (harmonia ok, <2 fontes).
    vereditos = {}
    REGRAS_DESC = {cod: desc for cod, desc in con.execute(
        "SELECT codigo, descricao FROM REGRAS_DE_REPROVACAO")}
    for acorde, shape, ver, span, tmax in con.execute(
            "SELECT acorde, shape, veredito_original, span, traste_max "
            "FROM SHAPES_APROVADOS WHERE regra_versao = ?", (REGRA,)):
        vereditos.setdefault(acorde, {})[shape] = {
            "veredito": ver or "valido", "falhos": "", "notas": "",
            "span": span, "traste_max": tmax, "fontes_externas": 0}
    for acorde, shape, span, tmax in con.execute(
            "SELECT acorde, shape, span, traste_max "
            "FROM SHAPES_EM_AUDITORIA WHERE regra_versao = ?", (REGRA,)):
        vereditos.setdefault(acorde, {})[shape] = {
            "veredito": "valido_raro", "falhos": "", "notas": "",
            "span": span, "traste_max": tmax, "fontes_externas": 0}
    for acorde, shape, ver, cod, span, tmax in con.execute(
            "SELECT acorde, shape, veredito_original, codigo_regra_reprovacao, "
            "span, traste_max FROM SHAPES_REPROVADOS WHERE regra_versao = ?", (REGRA,)):
        entry = vereditos.setdefault(acorde, {}).setdefault(shape, {
            "veredito": ver or "rejeitado", "falhos": "", "notas": "",
            "span": span, "traste_max": tmax, "fontes_externas": 0})
        entry["falhos"] = (entry["falhos"] + "," + cod).strip(",")

    descricoes = REGRAS_DESC

    # Shapes bloqueados por ergonomia (traste_alto/double_barre) saem
    # INTEIRAMENTE da conta: nao entram no numerador nem no denominador,
    # porque nao sao oferecidos ao usuario. Consultaveis em /impossiveis.
    try:
        impossiveis = {(a, s) for a, s, cod in con.execute(
            "SELECT acorde, shape, codigo_regra_reprovacao FROM SHAPES_REPROVADOS")
            if cod in ("traste_alto", "double_barre")}
    except sqlite3.OperationalError:
        impossiveis = set()
    con.close()'''

assert OLD in src, "bloco auditoria nao encontrado"
src = src.replace(OLD, NEW)
ast.parse(src)
with open("servidor.py", "w") as f:
    f.write(src)
print("servidor.py: gerar_relatorio_auditoria atualizado")

