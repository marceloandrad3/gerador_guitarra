"""
Modulo de validacao de shapes de acordes.

Regra (definicao de acorde): um shape so e valido se
1. Nenhuma nota errada: toda nota tocada pertence ao acorde.
2. Nenhuma nota faltando: todos os intervalos do acorde estao presentes,
   exceto os explicitamente tolerados via `tolerar_faltando` (ausencia da
   5a justa - pratica convencional do violao, Wikipedia "Guitar chord":
   "the fifth is often omitted"). Tonica e 5as alteradas nunca toleradas.
"""


def _parse_casas(diagrama):
    """Converte valores do diagrama ('X', '0', '3'...) em casa int ou None."""
    casas = []
    for valor in diagrama:
        try:
            casa = int(valor)
        except (TypeError, ValueError):
            casa = None
        casas.append(casa if casa is not None and casa >= 0 else None)
    return casas


def notas_tocadas(casas, afinacao):
    """Classes de altura (0-11) das cordas tocadas (inclui cordas soltas)."""
    return {(afinacao[i] + c) % 12 for i, c in enumerate(casas) if c is not None}


def shape_valido(casas, afinacao, notas_acorde, tolerar_faltando=frozenset()):
    """Valida o shape contra as notas do acorde.

    Sem sobra sempre; sem falta exceto notas em `tolerar_faltando`
    (classes de altura cuja ausencia e aceita, ex.: 5a justa).
    """
    tocadas = notas_tocadas(casas, afinacao)
    return (tocadas.issubset(notas_acorde)
            and notas_acorde.issubset(tocadas | set(tolerar_faltando)))


def diagrama_valido(diagrama, afinacao, notas_acorde, tolerar_faltando=frozenset()):
    """Valida um diagrama (lista de strings) contra as notas do acorde."""
    return shape_valido(_parse_casas(diagrama), afinacao, notas_acorde,
                        tolerar_faltando)
