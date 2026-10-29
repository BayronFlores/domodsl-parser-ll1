"""
Definición formal de la gramática de DomoDSL y su análisis LL(1).

Contiene:
  * la GLC (lista numerada de producciones),
  * el cálculo de los conjuntos FIRST y FOLLOW (algoritmo de punto fijo),
  * la construcción de la tabla predictiva LL(1) y la detección de conflictos.

Convención: los no terminales son los símbolos que aparecen a la izquierda de una
producción (en minúsculas); todo otro símbolo es terminal (tokens en MAYÚSCULAS).
EPS = ε (cadena vacía) y FIN = '$' (marca de fin de entrada).
"""

EPS = "ε"
FIN = "$"
SIMBOLO_INICIAL = "programa"

# ---------------------------------------------------------------------------
#  GLC final (ya sin recursión izquierda, factorizada y no ambigua)
#  Cada producción: (no_terminal, [símbolos del lado derecho])
# ---------------------------------------------------------------------------
PRODUCCIONES = [
    # --- Programa: una o más reglas ---------------------------------------
    ("programa",    ["regla", "programa_p"]),                                  # 1
    ("programa_p",  ["regla", "programa_p"]),                                  # 2
    ("programa_p",  [EPS]),                                                    # 3
    # --- Regla: WHEN <condición> THEN <acciones> ; ------------------------
    ("regla",       ["WHEN", "condicion", "THEN", "acciones", "PUNTO_COMA"]),  # 4
    # --- Condiciones: OR (menor precedencia) > AND > NOT / ( ) / comparación
    ("condicion",   ["termino", "condicion_p"]),                               # 5
    ("condicion_p", ["OR", "termino", "condicion_p"]),                         # 6
    ("condicion_p", [EPS]),                                                    # 7
    ("termino",     ["factor", "termino_p"]),                                  # 8
    ("termino_p",   ["AND", "factor", "termino_p"]),                           # 9
    ("termino_p",   [EPS]),                                                    # 10
    ("factor",      ["NOT", "factor"]),                                        # 11
    ("factor",      ["PARENT_IZQ", "condicion", "PARENT_DER"]),                # 12
    ("factor",      ["comparacion"]),                                          # 13
    ("comparacion", ["ID", "OP_REL", "valor"]),                                # 14
    # --- Valores ------------------------------------------------------------
    ("valor",       ["NUM"]),                                                  # 15
    ("valor",       ["TRUE"]),                                                 # 16
    ("valor",       ["FALSE"]),                                                # 17
    ("valor",       ["ID"]),                                                   # 18
    # --- Acciones (una o más, separadas por coma, con parámetros) ----------
    ("acciones",    ["accion", "acciones_p"]),                                 # 19
    ("acciones_p",  ["COMA", "accion", "acciones_p"]),                         # 20
    ("acciones_p",  [EPS]),                                                    # 21
    ("accion",      ["ID", "ID", "parametros"]),                               # 22
    ("parametros",  ["valor", "parametros"]),                                  # 23
    ("parametros",  [EPS]),                                                    # 24
]

NO_TERMINALES = list(dict.fromkeys(a for a, _ in PRODUCCIONES))
TERMINALES = list(dict.fromkeys(
    s for _, rhs in PRODUCCIONES for s in rhs
    if s not in NO_TERMINALES and s != EPS))
TERMINALES_TABLA = TERMINALES + [FIN]

# Nombres legibles para mensajes de error
NOMBRES_AMIGABLES = {
    "WHEN": "la palabra reservada WHEN", "THEN": "la palabra reservada THEN",
    "AND": "AND", "OR": "OR", "NOT": "NOT", "TRUE": "TRUE", "FALSE": "FALSE",
    "ID": "un identificador", "NUM": "un número",
    "OP_REL": "un operador relacional (>, <, >=, <=, ==, !=)",
    "PUNTO_COMA": "';'", "COMA": "','",
    "PARENT_IZQ": "'('", "PARENT_DER": "')'", FIN: "el fin de la entrada",
}


def es_no_terminal(simbolo):
    return simbolo in NO_TERMINALES


def producciones_de(no_terminal):
    return [(i + 1, rhs) for i, (a, rhs) in enumerate(PRODUCCIONES) if a == no_terminal]


def formatear_produccion(indice):
    a, rhs = PRODUCCIONES[indice - 1]
    return f"{a} → {' '.join(rhs)}"


# ---------------------------------------------------------------------------
#  FIRST
# ---------------------------------------------------------------------------
def calcular_first():
    first = {a: set() for a in NO_TERMINALES}
    cambio = True
    while cambio:
        cambio = False
        for a, rhs in PRODUCCIONES:
            nuevo = first_de_cadena(rhs, first)
            if not nuevo <= first[a]:
                first[a] |= nuevo
                cambio = True
    return first


def first_de_cadena(cadena, first):
    """FIRST de una forma sentencial X1 X2 ... Xn (puede contener ε)."""
    resultado = set()
    for simbolo in cadena:
        if simbolo == EPS:
            resultado.add(EPS)
            return resultado
        if not es_no_terminal(simbolo):          # terminal
            resultado.add(simbolo)
            return resultado
        resultado |= first[simbolo] - {EPS}
        if EPS not in first[simbolo]:
            return resultado
    resultado.add(EPS)                           # todos los símbolos anulables
    return resultado


# ---------------------------------------------------------------------------
#  FOLLOW
# ---------------------------------------------------------------------------
def calcular_follow(first=None):
    first = first or calcular_first()
    follow = {a: set() for a in NO_TERMINALES}
    follow[SIMBOLO_INICIAL].add(FIN)
    cambio = True
    while cambio:
        cambio = False
        for a, rhs in PRODUCCIONES:
            for i, simbolo in enumerate(rhs):
                if not es_no_terminal(simbolo):
                    continue
                beta = rhs[i + 1:]
                f_beta = first_de_cadena(beta, first) if beta else {EPS}
                nuevo = f_beta - {EPS}
                if EPS in f_beta:                # β ⇒* ε  →  FOLLOW(A) ⊆ FOLLOW(B)
                    nuevo |= follow[a]
                if not nuevo <= follow[simbolo]:
                    follow[simbolo] |= nuevo
                    cambio = True
    return follow


# ---------------------------------------------------------------------------
#  Tabla LL(1)
# ---------------------------------------------------------------------------
def construir_tabla(first=None, follow=None):
    """
    Devuelve (tabla, conflictos).
      tabla[A][a] = nº de producción a usar cuando el tope es A y el lookahead a.
      conflictos  = lista de (A, a, [producciones en conflicto]).
    """
    first = first or calcular_first()
    follow = follow or calcular_follow(first)
    celdas = {a: {} for a in NO_TERMINALES}
    for i, (a, rhs) in enumerate(PRODUCCIONES, start=1):
        f = first_de_cadena(rhs, first)
        for t in f - {EPS}:
            celdas[a].setdefault(t, []).append(i)
        if EPS in f:
            for t in follow[a]:
                celdas[a].setdefault(t, []).append(i)
    conflictos = [(a, t, ps) for a in NO_TERMINALES
                  for t, ps in celdas[a].items() if len(ps) > 1]
    tabla = {a: {t: ps[0] for t, ps in fila.items()} for a, fila in celdas.items()}
    return tabla, conflictos


def es_ll1():
    _, conflictos = construir_tabla()
    return not conflictos


# Cálculos únicos reutilizados por los analizadores
FIRST = calcular_first()
FOLLOW = calcular_follow(FIRST)
TABLA, CONFLICTOS = construir_tabla(FIRST, FOLLOW)


# ---------------------------------------------------------------------------
#  Presentación
# ---------------------------------------------------------------------------
def _fmt_conjunto(c):
    orden = {s: i for i, s in enumerate(TERMINALES_TABLA + [EPS])}
    return "{ " + ", ".join(sorted(c, key=lambda s: orden.get(s, 99))) + " }"


def formatear_gramatica():
    lineas = [f"Símbolo inicial: <{SIMBOLO_INICIAL}>", "Producciones:"]
    for i in range(1, len(PRODUCCIONES) + 1):
        lineas.append(f"  ({i:>2}) {formatear_produccion(i)}")
    return "\n".join(lineas)


def formatear_first_follow():
    ancho = max(len(a) for a in NO_TERMINALES)
    lineas = [f"{'No terminal':<{ancho}}  FIRST / FOLLOW"]
    for a in NO_TERMINALES:
        lineas.append(f"FIRST({a})".ljust(ancho + 8) + " = " + _fmt_conjunto(FIRST[a]))
    lineas.append("")
    for a in NO_TERMINALES:
        lineas.append(f"FOLLOW({a})".ljust(ancho + 9) + " = " + _fmt_conjunto(FOLLOW[a]))
    return "\n".join(lineas)


def formatear_tabla():
    ancho_nt = max(len(a) for a in NO_TERMINALES)
    cabecera = f"{'':<{ancho_nt}} | " + " | ".join(f"{t:^10}" for t in TERMINALES_TABLA)
    lineas = [cabecera, "-" * len(cabecera)]
    for a in NO_TERMINALES:
        celdas = [f"{TABLA[a].get(t, ''):^10}" for t in TERMINALES_TABLA]
        lineas.append(f"{a:<{ancho_nt}} | " + " | ".join(celdas))
    lineas.append("")
    lineas.append("Conflictos: " + ("ninguno → la gramática ES LL(1)" if not CONFLICTOS
                                    else str(CONFLICTOS)))
    return "\n".join(lineas)


if __name__ == "__main__":
    print(formatear_gramatica(), end="\n\n")
    print(formatear_first_follow(), end="\n\n")
    print(formatear_tabla())
