# Gerador de Acordes de Guitarra

Gerador de diagramas de acordes (incluindo inversoes/slash chords) com
dedicao de dedos validada (pestana cheia, mini-pestana apenas quando
inevitavel) e score de dificuldade.

## Executar
python3 servidor.py
Acesse http://localhost:8000

## Estrutura
- servidor.py: API Flask + frontend (index.html)
- gerador_web_dinamico.py: geracao de shapes e slash chords
- dedicacao.py: dedicao de dedos e pestana (fonte unica)
- dificuldade.py: score/rotulo de dificuldade
