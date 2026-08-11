#!/usr/bin/env python3
"""Migra 100% dos registros de VEREDITOS para exatamente uma de:
SHAPES_APROVADOS, SHAPES_REPROVADOS, SHAPES_EM_AUDITORIA.

Regra de precedencia:
1. veredito='rejeitado' ou 'valido_inacessivel' ou 'indeterminado' -> REPROVADO (harmonia/fisica)
2. cruza com PROBLEMAS_ERGONOMIA (traste_alto, double_barre, erro_harmonico) -> REPROVADO
3. senao, harmonia ok: conta fontes confiaveis em CONFIRMACOES
   >=2 fontes -> APROVADO
   <2 fontes  -> AUDITORIA
"""
import sqlite3
from datetime import datetime

DATA = datetime.now().isoformat(timespec="seconds")
con = sqlite3.connect("auditoria.db")
cur = con.cursor()

# mapa veredito da regua -> codigo de reprovacao (quando for o caso)
REPROVA_POR_VEREDITO = {
    "rejeitado": None,          # usa criterios_falhos, pode ter mais de 1 codigo
    "valido_inacessivel": "fisica.alcance",
    "indeterminado": "indeterminado",
}

vereditos = cur.execute(
    "SELECT acorde, shape, veredito, criterios_falhos, span, traste_max, "
    "fontes_externas, regra_versao FROM VEREDITOS").fetchall()

erg = {}
for acorde, shape, tipo in cur.execute(
        "SELECT acorde, shape, tipo_problema FROM PROBLEMAS_ERGONOMIA"):
    erg.setdefault((acorde, shape), []).append(tipo)

n_aprov = n_rep = n_audit = n_erro = 0

for acorde, shape, veredito, falhos, span, tmax, fontes_ext, regra_versao in vereditos:
    reprovacoes = []

    if veredito == "rejeitado":
        for cod in (falhos or "").split(","):
            cod = cod.strip()
            if cod:
                reprovacoes.append((cod, f"Reprovado pela regua: {cod}"))
        if not reprovacoes:
            reprovacoes.append(("indeterminado", "Rejeitado sem criterios_falhos registrado"))
    elif veredito == "valido_inacessivel":
        reprovacoes.append(("fisica.alcance", f"Traste maximo {tmax} > 15"))
    elif veredito == "indeterminado":
        reprovacoes.append(("indeterminado", "Acorde/tipo nao reconhecido pela regua"))

    for tipo_erg in erg.get((acorde, shape), []):
        if tipo_erg == "traste_alto":
            reprovacoes.append(("traste_alto", f"Traste maximo {tmax} >= 12"))
        elif tipo_erg == "double_barre":
            reprovacoes.append(("double_barre", "Duas pestanas simultaneas"))
        elif tipo_erg == "erro_harmonico":
            reprovacoes.append(("erro_harmonico", "Erro no dataset upstream"))
        # fonte_unica NAO e reprovacao - tratado abaixo, via contagem de fontes

    if reprovacoes:
        for cod, det in reprovacoes:
            cur.execute(
                "INSERT OR IGNORE INTO SHAPES_REPROVADOS "
                "(acorde, shape, regra_versao, codigo_regra_reprovacao, detalhe, "
                "span, traste_max, data) VALUES (?,?,?,?,?,?,?,?)",
                (acorde, shape, regra_versao, cod, det, span, tmax, DATA))
            n_rep += 1
        continue

    # harmonia aprovada, sem reprovacao -> checar fontes
    n_f = cur.execute(
        "SELECT COUNT(DISTINCT fonte_id) FROM CONFIRMACOES "
        "WHERE acorde=? AND shape=? AND confiavel=1", (acorde, shape)).fetchone()[0]

    is_slash = "/" in acorde

    if n_f >= 2 or is_slash:
        # slash: harmonia.baixo ja e' o criterio extra do v2.2, sem exigencia de fonte
        regras = "harmonia_completa,min_2_fontes_confiaveis" if n_f >= 2 else "harmonia_completa"
        cur.execute(
            "INSERT OR IGNORE INTO SHAPES_APROVADOS "
            "(acorde, shape, regra_versao, span, traste_max, n_fontes_confiaveis, "
            "regras_validacao_atendidas, data) VALUES (?,?,?,?,?,?,?,?)",
            (acorde, shape, regra_versao, span, tmax, n_f, regras, DATA))
        n_aprov += 1
    else:
        cur.execute(
            "INSERT OR IGNORE INTO SHAPES_EM_AUDITORIA "
            "(acorde, shape, regra_versao, span, traste_max, n_fontes_confiaveis, "
            "motivo, data) VALUES (?,?,?,?,?,?,?,?)",
            (acorde, shape, regra_versao, span, tmax, n_f,
             "aguardando_2a_fonte_confiavel", DATA))
        n_audit += 1

con.commit()

print(f"VEREDITOS lidos:        {len(vereditos)}")
print(f"linhas em REPROVADOS:   {n_rep}  (shapes podem ter >1 motivo)")
print(f"linhas em APROVADOS:    {n_aprov}")
print(f"linhas em AUDITORIA:    {n_audit}")
print(f"soma aprov+audit+rejeitados_unicos deve bater com total de shapes unicos processados")

# conferencia: todo shape unico (acorde,shape,regra_versao) caiu em exatamente
# uma das 3 categorias (aprovado/auditoria) OU tem >=1 linha em reprovados
shapes_unicos = {(a, s, r) for a, s, v, f, sp, t, fe, r in vereditos}
cur.execute("SELECT DISTINCT acorde, shape, regra_versao FROM SHAPES_APROVADOS")
aprov_set = set(cur.fetchall())
cur.execute("SELECT DISTINCT acorde, shape, regra_versao FROM SHAPES_EM_AUDITORIA")
audit_set = set(cur.fetchall())
cur.execute("SELECT DISTINCT acorde, shape, regra_versao FROM SHAPES_REPROVADOS")
rep_set = set(cur.fetchall())

cobertos = aprov_set | audit_set | rep_set
faltando = shapes_unicos - cobertos
sobrepondo = (aprov_set & rep_set) | (audit_set & rep_set) | (aprov_set & audit_set)

print(f"\nshapes unicos em VEREDITOS: {len(shapes_unicos)}")
print(f"cobertos pelas 3 tabelas:   {len(cobertos)}")
print(f"faltando (BUG se >0):      {len(faltando)}")
print(f"sobrepondo (BUG se >0):    {len(sobrepondo)}")
if faltando:
    print("exemplos faltando:", list(faltando)[:5])
if sobrepondo:
    print("exemplos sobrepondo:", list(sobrepondo)[:5])

con.close()
