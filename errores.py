"""Excepciones del analizador (léxico y sintáctico) con información de posición."""


class ErrorDSL(Exception):
    """Clase base: guarda posición (offset), línea y columna (1-based)."""

    prefijo = "Error"

    def __init__(self, mensaje, pos=0, linea=1, columna=1):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.pos = pos
        self.linea = linea
        self.columna = columna

    def __str__(self):
        return (f"{self.prefijo} (línea {self.linea}, columna {self.columna}, "
                f"posición {self.pos}): {self.mensaje}")

    def con_contexto(self, entrada):
        """Devuelve el mensaje seguido de la línea de código y un puntero '^'."""
        lineas = entrada.split("\n")
        if 1 <= self.linea <= len(lineas):
            texto = lineas[self.linea - 1]
            return f"{self}\n    {texto}\n    {' ' * (self.columna - 1)}^"
        return str(self)


class ErrorLexico(ErrorDSL):
    prefijo = "Error léxico"


class ErrorSintactico(ErrorDSL):
    prefijo = "Error sintáctico"
