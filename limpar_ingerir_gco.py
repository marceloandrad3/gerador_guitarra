import ast

with open("ingerir_gco.py") as f:
    src = f.read()

OLD = '''            conv = [None if p == "X" else int(p) for p in parse(shape)] \\
                if False else [None if p.strip().upper() == "X" else int(p.strip())
                                for p in shape.split(",")]'''

NEW = '''            conv = [None if p.strip().upper() == "X" else int(p.strip())
                    for p in shape.split(",")]'''

assert OLD in src, "trecho feio nao encontrado"
src = src.replace(OLD, NEW)
ast.parse(src)
with open("ingerir_gco.py", "w") as f:
    f.write(src)
print("ingerir_gco.py: limpo")
