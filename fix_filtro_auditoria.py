import ast

with open("servidor.py") as f:
    src = f.read()

OLD = '''    acorde_db = tonica + tipo
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

NEW = '''    # So aparece quem esta em SHAPES_APROVADOS. Bloqueia REPROVADOS (harmonia
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
    return resultado'''

assert OLD in src, "bloco nao encontrado"
src = src.replace(OLD, NEW)
ast.parse(src)
print("sintaxe ok")
with open("servidor.py", "w") as f:
    f.write(src)
print("servidor.py corrigido")
