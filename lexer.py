"""
Analizador léxico del lenguaje DomoDSL (automatización de una casa inteligente).

Parte del analizador léxico básico entregado por el docente, ampliado con:
  * token COMA (para encadenar acciones),
  * números decimales,
  * posición (offset, línea y columna) en cada token,
  * token de fin de entrada '$',
  * mensajes de error léxico con sugerencias.
"""
import re
from bisect import bisect_right
from dataclasses import dataclass

from errores import ErrorLexico

FIN = "$"

PALABRAS_RESERVADAS = {"WHEN", "THEN", "AND", "OR", "NOT", "TRUE", "FALSE"}

# Orden importa: la primera alternativa que coincide gana.
ESPECIFICACION_TOKENS = [
    ("NUM",        r"\d+(?:\.\d+)?"),
    ("OP_REL",     r">=|<=|==|!=|>|<"),
    ("PUNTO_COMA", r";"),
    ("COMA",       r","),
    ("PARENT_IZQ", r"\("),
    ("PARENT_DER", r"\)"),
    ("ID",         r"[A-Za-z_][A-Za-z0-9_]*"),
    ("ESPACIO",    r"[ \t\r\n]+"),
    ("ERROR",      r"."),
]

PATRON = re.compile("|".join(f"(?P<{n}>{e})" for n, e in ESPECIFICACION_TOKENS))


@dataclass(frozen=True)
class Token:
    tipo: str      # NUM, OP_REL, ID, WHEN, THEN, ..., '$'
    lexema: str    # texto tal como aparece en la entrada
    pos: int       # offset (0-based) dentro de la entrada
    linea: int     # 1-based
    columna: int   # 1-based


def _linea_columna(inicios_linea, pos):
    indice = bisect_right(inicios_linea, pos) - 1
    return indice + 1, pos - inicios_linea[indice] + 1


def analizador_lexico(cadena):
    """Convierte la cadena en una lista de Token terminada por el token '$'."""
    inicios = [0] + [m.end() for m in re.finditer(r"\n", cadena)]
    tokens = []
    for m in PATRON.finditer(cadena):
        tipo, lexema, pos = m.lastgroup, m.group(), m.start()
        linea, columna = _linea_columna(inicios, pos)
        if tipo == "ESPACIO":
            continue
        if tipo == "ID" and lexema.upper() in PALABRAS_RESERVADAS:
            tipo = lexema.upper()
        elif tipo == "ERROR":
            ayuda = ""
            if lexema == "=":
                ayuda = " ¿quiso escribir '==' para comparar?"
            elif lexema == "!":
                ayuda = " ¿quiso escribir '!=' para 'distinto de'?"
            raise ErrorLexico(f"símbolo no reconocido '{lexema}'.{ayuda}".rstrip(),
                              pos, linea, columna)
        tokens.append(Token(tipo, lexema, pos, linea, columna))
    linea, columna = _linea_columna(inicios, len(cadena))
    tokens.append(Token(FIN, "", len(cadena), linea, columna))
    return tokens


def tokens_a_tuplas(tokens):
    """Formato del notebook original: [(TIPO, lexema), ...] (sin el '$')."""
    return [(t.tipo, t.lexema) for t in tokens if t.tipo != FIN]
