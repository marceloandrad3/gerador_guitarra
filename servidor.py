#!/usr/bin/env python3
"""
Servidor HTTP para o Gerador Universal de Diagramas de Acordes.
Serve index.html do diretorio ATUAL e endpoints /gerar, /auditoria, /cobertura
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

DIR_ATUAL = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR_ATUAL)

sys.path.insert(0, DIR_ATUAL)
from gerador_web_dinamico import gerar_dinamico, parse_acorde, eh_ambiguo_dim
import sqlite3


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[SERVIDOR] {self.address_string()} - {format % args}")

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_html(self, html_bytes, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(html_bytes)

    def _send_error(self, message, status=400):
        self._send_json({"erro": message}, status)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/dificuldade/definir":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                self._send_error("JSON invalido no corpo da requisicao", 400)
                return

            acorde = str(body.get("acorde", "")).strip()
            shape = str(body.get("shape", "")).strip()
            regra_versao = str(body.get("regra_versao", "")).strip()
            nivel = body.get("nivel")

            if not acorde or not shape or not regra_versao or nivel is None:
                self._send_error("Parametros obrigatorios: acorde, shape, regra_versao, nivel", 400)
                return

            from dificuldade import NIVEIS
            mapa_niveis = {n: r for (_, n, r) in NIVEIS}
            if nivel not in mapa_niveis:
                self._send_error("nivel invalido: use " + ",".join(str(n) for n in mapa_niveis), 400)
                return
            rotulo = mapa_niveis[nivel]

            con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
            cur = con.execute(
                "UPDATE SHAPES_APROVADOS SET dificuldade_nivel=?, dificuldade_rotulo=?, "
                "dificuldade_travada=1 WHERE acorde=? AND shape=? AND regra_versao=?",
                (nivel, rotulo, acorde, shape, regra_versao))
            con.commit()
            afetadas = cur.rowcount
            con.close()

            if afetadas == 0:
                self._send_error("shape nao encontrado em SHAPES_APROVADOS", 404)
                return

            self._send_json({"ok": True, "nivel": nivel, "rotulo": rotulo, "travada": True})
            return

        if path == "/shapes/aprovar_manual":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                self._send_error("JSON invalido no corpo da requisicao", 400)
                return

            acorde = str(body.get("acorde", "")).strip()
            shape = str(body.get("shape", "")).strip()
            regra_versao = str(body.get("regra_versao", "")).strip()

            if not acorde or not shape or not regra_versao:
                self._send_error("Parametros obrigatorios: acorde, shape, regra_versao", 400)
                return

            from datetime import datetime
            from dedicacao import calcular_dedos_e_pestana
            from dificuldade import avaliar_dificuldade
            from gerador_web_dinamico import parsear_inversao

            con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
            row = con.execute(
                "SELECT span, traste_max, n_fontes_confiaveis FROM SHAPES_EM_AUDITORIA "
                "WHERE acorde=? AND shape=? AND regra_versao=?",
                (acorde, shape, regra_versao)).fetchone()

            if row is None:
                con.close()
                self._send_error("shape nao encontrado em SHAPES_EM_AUDITORIA", 404)
                return

            span, tmax, n_fontes = row
            acorde_base, _baixo = parsear_inversao(acorde)
            tonica, tipo = parse_acorde(acorde_base)
            partes = [p.strip().upper() for p in shape.split(",")]
            conv = [None if p == "X" else int(p) for p in partes]
            dedos, pestana = calcular_dedos_e_pestana(conv)
            dif = avaliar_dificuldade(partes, dedos, pestana, tonica, tipo)
            dedos_str = ",".join(str(d) for d in dedos)
            p_casa = pestana["casa"] if pestana else None
            p_min = min(pestana["cordas"]) if pestana else None
            p_max = max(pestana["cordas"]) if pestana else None
            data_agora = datetime.now().isoformat(timespec="seconds")

            cur = con.execute(
                "INSERT OR IGNORE INTO SHAPES_APROVADOS "
                "(acorde, shape, regra_versao, span, traste_max, n_fontes_confiaveis, "
                "regras_validacao_atendidas, veredito_original, data, dedos, "
                "pestana_casa, pestana_corda_min, pestana_corda_max, "
                "dificuldade_score, dificuldade_nivel, dificuldade_rotulo, "
                "aprovado_manual, aprovado_manual_data) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (acorde, shape, regra_versao, span, tmax, n_fontes,
                 "aprovacao_manual_marcelo", "valido_aprovacao_manual", data_agora,
                 dedos_str, p_casa, p_min, p_max,
                 dif["score"], dif["nivel"], dif["rotulo"], 1, data_agora))

            if cur.rowcount == 0:
                con.close()
                self._send_error("shape ja existe em SHAPES_APROVADOS (conflito)", 409)
                return

            con.execute(
                "DELETE FROM SHAPES_EM_AUDITORIA WHERE acorde=? AND shape=? AND regra_versao=?",
                (acorde, shape, regra_versao))
            con.commit()
            con.close()

            self._send_json({"ok": True, "acorde": acorde, "shape": shape,
                              "movido_para": "SHAPES_APROVADOS"})
            return

        self._send_error("rota nao encontrada", 404)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/gerar":
            acorde = query.get("acorde", [""])[0].strip()
            if not acorde:
                self._send_error("Parametro 'acorde' obrigatorio", 400)
                return
            try:
                if eh_ambiguo_dim(acorde):
                    resultado = gerar_resultado_ambiguo_dim(acorde)
                else:
                    resultado = gerar_dinamico(acorde)
                    resultado = complementar_com_shapes_validados(resultado)
                resultado = remover_shapes_impossiveis(resultado)
                resultado = filtrar_pestana_dupla(resultado)
                resultado = filtrar_traste_alto(resultado)
                resultado = filtrar_shapes_rejeitados(resultado)
                self._send_json(resultado)
            except Exception as e:
                self._send_error(str(e), 500)
            return

        if path == "/auditoria":
            self._send_json(gerar_relatorio_auditoria())
            return

        if path == "/impossiveis":
            self._send_json(gerar_relatorio_impossiveis())
            return

        if path == "/cobertura":
            self._send_json(gerar_relatorio_cobertura())
            return

        if path == "/painel":
            status = query.get("status", ["aprovados"])[0].strip()
            if status not in ("aprovados", "auditoria", "reprovados", "impossiveis"):
                self._send_error("status invalido: use aprovados, auditoria, reprovados ou impossiveis", 400)
                return
            self._send_json(gerar_painel(status))
            return

        if path == "/dificuldade/niveis":
            from dificuldade import NIVEIS
            self._send_json([{"nivel": n, "rotulo": r} for (_, n, r) in NIVEIS])
            return

        if path == "/" or path == "/index.html":
            index_path = os.path.join(DIR_ATUAL, "index.html")
            if os.path.exists(index_path):
                with open(index_path, "rb") as f:
                    self._send_html(f.read())
            else:
                self._send_error(f"index.html nao encontrado em: {index_path}", 404)
            return

        self._send_error(f"Rota nao encontrada: {path}", 404)


def gerar_resultado_ambiguo_dim(acorde_digitado):
    """O simbolo de grau (\u00b0) e a letra 'o' isolada sao usados de forma
    inconsistente entre plataformas de cifra: algumas os tratam como a
    triade diminuta (3 notas) e outras como a tetrade dim7 (4 notas, mais
    comum na pratica do violao - confirmado por verificacao manual do
    usuario, musico, em 2026-08-07 para 3 tonicas distintas). Por
    transparencia, retornamos as DUAS familias separadamente e
    identificadas, em vez de escolher uma sozinhos."""
    tonica, _ = parse_acorde(acorde_digitado)

    res_dim = complementar_com_shapes_validados(gerar_dinamico(tonica + "dim"))
    res_dim7 = complementar_com_shapes_validados(gerar_dinamico(tonica + "dim7"))

    nome_dim = tonica + "dim"
    nome_dim7 = tonica + "dim7"
    aka_dim7 = res_dim7.get("tambem_conhecido_como", [])

    for d in res_dim["diagramas"]:
        d["familia"] = "dim"
        d["familia_rotulo"] = "Versao simples (3 notas)"
        d["nome_exibicao"] = nome_dim
        d["tambem_conhecido_como"] = []
    for d in res_dim7["diagramas"]:
        d["familia"] = "dim7"
        d["familia_rotulo"] = "Versao completa (4 notas)"
        d["nome_exibicao"] = nome_dim7
        d["tambem_conhecido_como"] = aka_dim7

    diagramas = res_dim["diagramas"] + res_dim7["diagramas"]

    return {
        "acorde": acorde_digitado,
        "tonica": tonica,
        "tipo": "dim|dim7",
        "ambiguidade": {
            "simbolo_digitado": acorde_digitado,
            "explicacao": (
                "Esse simbolo (\u00b0) tem dois significados, dependendo do "
                "site ou livro de cifra. Pra nao errar por voce, mostramos "
                "os dois abaixo, bem separadinhos, pra voce escolher o certo."
            ),
            "total_triade": len(res_dim["diagramas"]),
            "total_tetrade": len(res_dim7["diagramas"]),
        },
        "diagramas": diagramas,
        "tambem_conhecido_como": aka_dim7,
        "total_diagramas": len(diagramas),
    }


def remover_shapes_impossiveis(resultado):
    """Tira da resposta de /gerar os shapes fisicamente inviaveis.

    Criterio validado pelo usuario (musico) em 2026-08-07 testando em
    violao e guitarra padrao: traste 12 ou acima e' inalcancavel porque o
    corpo do instrumento bloqueia a mao. Estes shapes continuam no banco e
    seguem consultaveis na aba "Diagramas Impossiveis" (/impossiveis) -
    apenas nao sao mais oferecidos como sugestao de digitacao."""
    tonica = resultado.get("tonica", "")
    tipo = resultado.get("tipo", "")
    if not tonica:
        return resultado
    # So aparece quem esta em SHAPES_APROVADOS. Bloqueia REPROVADOS (harmonia
    # errada ou ergonomia) e EM_AUDITORIA (harmonia ok, mas <2 fontes ainda) -
    # equivalente ao comportamento antigo, onde fonte_unica tambem bloqueava.
    acorde_db = tonica + tipo
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    try:
        bloqueados = {s for (s,) in con.execute(
            "SELECT DISTINCT shape FROM SHAPES_REPROVADOS WHERE acorde = ?",
            (acorde_db,))}
        bloqueados |= {s for (s,) in con.execute(
            "SELECT DISTINCT shape FROM SHAPES_EM_AUDITORIA WHERE acorde = ?",
            (acorde_db,))}
    except sqlite3.OperationalError:
        con.close()
        return resultado
    con.close()
    if not bloqueados:
        return resultado

    antes = len(resultado.get("diagramas", []))
    resultado["diagramas"] = [
        d for d in resultado.get("diagramas", [])
        if ",".join(str(x).upper() for x in d["diagrama"]) not in bloqueados]
    removidos = antes - len(resultado["diagramas"])
    resultado["total_diagramas"] = len(resultado["diagramas"])
    if removidos:
        resultado["shapes_impossiveis_ocultos"] = removidos
    return resultado


def _tem_pestana_dupla(dedos):
    """2+ dedos diferentes cobrindo 2+ cordas cada = fisicamente impossivel.

    Uma pestana unica (apenas o dedo 1 repetido em varias cordas) e'
    normal e nao e' barrada aqui. Criterio confirmado pelo usuario
    (musico) em 2026-08-08."""
    from collections import Counter
    c = Counter(d for d in (dedos or []) if d and d > 0)
    return len([d for d, n in c.items() if n >= 2]) >= 2


def filtrar_pestana_dupla(resultado):
    """Filtro GLOBAL: remove da lista qualquer diagrama com pestana dupla,
    seja ele gerado internamente (CAGED) ou vindo de fonte externa."""
    diagramas = resultado.get("diagramas", [])
    antes = len(diagramas)
    resultado["diagramas"] = [
        d for d in diagramas if not _tem_pestana_dupla(d.get("dedos"))]
    removidos = antes - len(resultado["diagramas"])
    if removidos:
        resultado["total_diagramas"] = len(resultado["diagramas"])
        resultado["shapes_impossiveis_ocultos"] = (
            resultado.get("shapes_impossiveis_ocultos", 0) + removidos)
    return resultado


def _traste_alto(diagrama, limite=12):
    """True se algum traste pisado for >= limite (default 12)."""
    for v in (diagrama or []):
        s = str(v).upper()
        if s in ("X", "-1", "0"):
            continue
        try:
            if int(s) >= limite:
                return True
        except ValueError:
            continue
    return False


def filtrar_traste_alto(resultado):
    """Filtro GLOBAL: remove diagramas com traste >= 12."""
    diagramas = resultado.get("diagramas", [])
    antes = len(diagramas)
    resultado["diagramas"] = [
        d for d in diagramas if not _traste_alto(d.get("diagrama"))]
    removidos = antes - len(resultado["diagramas"])
    if removidos:
        resultado["total_diagramas"] = len(resultado["diagramas"])
        resultado["shapes_impossiveis_ocultos"] = (
            resultado.get("shapes_impossiveis_ocultos", 0) + removidos)
    return resultado


def gerar_relatorio_impossiveis():
    """Shapes harmonicamente corretos mas fisicamente inviaveis.

    Criterio validado pelo usuario (musico) em 2026-08-07, testando em
    violao e guitarra padrao: a partir do traste 12 o corpo do instrumento
    bloqueia o acesso da mao. Vale com ou sem pestana. Estes shapes ficam
    FORA da lista normal de diagramas, mas seguem consultaveis aqui para
    fins de auditoria e transparencia."""
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    try:
        linhas = con.execute(
            "SELECT acorde, shape, codigo_regra_reprovacao, detalhe, data "
            "FROM SHAPES_REPROVADOS "
            "WHERE codigo_regra_reprovacao IN ('traste_alto','double_barre') "
            "ORDER BY acorde, shape").fetchall()
    except sqlite3.OperationalError:
        con.close()
        return {"total": 0, "acordes": [], "erro": "tabela ainda nao criada"}
    con.close()

    por_acorde = {}
    for acorde, shape, tipo_p, detalhe, data in linhas:
        por_acorde.setdefault(acorde, []).append({
            "shape": shape, "tipo_problema": tipo_p,
            "motivo": detalhe, "data": data})

    return {
        "total": len(linhas),
        "total_acordes": len(por_acorde),
        "criterio": ("Traste 12 ou acima. Verificado pelo usuario (musico) em "
                     "violao e guitarra padrao. Vale com ou sem pestana."),
        "acordes": [{"acorde": a, "shapes": por_acorde[a]}
                    for a in sorted(por_acorde)],
    }


def gerar_relatorio_auditoria():
    """Fonte da verdade: tabela `vereditos` (regua dedutiva v2.1).

    Um shape e' avaliado por criterios DEDUTIVOS, nao por contagem de fontes:
      - harmonia: notas pertencem ao acorde, fundamental presente, terca
        presente (define a qualidade), quinta exigida so em triades ou
        quando alterada, extensao caracteristica presente.
      - executabilidade: abertura <= 4 trastes (arXiv:2409.16629).
      - alcance: traste maximo <= 15 -> acima disso e' 'valido_inacessivel'
        (harmonia correta, fora do alcance pratico), nao rejeitado.
    Fontes externas viram METADADO DE POPULARIDADE (ordenacao e cross-check),
    nao criterio de verdade. Um acorde e' validado quando nenhum shape seu
    foi rejeitado. Criterios e vereditos ficam rastreaveis nas tabelas
    `criterios` e `vereditos`."""
    REGRA = "v2.1-dedutiva"
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
    con.close()

    ROTULO = {"valido": "Valido", "valido_raro": "Valido (voicing raro)",
              "valido_inacessivel": "Valido, fora do alcance pratico",
              "rejeitado": "Rejeitado", "indeterminado": "Tipo nao mapeado"}

    linhas = []
    for acorde in sorted(vereditos):
        shapes = vereditos[acorde]
        total_shapes = sum(1 for s in shapes
                           if (acorde, s) not in impossiveis)
        shapes_validados = 0
        fontes_presentes = set()
        shapes_detalhe = []
        for shape_str in sorted(shapes):
            if (acorde, shape_str) in impossiveis:
                continue          # fora da conta: nem numerador nem denominador
            v = shapes[shape_str]
            ver = v["veredito"]
            fids = presenca.get(acorde, {}).get(shape_str, set())
            fontes_presentes |= fids
            ok = ver in ("valido", "valido_raro")
            if ok:
                shapes_validados += 1
            if ver == "rejeitado":
                motivos = [descricoes.get(x, x) for x in v["falhos"].split(",") if x]
                motivo = "Reprovado: " + "; ".join(motivos)
            elif ver == "valido_inacessivel":
                motivo = ("Harmonia correta, mas o traste %d esta' fora do alcance "
                          "pratico do braco" % v["traste_max"])
            elif ver == "valido_raro":
                motivo = "Valido pela teoria; nenhuma fonte externa publica este voicing"
            else:
                motivo = ROTULO.get(ver, ver)
            shapes_detalhe.append({
                "shape": shape_str,
                "validado": ok,
                "veredito": ver,
                "rotulo": ROTULO.get(ver, ver),
                "motivo": motivo,
                "notas": v["notas"],
                "span": v["span"],
                "traste_max": v["traste_max"],
                "criterios_falhos": [x for x in v["falhos"].split(",") if x],
                "fontes_confirmando": sorted(nome_por_id[f] for f in fids),
                "fontes_reprovando": [],
                "fontes_pendentes": [],
            })
        rejeitados = sum(1 for k, s in shapes.items()
                         if (acorde, k) not in impossiveis
                         and s["veredito"] == "rejeitado")
        inacessiveis = sum(1 for k, s in shapes.items()
                           if (acorde, k) not in impossiveis
                           and s["veredito"] == "valido_inacessivel")
        if total_shapes == 0:
            continue          # todos os shapes deste acorde eram impossiveis
        por_fonte = {nome: (fid in fontes_presentes) for fid, nome in fontes}
        linhas.append({
            "acorde": acorde,
            "por_fonte": por_fonte,
            "shapes_validados": shapes_validados,
            "total_shapes": total_shapes,
            "shapes_rejeitados": rejeitados,
            "shapes_inacessiveis": inacessiveis,
            "validado": rejeitados == 0,
            "shapes_detalhe": shapes_detalhe,
        })
    return {"regra": REGRA, "fontes": [n for _, n in fontes], "acordes": linhas}


def filtrar_shapes_rejeitados(resultado):
    """Rede de seguranca: nunca entrega shape que a auditoria rejeitou.
    O construtivo de slash e a regua sao codigos distintos; se divergirem,
    a AUDITORIA e' a verdade. Vale so para acordes com veredito gravado."""
    tipo = str(resultado.get("tipo", ""))
    if "/" not in tipo:
        return resultado
    acorde = str(resultado.get("tonica", "")) + tipo
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    try:
        rej = {",".join(x.strip().upper() for x in sh.split(","))
               for (sh,) in con.execute(
                   "SELECT DISTINCT shape FROM SHAPES_REPROVADOS WHERE acorde=? "
                   "AND regra_versao='v2.2-dedutiva'",
                   (acorde,))}
    except sqlite3.OperationalError:
        rej = set()
    con.close()
    if rej:
        resultado["diagramas"] = [
            d for d in resultado.get("diagramas", [])
            if ",".join(str(x).upper() for x in d["diagrama"]) not in rej]
    return resultado


def complementar_com_shapes_validados(resultado):
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

    # Nomes enarmonicos: dim7 (passo 3) e aug (passo 4) sao simetricos -
    # o MESMO conjunto de notas responde a varios nomes de tonica.
    # Verificado manualmente pelo usuario (musico) em 2026-08-07:
    # A dim7 (5,X,4,5,4,X) = C dim7 (X,3,4,2,4,2) = mesmas 4 notas.
    resultado["tambem_conhecido_como"] = []
    if tipo in ("dim7", "aug") and tonica:
        from gerador_web_dinamico import NOTAS
        passo = 3 if tipo == "dim7" else 4
        idx = NOTAS.index(tonica)
        resultado["tambem_conhecido_como"] = [
            NOTAS[(idx + k * passo) % 12] + tipo
            for k in range(1, 12 // passo)
        ]

    # Slash chords: auditados sob v2.2-dedutiva (criterio harmonia.baixo).
    # Leem `vereditos` direto, e nao `confirmacoes`, porque nenhuma fonte
    # externa cataloga slash chord: o schema do chords-db e' key+suffix,
    # sem campo de baixo. Nunca retorna None para shape presente no banco.
    if "/" in str(tipo):
        acorde_slash = str(tonica) + str(tipo)
        con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
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
        return resultado

    if not tonica:
        for d in resultado.get("diagramas", []):
            d["shape_validado"] = None  # slash chords sem cobertura de auditoria ainda
        return resultado

    acorde_db = tonica + tipo
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
            d["shape_validado"] = False

    resultado["diagramas"].sort(
        key=lambda d: ((d.get("dificuldade") or {}).get("nivel", 9),
                       (d.get("dificuldade") or {}).get("score", 99))
    )
    resultado["total_diagramas"] = len(resultado["diagramas"])
    return resultado


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


def _preencher_painel_reprovados(con, por_acorde, filtro_sql=""):
    """Le SHAPES_REPROVADOS (com filtro opcional) e agrupa por acorde,
    calculando o diagrama ao vivo. Reaproveitado por 'reprovados' e
    'impossiveis' (subconjunto: traste_alto/double_barre)."""
    query = ("SELECT acorde, shape, codigo_regra_reprovacao, detalhe, "
              "veredito_original, span, traste_max, regra_versao "
              "FROM SHAPES_REPROVADOS " + filtro_sql +
              " ORDER BY acorde, id")
    rows = con.execute(query).fetchall()
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


def gerar_painel(status):
    """Agrupa shapes por acorde, para as 4 abas do painel de auditoria.
    'aprovados' le o diagrama pronto de SHAPES_APROVADOS. 'auditoria',
    'reprovados' e 'impossiveis' calculam o diagrama ao vivo (nao gravam)."""
    con = sqlite3.connect(os.path.join(DIR_ATUAL, "auditoria.db"))
    por_acorde = {}

    if status == "aprovados":
        rows = con.execute(
            "SELECT acorde, shape, dedos, pestana_casa, pestana_corda_min, "
            "pestana_corda_max, dificuldade_score, dificuldade_nivel, "
            "dificuldade_rotulo, dificuldade_travada, n_fontes_confiaveis, veredito_original, "
            "regras_validacao_atendidas, regra_versao "
            "FROM SHAPES_APROVADOS ORDER BY acorde, id").fetchall()
        for (acorde, shape, dedos, p_casa, p_min, p_max, dif_s, dif_n, dif_r, dif_trav,
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
                "dificuldade_travada": bool(dif_trav),
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

    elif status == "reprovados":
        _preencher_painel_reprovados(con, por_acorde)

    else:  # impossiveis
        _preencher_painel_reprovados(
            con, por_acorde,
            "WHERE codigo_regra_reprovacao IN ('traste_alto','double_barre')")

    con.close()

    acordes = [{"acorde": a, "total_shapes": len(shapes), "shapes": shapes}
               for a, shapes in sorted(por_acorde.items())]
    return {"status": status, "total_acordes": len(acordes),
            "total_shapes": sum(a["total_shapes"] for a in acordes),
            "acordes": acordes}


def run(port=8000):
    print(f"=" * 60)
    print(f" GERADOR DE ACORDES - SERVIDOR")
    print(f"=" * 60)
    print(f" Diretorio de trabalho: {DIR_ATUAL}")
    print(f" index.html esperado em: {os.path.join(DIR_ATUAL, 'index.html')}")
    print(f" Endpoint: http://localhost:{port}/gerar?acorde=C")
    print(f" Frontend: http://localhost:{port}/")
    print(f"=" * 60)
    server = HTTPServer(("", port), Handler)
    print(f" Servidor rodando na porta {port}...")
    print(f" Pressione Ctrl+C para parar.")
    print(f"=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n Servidor encerrado.")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run(port)
