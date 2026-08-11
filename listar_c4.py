#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect("auditoria.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT * FROM auditoria WHERE acorde = 'Csus4'")
rows = cur.fetchall()
print(f"Registros com acorde='Csus4': {len(rows)}")
for row in rows:
    print(dict(row))
    print()

conn.close()
