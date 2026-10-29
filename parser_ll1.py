"""
Analizador sintáctico predictivo DIRIGIDO POR TABLA LL(1) para DomoDSL.

Usa la tabla construida en gramatica.py (no depende de ninguna biblioteca de
generación de parsers). Mantiene una pila de símbolos y construye el árbol
sintáctico concreto (árbol de derivación) como objetos arbol.Nodo.

Algoritmo (clásico):
    pila = [$, programa]
    mientras pila no vacía:
        X = tope, a = token actual
        si X es terminal:  X == a → consumir ; si no → error
        si X es no terminal: M[X, a] = producción → reemplazar X por su lado derecho
                              (en orden inverso) ; si la celda está vacía → error
"""
from arbol import Nodo
from errores import ErrorSintactico
from gramatica import (EPS, FIN, NOMBRES_AMIGABLES, PRODUCCIONES, SIMBOLO_INICIAL,
                       TABLA, es_no_terminal, formatear_produccion)
from lexer import analizador_lexico
from parser_rd import describir


def _esperados(no_terminal):
    """Terminales que tienen entrada en la fila del no terminal (para el mensaje)."""
    return sorted(TABLA[no_terminal].keys(), key=lambda t: list(NOMBRES_AMIGABLES).index(t))


def _lista_legible(terminales):
    nombres = [NOMBRES_AMIGABLES[t] for t in terminales]
    if len(nombres) == 1:
        return nombres[0]
    return ", ".join(nombres[:-1]) + " o " + nombres[-1]


def parsear_ll1(tokens, traza=None):
    """
    Analiza la lista de tokens. Devuelve la raíz del árbol sintáctico (Nodo).
    Si se entrega una lista en `traza`, se le agregan los pasos del algoritmo
    como tuplas (pila, entrada_restante, accion).
    """
    raiz = Nodo(SIMBOLO_INICIAL)
    fin = Nodo(FIN, terminal=True)
    pila = [(FIN, fin), (SIMBOLO_INICIAL, raiz)]     # el tope es el último elemento
    i = 0

    while pila:
        simbolo, nodo = pila[-1]
        token = tokens[i]

        if traza is not None:
            restante = " ".join(t.tipo for t in tokens[i:])
            contenido = " ".join(s for s, _ in reversed(pila))
            accion = ""

        if not es_no_terminal(simbolo):                       # --- terminal ---
            if simbolo != token.tipo:
                raise ErrorSintactico(
                    f"se esperaba {NOMBRES_AMIGABLES[simbolo]}, "
                    f"pero se encontró {describir(token)}.",
                    token.pos, token.linea, token.columna)
            pila.pop()
            nodo.etiqueta = f"{simbolo} '{token.lexema}'" if token.lexema else simbolo
            if traza is not None:
                traza.append((contenido, restante, f"coincidir {simbolo}"))
            if simbolo != FIN:
                i += 1
            continue

        nprod = TABLA[simbolo].get(token.tipo)                # --- no terminal ---
        if nprod is None:
            raise ErrorSintactico(
                f"símbolo inesperado: se encontró {describir(token)}; "
                f"en este punto (<{simbolo}>) se esperaba {_lista_legible(_esperados(simbolo))}.",
                token.pos, token.linea, token.columna)
        pila.pop()
        _, rhs = PRODUCCIONES[nprod - 1]
        hijos = []
        for s in rhs:
            hijos.append(Nodo(EPS, terminal=True) if s == EPS
                         else Nodo(s, terminal=not es_no_terminal(s)))
        nodo.hijos = hijos
        for s, h in reversed(list(zip(rhs, hijos))):
            if s != EPS:
                pila.append((s, h))
        if traza is not None:
            traza.append((contenido, restante, f"({nprod}) {formatear_produccion(nprod)}"))
    return raiz


def parsear_texto_ll1(entrada, traza=None):
    return parsear_ll1(analizador_lexico(entrada), traza)
