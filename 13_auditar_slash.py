"""Auditoria de slash chords - regra v2.2-dedutiva.

Estende a v2.1 (provada, 1811/1811) com UM criterio novo, sem alterar nenhum
dos 7 existentes:

  harmonia.baixo -- a nota mais grave soando deve ser exatamente a nota
                    apos a barra.
  Fonte: Wikipedia 'Slash chord' (o baixo e' indicado apos a barra);
  piano.org (a nota do baixo e' sempre o som mais grave; se ela sobe acima,
  deixa de ser slash chord).

Alem disso, o conjunto de notas permitidas passa a ser notas(X) U {Y}, porque
em X/Y o Y faz parte da ESPECIFICACAO do acorde, nao e' nota estranha.
  Fonte: appliedguitartheory (o baixo pode ser qualquer nota, nao precisa ser
  nota do acorde); piano.org (baixo fora do acorde = slash "verdadeiro",
  harmonia mais rica, nao erro).

Vereditos novos, para separar os dois objetos harmonicos distintos:
  valido_inversao       -- baixo E' nota do acorde (1a/2a/3a inversao)
  valido_baixo_alterado -- baixo NAO e' nota do acorde (policorde/baixo pedal)
Ambos podem virar *_raro se fontes_externas=0. Nota: chords-db tem schema
key+suffix, SEM campo de baixo, logo nao confirma slash chord algum.
"""
import sqlite3, sys
from regua_v21 import (NOTAS, CORDAS_MIDI, TIPOS, SEM_TERCA, TRIADES,
                       EXTENSAO, QUINTA_ALTERADA, idx, parse_acorde, DB)
from gerador_web_dinamico import gerar_dinamico

REGRA_NOVA = "v2.2-dedutiva"

def avaliar_slash(acorde_base, nota_baixo, shape_str, fontes_externas=None):
    tonica, tipo = parse_acorde(acorde_base)
    if tonica is None or tipo not in TIPOS:
        return "indeterminado", "", "", None, None
    ti, bi = idx(tonica), idx(nota_baixo)
    notas_acorde = {(ti + i) % 12 for i in TIPOS[tipo]}
    permitidas = notas_acorde | {bi}          # X/Y: Y faz parte da especificacao

    pos = [p.strip().upper() for p in shape_str.split(',')]
    if len(pos) != 6: return "rejeitado", "shape.malformado", "", None, None

    notas, trastes, mais_grave = [], [], None
    for c, p in enumerate(pos):
        if p == 'X': continue
        t = int(p); trastes.append(t)
        n = NOTAS[(CORDAS_MIDI[c] + t) % 12]
        notas.append(n)
        if mais_grave is None: mais_grave = n   # 1a corda soando = mais grave
    if not notas: return "rejeitado", "shape.vazio", "", None, None

    tocados = {idx(n) for n in notas}
    presos = [t for t in trastes if t > 0]
    span = (max(presos) - min(presos) + 1) if presos else 1
    tmax = max(trastes)

    falhos = []
    if idx(mais_grave) != bi:           falhos.append("harmonia.baixo")
    if tocados - permitidas:            falhos.append("harmonia.notas_pertencem")
    if ti not in tocados:               falhos.append("harmonia.fundamental")
    if tipo not in SEM_TERCA:
        terca = 3 if 3 in TIPOS[tipo] else 4
        if (ti + terca) % 12 not in tocados: falhos.append("harmonia.terca")
    if tipo in TRIADES or tipo in QUINTA_ALTERADA:
        q = next((i for i in TIPOS[tipo] if i in (6,7,8)), None)
        if q is not None and (ti + q) % 12 not in tocados:
            falhos.append("harmonia.quinta")
    if tipo in EXTENSAO and (ti + EXTENSAO[tipo]) % 12 not in tocados:
        falhos.append("harmonia.extensao")
    if span > 4: falhos.append("fisica.abertura")

    n_str = "-".join(notas)
    if falhos: return "rejeitado", ",".join(falhos), n_str, span, tmax
    if tmax > 15: return "valido_inacessivel", "fisica.alcance", n_str, span, tmax
    base = "valido_inversao" if bi in notas_acorde else "valido_baixo_alterado"
    if fontes_externas == 0: base += "_raro"
    return base, "", n_str, span, tmax

def universo():
    """Inversoes proprias: baixo E' nota do acorde, exceto a fundamental."""
    for t in NOTAS:
        for tipo in TIPOS:
            if tipo == '5': continue
            for iv in TIPOS[tipo]:
                if iv == 0: continue
                yield f"{t}{tipo}", NOTAS[(idx(t) + iv) % 12]

def main():
    total = por_veredito = 0
    from collections import Counter
    cont, exemplos, sem_shape = Counter(), [], 0
    for base, baixo in universo():
        nome = f"{base}/{baixo}"
        try:
            res = gerar_dinamico(nome)
        except Exception as e:
            print(f"  ERRO gerar {nome}: {e}"); continue
        diags = res.get("diagramas", []) if isinstance(res, dict) else []
        if not diags: sem_shape += 1; continue
        for d in diags:
            shape = ",".join(str(x).upper() for x in d["diagrama"])
            v, f, n, sp, tm = avaliar_slash(base, baixo, shape, 0)
            cont[v] += 1; total += 1
            if len(exemplos) < 20: exemplos.append((nome, shape, v, f, n))

    print(f"=== DRY-RUN v2.2 (nada gravado) ===")
    print(f"acordes slash no universo: {sum(1 for _ in universo())}")
    print(f"sem nenhum shape gerado:   {sem_shape}")
    print(f"shapes avaliados:          {total}\n")
    for v, n in cont.most_common(): print(f"  {v:<28}{n}")
    print("\n--- 20 exemplos ---")
    for nome, shape, v, f, n in exemplos:
        print(f"  {nome:<12}{shape:<22}{v:<28}{f or ''}  [{n}]")

if __name__ == "__main__":
    main()
