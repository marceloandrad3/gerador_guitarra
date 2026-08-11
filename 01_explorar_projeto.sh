#!/bin/bash
PROJ="."

echo "===================================="
echo "1) ESTRUTURA DE ARQUIVOS (ate 3 niveis)"
echo "===================================="
find "$PROJ" -maxdepth 3 \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/venv/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/.venv/*' \
  | sort

echo ""
echo "===================================="
echo "2) ARQUIVOS DE CONFIG/METADADOS"
echo "===================================="
for f in README.md README.txt package.json requirements.txt pyproject.toml setup.py Cargo.toml go.mod composer.json .gitignore Makefile Dockerfile; do
  if [ -f "$PROJ/$f" ]; then
    echo "--- $f ---"
    cat "$PROJ/$f"
    echo ""
  fi
done

echo "===================================="
echo "3) CONTAGEM DE ARQUIVOS POR EXTENSAO"
echo "===================================="
find "$PROJ" \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/venv/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/.venv/*' \
  -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn

echo ""
echo "===================================="
echo "4) TAMANHO TOTAL DO PROJETO"
echo "===================================="
du -sh "$PROJ" 2>/dev/null

echo ""
echo "===================================="
echo "5) GIT LOG"
echo "===================================="
if [ -d "$PROJ/.git" ]; then
  git -C "$PROJ" log --oneline -10
else
  echo "(nao e um repositorio git)"
fi
