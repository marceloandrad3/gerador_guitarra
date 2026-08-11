import ast

with open("ingerir_gco.py") as f:
    src = f.read()

OLD_IMPORTS = '''from regua_v21 import avaliar, REGRA
from dedicacao import calcular_dedos_e_pestana'''

NEW_IMPORTS = '''from regua_v21 import avaliar, REGRA
from dedicacao import calcular_dedos_e_pestana
from dificuldade import avaliar_dificuldade
from gerador_web_dinamico import parse_acorde, parsear_inversao'''

assert OLD_IMPORTS in src, "bloco imports nao encontrado"
src = src.replace(OLD_IMPORTS, NEW_IMPORTS)

OLD = '''        n_f = cur.execute(
            "SELECT COUNT(DISTINCT fonte_id) FROM CONFIRMACOES "
            "WHERE acorde=? AND shape=? AND confiavel=1", (acorde, shape)).fetchone()[0]
        if n_f >= 2:
            cur.execute(
                "INSERT INTO SHAPES_APROVADOS (acorde, shape, regra_versao, span, "
                "traste_max, n_fontes_confiaveis, regras_validacao_atendidas, "
                "veredito_original, data) VALUES (?,?,?,?,?,?,?,?,?)",
                (acorde, shape, REGRA, span, tmax, n_f,
                 "harmonia_completa,min_2_fontes_confiaveis", ver, DATA))
            aprov_novos += 1
            estado = f"GRAVADO APROVADO ({n_f} fontes)"'''

NEW = '''        n_f = cur.execute(
            "SELECT COUNT(DISTINCT fonte_id) FROM CONFIRMACOES "
            "WHERE acorde=? AND shape=? AND confiavel=1", (acorde, shape)).fetchone()[0]
        if n_f >= 2:
            acorde_base, _baixo = parsear_inversao(acorde)
            tonica, tipo_p = parse_acorde(acorde_base)
            conv = [None if p == "X" else int(p) for p in parse(shape)] \\
                if False else [None if p.strip().upper() == "X" else int(p.strip())
                                for p in shape.split(",")]
            dedos, pestana = calcular_dedos_e_pestana(conv)
            partes = [p.strip().upper() for p in shape.split(",")]
            dif = avaliar_dificuldade(partes, dedos, pestana, tonica, tipo_p)
            dedos_str = ",".join(str(d) for d in dedos)
            p_casa = pestana["casa"] if pestana else None
            p_min = min(pestana["cordas"]) if pestana else None
            p_max = max(pestana["cordas"]) if pestana else None

            cur.execute(
                "INSERT INTO SHAPES_APROVADOS (acorde, shape, regra_versao, span, "
                "traste_max, n_fontes_confiaveis, regras_validacao_atendidas, "
                "veredito_original, data, dedos, pestana_casa, pestana_corda_min, "
                "pestana_corda_max, dificuldade_score, dificuldade_nivel, "
                "dificuldade_rotulo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (acorde, shape, REGRA, span, tmax, n_f,
                 "harmonia_completa,min_2_fontes_confiaveis", ver, DATA,
                 dedos_str, p_casa, p_min, p_max,
                 dif["score"], dif["nivel"], dif["rotulo"]))
            aprov_novos += 1
            estado = f"GRAVADO APROVADO ({n_f} fontes)"'''

assert OLD in src, "bloco INSERT SHAPES_APROVADOS nao encontrado"
src = src.replace(OLD, NEW)

ast.parse(src)
with open("ingerir_gco.py", "w") as f:
    f.write(src)
print("ingerir_gco.py: agora popula dedos/pestana/dificuldade ao gravar em SHAPES_APROVADOS")
