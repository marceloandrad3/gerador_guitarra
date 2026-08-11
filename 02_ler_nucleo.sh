#!/bin/bash
for f in servidor.py gerador_web_dinamico.py dedicacao.py dificuldade.py; do
  echo ""
  echo "########################################################"
  echo "### ARQUIVO: $f"
  echo "########################################################"
  if [ -f "$f" ]; then
    cat -n "$f"
  else
    echo ">>> NAO ENCONTRADO <<<"
  fi
done
