"""
Representaciones sintácticas de DomoDSL.

  * Nodo      : nodo genérico (etiqueta + hijos) usado para dibujar cualquier árbol.
  * Clases AST: Programa, Regla, Or, And, Not, Comparacion, Valor, Accion.
                Cada una sabe convertirse a Nodo con a_nodo().
  * a_texto() : árbol en texto jerárquico (con caracteres ├── └──).
  * a_dot()   : exportación a Graphviz (.dot) para generar PNG/SVG/PDF.
"""
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
#  Nodo genérico
# ---------------------------------------------------------------------------
@dataclass
class Nodo:
    etiqueta: str
    hijos: list = field(default_factory=list)
    terminal: bool = False


def a_texto(nodo):
    """Árbol jerárquico en texto."""
    lineas = [nodo.etiqueta]

    def recorrer(n, prefijo):
        for i, h in enumerate(n.hijos):
            ultimo = i == len(n.hijos) - 1
            lineas.append(prefijo + ("└── " if ultimo else "├── ") + h.etiqueta)
            recorrer(h, prefijo + ("    " if ultimo else "│   "))

    recorrer(nodo, "")
    return "\n".join(lineas)


def a_dot(nodo, titulo="arbol"):
    """Exporta el árbol a formato Graphviz DOT."""
    lineas = [f'digraph "{titulo}" {{',
              '  graph [ordering=out, nodesep=0.25, ranksep=0.45];',
              '  node [fontname="Helvetica", fontsize=11];']
    contador = [0]

    def escapar(s):
        return s.replace("\\", "\\\\").replace('"', '\\"')

    def visitar(n):
        mi_id = f"n{contador[0]}"
        contador[0] += 1
        estilo = ('shape=box, style="rounded,filled", fillcolor="#e8f1fb"'
                  if n.terminal else 'shape=ellipse, style=filled, fillcolor="#fdf3d8"')
        lineas.append(f'  {mi_id} [label="{escapar(n.etiqueta)}", {estilo}];')
        for h in n.hijos:
            hid = visitar(h)
            lineas.append(f"  {mi_id} -> {hid};")
        return mi_id

    visitar(nodo)
    lineas.append("}")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
#  AST
# ---------------------------------------------------------------------------
@dataclass
class Valor:
    tipo: str       # 'NUM' | 'BOOL' | 'ID'
    texto: str

    def a_nodo(self):
        return Nodo(f"{self.texto}  [{self.tipo}]", terminal=True)


@dataclass
class Comparacion:
    variable: str
    operador: str
    valor: Valor

    def a_nodo(self):
        return Nodo(self.operador, [Nodo(f"{self.variable}  [ID]", terminal=True),
                                    self.valor.a_nodo()])


@dataclass
class Not:
    operando: object

    def a_nodo(self):
        return Nodo("NOT", [self.operando.a_nodo()])


@dataclass
class And:
    izq: object
    der: object

    def a_nodo(self):
        return Nodo("AND", [self.izq.a_nodo(), self.der.a_nodo()])


@dataclass
class Or:
    izq: object
    der: object

    def a_nodo(self):
        return Nodo("OR", [self.izq.a_nodo(), self.der.a_nodo()])


@dataclass
class Accion:
    nombre: str
    objeto: str
    parametros: list

    def a_nodo(self):
        hijos = [Nodo(f"objeto: {self.objeto}", terminal=True)]
        hijos += [Nodo(f"param: {p.texto} [{p.tipo}]", terminal=True) for p in self.parametros]
        return Nodo(f"Acción: {self.nombre}", hijos)


@dataclass
class Regla:
    condicion: object
    acciones: list
    linea: int = 1

    def a_nodo(self):
        return Nodo(f"Regla (línea {self.linea})", [
            Nodo("Condición", [self.condicion.a_nodo()]),
            Nodo("Acciones", [a.a_nodo() for a in self.acciones]),
        ])


@dataclass
class Programa:
    reglas: list

    def a_nodo(self):
        return Nodo("Programa", [r.a_nodo() for r in self.reglas])
