import ast

with open("servidor.py") as f:
    src = f.read()

OLD_ROUTE = '''        if path == "/cobertura":
            self._send_json(gerar_relatorio_cobertura())
            return'''

NEW_ROUTE = '''        if path == "/cobertura":
            self._send_json(gerar_relatorio_cobertura())
            return

        if path == "/painel":
            status = query.get("status", ["aprovados"])[0].strip()
            if status not in ("aprovados", "auditoria", "reprovados"):
                self._send_error("status invalido: use aprovados, auditoria ou reprovados", 400)
                return
            self._send_json(gerar_painel(status))
            return'''

assert OLD_ROUTE in src, "rota /cobertura nao encontrada"
src = src.replace(OLD_ROUTE, NEW_ROUTE)

FUNC = '''
def _calcular_diagrama_ao_vivo(acorde, shape):
    """Calcula dedos/pestana/dificuldade sem gravar nada - usado para
    exibicao em SHAPES_EM_AUDITORIA e SHAPES_REPROVADOS, que nao guardam
    esses campos prontos (so SHAPES_APROVADOS guarda)."""
    from dedicacao import calcular_dedos_e_pestana
    from dificuldade import avaliar_dificuldade
    from gerador_web_dinamico import parse_acorde, parsear_inversao

    acorde_base, _baixo = parsear_inversao(acorde)
    tonica, tipo = parse_acorde(acorde_base)
    partes = [p.strip().upper() for p in shape.split(",")]
    conv = [None if p == "X" else int(p) for p in partes]
    dedos, pestana = calcular_dedos_e_pestana(conv)
    dif = avaliar_dificuldade(partes, dedos, pestana, tonica, tipo)
    return {
        "diagrama": partes,
        "dedos": dedos,
        "pestana": pestana,
        "dificuldade": dif,
    }


def gerar_painel(status):
    """Agrupa shapes por acorde, para as 3 abas do painel de auditoria.
    'aprovados' le o diagrama pronto de SHAPES_APROVADOS. 'auditoria' e
    'reprovados' calculam o diagrama ao vivo (nao gravam)."""
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    por_acorde = {}

    if status == "aprovados":
        rows = con.execute(
            "SELECT acorde, shape, dedos, pestana_casa, pestana_corda_min, "
            "pestana_corda_max, dificuldade_score, dificuldade_nivel, "
            "dificuldade_rotulo, n_fontes_confiaveis, veredito_original, "
            "regras_validacao_atendidas, regra_versao "
            "FROM SHAPES_APROVADOS ORDER BY acorde, id").fetchall()
        for (acorde, shape, dedos, p_casa, p_min, p_max, dif_s, dif_n, dif_r,
             n_f, ver, regras, regra_versao) in rows:
            partes = [p.strip().upper() for p in shape.split(",")]
            pestana = ({"casa": p_casa, "cordas": list(range(p_min, p_max + 1))}
                       if p_casa is not None else None)
            item = {
                "shape": shape,
                "diagrama": partes,
                "dedos": [int(d) for d in dedos.split(",")],
                "pestana": pestana,
                "dificuldade": {"score": dif_s, "nivel": dif_n, "rotulo": dif_r},
                "n_fontes_confiaveis": n_f,
                "veredito_original": ver,
                "regras_atendidas": regras.split(",") if regras else [],
                "regra_versao": regra_versao,
            }
            por_acorde.setdefault(acorde, []).append(item)

    elif status == "auditoria":
        rows = con.execute(
            "SELECT acorde, shape, span, traste_max, n_fontes_confiaveis, "
            "motivo, regra_versao FROM SHAPES_EM_AUDITORIA "
            "ORDER BY acorde, id").fetchall()
        for acorde, shape, span, tmax, n_f, motivo, regra_versao in rows:
            calc = _calcular_diagrama_ao_vivo(acorde, shape)
            item = {
                "shape": shape,
                "diagrama": calc["diagrama"],
                "dedos": calc["dedos"],
                "pestana": calc["pestana"],
                "dificuldade": calc["dificuldade"],
                "span": span,
                "traste_max": tmax,
                "n_fontes_confiaveis": n_f,
                "motivo": motivo,
                "regra_versao": regra_versao,
            }
            por_acorde.setdefault(acorde, []).append(item)

    else:  # reprovados
        rows = con.execute(
            "SELECT acorde, shape, codigo_regra_reprovacao, detalhe, "
            "veredito_original, span, traste_max, regra_versao "
            "FROM SHAPES_REPROVADOS ORDER BY acorde, id").fetchall()
        agrupado = {}
        for acorde, shape, cod, detalhe, ver, span, tmax, regra_versao in rows:
            chave = (acorde, shape, regra_versao)
            entry = agrupado.setdefault(chave, {
                "acorde": acorde, "shape": shape, "regra_versao": regra_versao,
                "veredito_original": ver, "span": span, "traste_max": tmax,
                "motivos": []})
            entry["motivos"].append({"codigo": cod, "detalhe": detalhe})
        for (acorde, shape, regra_versao), entry in agrupado.items():
            calc = _calcular_diagrama_ao_vivo(acorde, shape)
            item = {
                "shape": shape,
                "diagrama": calc["diagrama"],
                "dedos": calc["dedos"],
                "pestana": calc["pestana"],
                "dificuldade": calc["dificuldade"],
                "span": entry["span"],
                "traste_max": entry["traste_max"],
                "veredito_original": entry["veredito_original"],
                "motivos": entry["motivos"],
                "regra_versao": regra_versao,
            }
            por_acorde.setdefault(acorde, []).append(item)

    con.close()

    acordes = [{"acorde": a, "total_shapes": len(shapes), "shapes": shapes}
               for a, shapes in sorted(por_acorde.items())]
    return {"status": status, "total_acordes": len(acordes),
            "total_shapes": sum(a["total_shapes"] for a in acordes),
            "acordes": acordes}


'''

MARCA_FUNC = "def run(port=8000):"
assert MARCA_FUNC in src, "ponto de insercao da funcao nao encontrado"
src = src.replace(MARCA_FUNC, FUNC + MARCA_FUNC)

ast.parse(src)
with open("servidor.py", "w") as f:
    f.write(src)
print("servidor.py: endpoint /painel adicionado")
