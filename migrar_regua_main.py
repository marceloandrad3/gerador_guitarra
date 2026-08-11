import ast

with open("regua_v21.py") as f:
    src = f.read()

OLD = '''def main():
    con = sqlite3.connect(DB)
    linhas = con.execute(
        "SELECT acorde, shape, veredito, criterios_falhos, fontes_externas, span, traste_max "
        "FROM VEREDITOS WHERE regra_versao=? ORDER BY id", (REGRA,)).fetchall()
    con.close()

    ok = 0; div = []
    for acorde, shape, ver_gravado, falhos_gravados, fe, sp_g, tm_g in linhas:
        ver_calc, falhos_calc, _, sp_c, tm_c = avaliar(acorde, shape, fe)
        if ver_calc == ver_gravado and tm_c == tm_g and sp_c == sp_g:
            ok += 1
        else:
            div.append((acorde, shape, ver_gravado, falhos_gravados or "", ver_calc, falhos_calc))

    print(f"Total gravado ({REGRA}): {len(linhas)}")
    print(f"Veredito identico:       {ok}")
    print(f"DIVERGENTE:              {len(div)}")
    if div:
        print("\\n--- primeiras 25 divergencias ---")
        print(f"{'acorde':<10}{'shape':<22}{'GRAVADO':<22}{'CALCULADO':<22}falhos_calc")
        for a, s, vg, fg, vc, fc in div[:25]:
            print(f"{a:<10}{s:<22}{vg:<22}{vc:<22}{fc}")
        from collections import Counter
        print("\\n--- padrao das divergencias (gravado -> calculado) ---")
        for k, n in Counter((vg, vc) for _,_,vg,_,vc,_ in div).most_common():
            print(f"  {k[0]} -> {k[1]}: {n}")'''

NEW = '''def main():
    """Delega para teste_regua_v21.py, que compara contra as tabelas
    SHAPES_APROVADOS/SHAPES_EM_AUDITORIA/SHAPES_REPROVADOS (fonte de verdade
    atual). Evita duplicar aqui a mesma logica de comparacao."""
    import subprocess, sys as _sys
    r = subprocess.run([_sys.executable, os.path.join(DIR, "teste_regua_v21.py")])
    _sys.exit(r.returncode)'''

assert OLD in src, "bloco main() nao encontrado"
src = src.replace(OLD, NEW)
ast.parse(src)
with open("regua_v21.py", "w") as f:
    f.write(src)
print("regua_v21.py: main() atualizado, sem mais referencia a VEREDITOS")
