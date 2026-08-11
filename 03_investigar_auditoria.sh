#!/bin/bash

echo "########################################################"
echo "### ARQUIVO: auditoria.py"
echo "########################################################"
if [ -f auditoria.py ]; then
  cat -n auditoria.py
else
  echo ">>> NAO ENCONTRADO <<<"
fi

echo ""
echo "########################################################"
echo "### SCHEMA DO auditoria.db"
echo "########################################################"
sqlite3 auditoria.db ".schema"

echo ""
echo "########################################################"
echo "### CONTAGEM DE LINHAS POR TABELA"
echo "########################################################"
for t in $(sqlite3 auditoria.db ".tables"); do
  echo "--- $t ---"
  sqlite3 auditoria.db "SELECT COUNT(*) FROM $t;"
done

echo ""
echo "########################################################"
echo "### AMOSTRA: 20 LINHAS DA TABELA auditoria"
echo "########################################################"
sqlite3 -header -column auditoria.db "SELECT * FROM auditoria LIMIT 20;"

echo ""
echo "########################################################"
echo "### VALORES DISTINTOS DE gerado_por"
echo "########################################################"
sqlite3 auditoria.db "SELECT gerado_por, COUNT(*) FROM auditoria GROUP BY gerado_por;"

echo ""
echo "########################################################"
echo "### QUANTOS ACORDES DISTINTOS EXISTEM NA TABELA"
echo "########################################################"
sqlite3 auditoria.db "SELECT COUNT(DISTINCT acorde) FROM auditoria;"

echo ""
echo "########################################################"
echo "### todos_acordes.json (primeiras 50 linhas)"
echo "########################################################"
if [ -f todos_acordes.json ]; then
  head -c 3000 todos_acordes.json
  echo ""
  echo "... (tamanho do arquivo: $(wc -c < todos_acordes.json) bytes)"
else
  echo ">>> NAO ENCONTRADO <<<"
fi

echo ""
echo "########################################################"
echo "### validacao.py (importado por gerador_web_dinamico.py)"
echo "########################################################"
if [ -f validacao.py ]; then
  cat -n validacao.py
else
  echo ">>> NAO ENCONTRADO NA RAIZ <<<"
fi

echo ""
echo "########################################################"
echo "### BUSCA POR 'requests' / 'bs4' / 'selenium' / 'scrap' no projeto (indicios de robo existente)"
echo "########################################################"
grep -rliE "requests|beautifulsoup|bs4|selenium|scrap|urlopen" --include="*.py" . 2>/dev/null | grep -v backup_antes

