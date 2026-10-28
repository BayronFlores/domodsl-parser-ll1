"""
Analizador sintáctico predictivo por DESCENSO RECURSIVO para DomoDSL.

Hay un método por cada no terminal de la gramática (ver gramatica.py). Los no
terminales "primados" (programa_p, condicion_p, termino_p, acciones_p, parametros)
son listas/recursiones por la derecha, así que se implementan con un ciclo
`while`; esto es equivalente a la recursión de la gramática pero evita
desbordar la pila de Python con programas largos y permite construir el AST
con asociatividad izquierda.

Cuando un no terminal puede derivar ε, el analizador verifica que el token de
lookahead pertenezca a FOLLOW de ese no terminal; si no, informa un error
específico en lugar de aceptar y fallar más adelante.

Devuelve un AST (arbol.Programa). Ante el primer error lanza ErrorSintactico
con un mensaje localizado (línea, columna, posición).
"""
from arbol import (Accion, And, Comparacion, Not, Or, Programa, Regla, Valor)
from errores import ErrorSintactico
from gramatica import FIN, FIRST, FOLLOW
from lexer import analizador_lexico

PRIMERO_VALOR = FIRST["valor"]                 # {NUM, TRUE, FALSE, ID}
OPERADORES_TXT = "'>', '<', '>=', '<=', '==', '!='"


def describir(token):
    """Descripción legible de un token para los mensajes de error."""
    if token.tipo == FIN:
        return "el fin de la entrada"
    if token.tipo in ("WHEN", "THEN", "AND", "OR", "NOT", "TRUE", "FALSE"):
        return f"la palabra reservada {token.lexema.upper()}"
    if token.tipo == "ID":
        return f"el identificador '{token.lexema}'"
    if token.tipo == "NUM":
        return f"el número {token.lexema}"
    if token.tipo == "OP_REL":
        return f"el operador '{token.lexema}'"
    return f"el símbolo '{token.lexema}'"


class ParserDescendente:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0
        self.profundidad = 0          # nivel de paréntesis abiertos
        self.parentesis_abiertos = []  # pila de tokens '(' para mensajes

    # ------------------------------------------------------------ utilidades
    @property
    def actual(self):
        return self.tokens[self.i]

    def avanzar(self):
        token = self.tokens[self.i]
        if token.tipo != FIN:
            self.i += 1
        return token

    @property
    def anterior(self):
        return self.tokens[self.i - 1] if self.i > 0 else None

    def error(self, mensaje, token=None):
        t = token or self.actual
        raise ErrorSintactico(mensaje, t.pos, t.linea, t.columna)

    def error_esperaba(self, esperado, contexto=""):
        """'se esperaba X [contexto], pero se encontró Y'."""
        suf = f" {contexto}" if contexto else ""
        self.error(f"se esperaba {esperado}{suf}, pero se encontró {describir(self.actual)}.")

    def coincidir(self, tipo, esperado, contexto=""):
        if self.actual.tipo != tipo:
            self.error_esperaba(esperado, contexto)
        return self.avanzar()

    # ----------------------------------------------------- <programa> (1,2,3)
    def programa(self):
        if self.actual.tipo != "WHEN":
            if self.actual.tipo == FIN:
                self.error("la entrada está vacía: se esperaba al menos una regla "
                           "que comience con la palabra reservada WHEN.")
            self.error_esperaba("la palabra reservada WHEN", "al inicio de una regla")
        reglas = [self.regla()]                       # programa → regla programa_p
        while self.actual.tipo == "WHEN":             # programa_p → regla programa_p
            reglas.append(self.regla())
        if self.actual.tipo != FIN:                   # programa_p → ε  (lookahead ∈ {$})
            self.error_esperaba("una nueva regla (WHEN) o el fin de la entrada",
                                "después de ';'")
        return Programa(reglas)

    # ----------------------------------------------------------- <regla> (4)
    def regla(self):
        when = self.coincidir("WHEN", "la palabra reservada WHEN")
        condicion = self.condicion("después de WHEN")
        self.coincidir("THEN", "la palabra reservada THEN",
                       "después de la condición")
        acciones = self.acciones()
        self.coincidir("PUNTO_COMA", "';'",
                       "al final de la regla (o ',' para encadenar otra acción)")
        return Regla(condicion, acciones, when.linea)

    # ------------------------------------------------- <condicion> (5,6,7)
    def condicion(self, contexto):
        izq = self.termino(contexto)                  # condicion → termino condicion_p
        while self.actual.tipo == "OR":               # condicion_p → OR termino condicion_p
            self.avanzar()
            der = self.termino("después de OR")
            izq = Or(izq, der)                        # asociatividad izquierda
        return izq                                    # condicion_p → ε  (lookahead ∈ FOLLOW)

    # --------------------------------------------------- <termino> (8,9,10)
    def termino(self, contexto):
        izq = self.factor(contexto)                   # termino → factor termino_p
        while self.actual.tipo == "AND":              # termino_p → AND factor termino_p
            self.avanzar()
            der = self.factor("después de AND")
            izq = And(izq, der)
        # termino_p → ε : el lookahead debe estar en FOLLOW(termino_p)
        if self.actual.tipo not in FOLLOW["termino_p"]:
            if self.profundidad > 0:
                self.error_esperaba("')' para cerrar el paréntesis abierto "
                                    f"en la columna {self.parentesis_abiertos[-1].columna} "
                                    "(o un conector AND / OR)")
            self.error_esperaba("la palabra reservada THEN (o un conector AND / OR)",
                                "después de la condición")
        if self.actual.tipo == "PARENT_DER" and self.profundidad == 0:
            self.error("paréntesis de cierre ')' sin su '(' correspondiente.")
        return izq

    # ---------------------------------------------------- <factor> (11,12,13)
    def factor(self, contexto):
        if self.actual.tipo == "NOT":                 # factor → NOT factor
            self.avanzar()
            return Not(self.factor("después de NOT"))
        if self.actual.tipo == "PARENT_IZQ":          # factor → ( condicion )
            abre = self.avanzar()
            self.profundidad += 1
            self.parentesis_abiertos.append(abre)
            interno = self.condicion("después de '('")
            if self.actual.tipo != "PARENT_DER":
                self.error_esperaba(f"')' para cerrar el paréntesis abierto en la columna "
                                    f"{abre.columna}")
            self.avanzar()
            self.parentesis_abiertos.pop()
            self.profundidad -= 1
            return interno
        return self.comparacion(contexto)             # factor → comparacion

    # ------------------------------------------------- <comparacion> (14)
    def comparacion(self, contexto):
        if self.actual.tipo != "ID":
            self.error_esperaba("una condición (un identificador, NOT o '(')", contexto)
        variable = self.avanzar()
        if self.actual.tipo != "OP_REL":
            self.error_esperaba(f"un operador relacional ({OPERADORES_TXT})",
                                f"después de '{variable.lexema}'")
        operador = self.avanzar()
        valor = self.valor(f"después del operador {operador.lexema}")
        return Comparacion(variable.lexema, operador.lexema, valor)

    # ------------------------------------------------------ <valor> (15-18)
    def valor(self, contexto):
        t = self.actual
        if t.tipo not in PRIMERO_VALOR:
            self.error_esperaba("un valor (número, TRUE, FALSE o identificador)", contexto)
        self.avanzar()
        if t.tipo == "NUM":
            return Valor("NUM", t.lexema)
        if t.tipo in ("TRUE", "FALSE"):
            return Valor("BOOL", t.lexema.upper())
        return Valor("ID", t.lexema)

    # ------------------------------------------- <acciones> (19,20,21)
    def acciones(self):
        lista = [self.accion("después de THEN")]      # acciones → accion acciones_p
        while self.actual.tipo == "COMA":             # acciones_p → , accion acciones_p
            self.avanzar()
            lista.append(self.accion("después de ','"))
        return lista                                  # acciones_p → ε (lookahead = ';')

    # ---------------------------------------------- <accion> (22) y <parametros> (23,24)
    def accion(self, contexto):
        if self.actual.tipo != "ID":
            self.error_esperaba("el nombre de una acción (identificador)", contexto)
        nombre = self.avanzar()
        if self.actual.tipo != "ID":
            self.error_esperaba("el dispositivo u objeto (identificador)",
                                f"después de la acción '{nombre.lexema}'")
        objeto = self.avanzar()
        parametros = []
        while self.actual.tipo in PRIMERO_VALOR:      # parametros → valor parametros
            parametros.append(self.valor("como parámetro"))
        return Accion(nombre.lexema, objeto.lexema, parametros)   # parametros → ε


def parsear(entrada):
    """Atajo: texto → AST (lanza ErrorLexico / ErrorSintactico)."""
    return ParserDescendente(analizador_lexico(entrada)).programa()
