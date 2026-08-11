#!/usr/bin/env python3
"""Lista quantos acordes estao cadastrados no banco de auditoria."""
import sqlite3

DB = "auditoria.db"

con = sqlite3.connect(DB)
cur = con.cursor()

# Totais gerais
cur.execute("SELECT COUNT(*) FROM auditoria")
total_registros = cur.fetchone()[0]

cur.execute("SELECT COUNT(DISTINCT acorde) FROM auditoria")
total_acordes = cur.fetchone()[0]

print("=" * 50)
print(f"Total de registros (shapes): {total_registros}")
print(f"Total de ACORDES distintos:  {total_acordes}")
print("=" * 50)
print()

# Por acorde: quantos shapes cada um tem
print("--- Shapes por acorde ---")
cur.execute("""
    SELECT acorde, COUNT(*) as qtd
    FROM auditoria
    GROUP BY acorde
    ORDER BY qtd DESC, acorde ASC
""")
for acorde, qtd in cur.fetchall():
    print(f"  {acorde:8s} {qtd} shape(s)")

print()

# Por origem (gerado_por)
print("--- Registros por origem ---")
cur.execute("""
    SELECT gerado_por, COUNT(*) as qtd
    FROM auditoria
    GROUP BY gerado_por
    ORDER BY qtd DESC
""")
for origem, qtd in cur.fetchall():
    print(f"  {origem:12s} {qtd}")

print()

# Por status
print("--- Registros por status ---")
cur.execute("""
    SELECT status, COUNT(*) as qtd
    FROM auditoria
    GROUP BY status
    ORDER BY qtd DESC
""")
for status, qtd in cur.fetchall():
    print(f"  {status:12s} {qtd}")

con.close()
