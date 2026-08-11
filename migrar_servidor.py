#!/usr/bin/env python3
"""Reescreve as 5 funcoes de servidor.py que leem tabelas antigas para
lerem das 3 novas (SHAPES_APROVADOS, SHAPES_REPROVADOS, SHAPES_EM_AUDITORIA).
Valida sintaxe ANTES de sobrescrever o arquivo real."""
import ast

with open("servidor.py") as f:
    src = f.read()

# --- 1. remover_shapes_impossiveis: PROBLEMAS_ERGONOMIA -> SHAPES_REPROVADOS ---
OLD_1 = '''    acorde_db = tonica + tipo
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    try:
        impossiveis = {s for (s,) in con.execute(
            "SELECT shape FROM PROBLEMAS_ERGONOMIA WHERE acorde = ?",
            (acorde_db,))}
    except sqlite3.OperationalError:
        con.close()
        return resultado
    con.close()
    if not impossiveis:
        return resultado

    antes = len(resultado.get("diagramas", []))
    resultado["diagramas"] = [
        d for d in resultado.get("diagramas", [])
        if ",".join(str(x).upper() for x in d["diagrama"]) not in impossiveis]
    removidos = antes - len(resultado["diagramas"])
    resultado["total_diagramas"] = len(resultado["diagramas"])
    if removidos:
        resultado["shapes_impossiveis_ocultos"] = removidos
    return resultado'''

NEW_1 = '''    acorde_db = tonica + tipo
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    try:
        reprovados = {s for (s,) in con.execute(
            "SELECT DISTINCT shape FROM SHAPES_REPROVADOS WHERE acorde = ?",
            (acorde_db,))}
    except sqlite3.OperationalError:
        con.close()
        return resultado
    con.close()
    if not reprovados:
        return resultado

    antes = len(resultado.get("diagramas", []))
    resultado["diagramas"] = [
        d for d in resultado.get("diagramas", [])
        if ",".join(str(x).upper() for x in d["diagrama"]) not in reprovados]
    removidos = antes - len(resultado["diagramas"])
    resultado["total_diagramas"] = len(resultado["diagramas"])
    if removidos:
        resultado["shapes_impossiveis_ocultos"] = removidos
    return resultado'''

assert OLD_1 in src, "bloco 1 nao encontrado"
src = src.replace(OLD_1, NEW_1)

# --- 2. gerar_relatorio_impossiveis: PROBLEMAS_ERGONOMIA -> SHAPES_REPROVADOS
#         (so os motivos ergonomicos, nao harmonia) ---
OLD_2 = '''    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    try:
        linhas = con.execute(
            "SELECT acorde, shape, tipo_problema, detalhe, data "
            "FROM PROBLEMAS_ERGONOMIA ORDER BY acorde, shape").fetchall()
    except sqlite3.OperationalError:
        con.close()
        return {"total": 0, "acordes": [], "erro": "tabela ainda nao criada"}
    con.close()'''

NEW_2 = '''    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    try:
        linhas = con.execute(
            "SELECT acorde, shape, codigo_regra_reprovacao, detalhe, data "
            "FROM SHAPES_REPROVADOS "
            "WHERE codigo_regra_reprovacao IN ('traste_alto','double_barre') "
            "ORDER BY acorde, shape").fetchall()
    except sqlite3.OperationalError:
        con.close()
        return {"total": 0, "acordes": [], "erro": "tabela ainda nao criada"}
    con.close()'''

assert OLD_2 in src, "bloco 2 nao encontrado"
src = src.replace(OLD_2, NEW_2)

# --- 3. filtrar_shapes_rejeitados (slash): VEREDITOS -> SHAPES_REPROVADOS ---
OLD_3 = '''    try:
        rej = {",".join(x.strip().upper() for x in sh.split(","))
               for (sh,) in con.execute(
                   "SELECT shape FROM VEREDITOS WHERE acorde=? "
                   "AND regra_versao='v2.2-dedutiva' AND veredito='rejeitado'",
                   (acorde,))}
    except sqlite3.OperationalError:
        rej = set()'''

NEW_3 = '''    try:
        rej = {",".join(x.strip().upper() for x in sh.split(","))
               for (sh,) in con.execute(
                   "SELECT DISTINCT shape FROM SHAPES_REPROVADOS WHERE acorde=? "
                   "AND regra_versao='v2.2-dedutiva'",
                   (acorde,))}
    except sqlite3.OperationalError:
        rej = set()'''

assert OLD_3 in src, "bloco 3 nao encontrado"
src = src.replace(OLD_3, NEW_3)

# --- 4. complementar_com_shapes_validados (slash): VEREDITOS -> SHAPES_APROVADOS/REPROVADOS ---
OLD_4 = '''        con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
        try:
            vs = {",".join(x.strip().upper() for x in sh.split(",")): v
                  for sh, v in con.execute(
                      "SELECT shape, veredito FROM VEREDITOS "
                      "WHERE acorde = ? AND regra_versao = 'v2.2-dedutiva'",
                      (acorde_slash,))}
        except sqlite3.OperationalError:
            vs = {}
        con.close()
        for d in resultado.get("diagramas", []):
            chave = ",".join(str(x).upper() for x in d["diagrama"])
            ver = vs.get(chave)
            d["veredito"] = ver
            d["shape_validado"] = (ver.startswith("valido")) if ver else None
        return resultado'''

NEW_4 = '''        con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
        try:
            vs = {",".join(x.strip().upper() for x in sh.split(",")): v
                  for sh, v in con.execute(
                      "SELECT shape, veredito_original FROM SHAPES_APROVADOS "
                      "WHERE acorde = ? AND regra_versao = 'v2.2-dedutiva'",
                      (acorde_slash,))}
        except sqlite3.OperationalError:
            vs = {}
        con.close()
        for d in resultado.get("diagramas", []):
            chave = ",".join(str(x).upper() for x in d["diagrama"])
            ver = vs.get(chave)
            d["veredito"] = ver
            d["shape_validado"] = True if ver else None
        return resultado'''

assert OLD_4 in src, "bloco 4 nao encontrado"
src = src.replace(OLD_4, NEW_4)

# --- 5. complementar_com_shapes_validados (normal): CONFIRMACOES ao vivo -> SHAPES_APROVADOS/AUDITORIA ---
OLD_5 = '''    acorde_db = tonica + tipo
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
            d["shape_validado"] = False'''

NEW_5 = '''    acorde_db = tonica + tipo
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    try:
        aprovados = {s.strip().upper(): (nf, veredito_original) for s, nf, veredito_original in con.execute(
            "SELECT shape, n_fontes_confiaveis, veredito_original FROM SHAPES_APROVADOS WHERE acorde = ?",
            (acorde_db,))}
        em_auditoria = {s.strip().upper() for (s,) in con.execute(
            "SELECT shape FROM SHAPES_EM_AUDITORIA WHERE acorde = ?",
            (acorde_db,))}
    except sqlite3.OperationalError:
        con.close()
        for d in resultado.get("diagramas", []):
            d["shape_validado"] = None
        return resultado
    con.close()

    status_por_shape = {}
    for shape_str, (nf, ver) in aprovados.items():
        chave = ",".join(p.strip().upper() for p in shape_str.split(","))
        status_por_shape[chave] = {"aprovado": True, "n_fontes": nf, "veredito": ver}
    for shape_str in em_auditoria:
        chave = ",".join(p.strip().upper() for p in shape_str.split(","))
        status_por_shape.setdefault(chave, {"aprovado": False, "n_fontes": 0, "veredito": None})

    from dedicacao import calcular_dedos_e_pestana
    from dificuldade import avaliar_dificuldade

    ja_temos = {
        tuple(str(x).upper() for x in d["diagrama"])
        for d in resultado["diagramas"]
    }

    for shape_chave, info in status_por_shape.items():
        if not info["aprovado"]:
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
        elif info["aprovado"]:
            d["shape_validado"] = True
            d["veredito"] = info["veredito"]
        else:
            d["shape_validado"] = False'''

assert OLD_5 in src, "bloco 5 nao encontrado"
src = src.replace(OLD_5, NEW_5)

# validar sintaxe ANTES de gravar
ast.parse(src)
print("sintaxe ok, todos os 5 blocos encontrados e substituidos")

with open("servidor.py", "w") as f:
    f.write(src)
print("servidor.py atualizado")
