#!/usr/bin/env python3
"""
Genera informe/Informe_DomoDSL.tex a partir del código del proyecto, de modo que las tablas
(producciones, FIRST, FOLLOW, tabla LL(1), pruebas) del informe sean EXACTAMENTE las que calcula
el programa. Luego compilar con:  xelatex Informe_DomoDSL.tex   (dos veces)

Ejecutar desde la carpeta informe/:   python generar_informe.py
"""
import json
import os
import re
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import gramatica as g                                   # noqa: E402
from arbol import a_texto                               # noqa: E402
from lexer import analizador_lexico                     # noqa: E402
from parser_ll1 import parsear_ll1                      # noqa: E402
from parser_rd import parsear                           # noqa: E402

with open(os.path.join(RAIZ, "docs", "resultados_pruebas.json"), encoding="utf-8") as f:
    PRUEBAS = json.load(f)


# ----------------------------------------------------------------------------- utilidades LaTeX
def esc(s):
    s = s.replace("\\", "\x00")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"), ("_", r"\_"),
                 ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"),
                 ("^", r"\textasciicircum{}")]:
        s = s.replace(a, b)
    return s.replace("\x00", r"\textbackslash{}")


def tt(s):
    return r"\texttt{" + esc(s) + "}"


def nt(a):
    """No terminal en cursiva; programa_p se muestra como programa'."""
    base = a[:-2] if a.endswith("_p") else a
    return r"\textit{" + esc(base) + "}" + ("$'$" if a.endswith("_p") else "")


def simbolo(s):
    if s == g.EPS:
        return r"$\varepsilon$"
    return nt(s) if g.es_no_terminal(s) else tt(s)


def conjunto(c):
    orden = {s: i for i, s in enumerate(g.TERMINALES_TABLA + [g.EPS])}
    elems = sorted(c, key=lambda s: orden.get(s, 99))
    return r"$\{$ " + ", ".join(simbolo(e) for e in elems) + r" $\}$"


def produccion_tex(i):
    a, rhs = g.PRODUCCIONES[i - 1]
    return nt(a) + r" $\rightarrow$ " + " ".join(simbolo(s) for s in rhs)


def numerar_linea(archivo, patron, desde=0):
    with open(os.path.join(RAIZ, archivo), encoding="utf-8") as f:
        for n, linea in enumerate(f, start=1):
            if n > desde and re.search(patron, linea):
                return n
    raise ValueError(patron)


# ----------------------------------------------------------------------------- tablas generadas
def tabla_producciones():
    filas = [r"\begin{longtable}{@{}r p{11cm}@{}}", r"\toprule", r"\textbf{N.º} & \textbf{Producción} \\",
             r"\midrule", r"\endhead"]
    for i in range(1, len(g.PRODUCCIONES) + 1):
        filas.append(f"{i} & {produccion_tex(i)} \\\\")
    filas += [r"\bottomrule", r"\end{longtable}"]
    return "\n".join(filas)


JUST_FIRST = {
    "programa": "Prod. 1: empieza por \\textit{regla}, que no deriva $\\varepsilon$; FIRST(programa) = FIRST(regla).",
    "programa_p": "Prod. 2: FIRST(regla) = \\{WHEN\\}; prod. 3 aporta $\\varepsilon$.",
    "regla": "Prod. 4: empieza con el terminal WHEN.",
    "condicion": "Prod. 5: \\textit{termino} no es anulable, luego FIRST(condicion) = FIRST(termino).",
    "condicion_p": "Prod. 6 empieza con OR; prod. 7 aporta $\\varepsilon$.",
    "termino": "Prod. 8: \\textit{factor} no es anulable, luego FIRST(termino) = FIRST(factor).",
    "termino_p": "Prod. 9 empieza con AND; prod. 10 aporta $\\varepsilon$.",
    "factor": "Prod. 11: NOT; prod. 12: PARENT\\_IZQ; prod. 13: FIRST(comparacion) = \\{ID\\}.",
    "comparacion": "Prod. 14: empieza con el terminal ID.",
    "valor": "Prods. 15--18: NUM, TRUE, FALSE e ID.",
    "acciones": "Prod. 19: FIRST(accion) = \\{ID\\}; \\textit{accion} no es anulable.",
    "acciones_p": "Prod. 20 empieza con COMA; prod. 21 aporta $\\varepsilon$.",
    "accion": "Prod. 22: empieza con el terminal ID.",
    "parametros": "Prod. 23: FIRST(valor); prod. 24 aporta $\\varepsilon$.",
}

JUST_FOLLOW = {
    "programa": "Símbolo inicial: se agrega \\$.",
    "programa_p": "Prod. 1: \\textit{programa'} está al final, luego FOLLOW(programa) $\\subseteq$ FOLLOW(programa'); la prod. 2 solo repite la regla.",
    "regla": "Prods. 1 y 2: sigue \\textit{programa'}; FIRST(programa')$\\setminus\\{\\varepsilon\\}$ = \\{WHEN\\} y como es anulable se agrega FOLLOW(programa') = \\{\\$\\}.",
    "condicion": "Prod. 4: sigue THEN. Prod. 12: sigue PARENT\\_DER.",
    "condicion_p": "Prods. 5 y 6: va al final, luego hereda FOLLOW(condicion).",
    "termino": "Prods. 5 y 6: sigue \\textit{condicion'}; FIRST = \\{OR\\} y es anulable, luego se agrega FOLLOW(condicion).",
    "termino_p": "Prods. 8 y 9: va al final, luego hereda FOLLOW(termino).",
    "factor": "Prods. 8 y 9: sigue \\textit{termino'}: AND, y por ser anulable FOLLOW(termino). Prod. 11 (NOT factor): hereda FOLLOW(factor) (sin efecto nuevo).",
    "comparacion": "Prod. 13: va al final, luego hereda FOLLOW(factor).",
    "valor": "Prod. 14: va al final, hereda FOLLOW(comparacion). Prod. 23: sigue \\textit{parametros}: FIRST(parametros)$\\setminus\\{\\varepsilon\\}$ y, al ser anulable, FOLLOW(parametros).",
    "acciones": "Prod. 4: sigue PUNTO\\_COMA.",
    "acciones_p": "Prods. 19 y 20: va al final, luego hereda FOLLOW(acciones).",
    "accion": "Prods. 19 y 20: sigue \\textit{acciones'}: COMA, y por ser anulable FOLLOW(acciones) (y FOLLOW(acciones')).",
    "parametros": "Prod. 22: va al final, hereda FOLLOW(accion). Prod. 23: va al final, hereda FOLLOW(parametros).",
}


def tabla_conjuntos(nombre, datos, just):
    filas = [r"\begin{longtable}{@{}>{\raggedright\arraybackslash}p{2.6cm} >{\raggedright\arraybackslash}p{5.3cm} >{\raggedright\arraybackslash}p{6.9cm}@{}}",
             r"\toprule", rf"\textbf{{No terminal}} & \textbf{{{nombre}}} & \textbf{{Justificación}} \\",
             r"\midrule", r"\endhead"]
    for a in g.NO_TERMINALES:
        filas.append(f"{nt(a)} & {conjunto(datos[a])} & \\footnotesize {just[a]} \\\\")
    filas += [r"\bottomrule", r"\end{longtable}"]
    return "\n".join(filas)


def tabla_ll1():
    cols = g.TERMINALES_TABLA
    filas = [r"\begin{tabular}{@{}l|" + r">{\centering\arraybackslash}p{1.4cm}" * len(cols) + r"@{}}", r"\toprule",
             " & " + " & ".join(rf"{{\fontsize{{6.5}}{{7}}\selectfont {tt(t)}}}" for t in cols) + r" \\", r"\midrule"]
    for a in g.NO_TERMINALES:
        celdas = [str(g.TABLA[a].get(t, "")) for t in cols]
        celdas = [rf"\cellcolor{{celda}}\textbf{{{c}}}" if c else "" for c in celdas]
        filas.append(f"{nt(a)} & " + " & ".join(celdas) + r" \\")
    filas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(filas)


def tabla_select():
    filas = [r"\begin{longtable}{@{}>{\raggedright\arraybackslash}p{2.3cm} >{\raggedright\arraybackslash}p{4.0cm} >{\raggedright\arraybackslash}p{5.9cm} c@{}}",
             r"\toprule", r"\textbf{No terminal} & \textbf{Producción} & \textbf{Conjunto de selección} & \textbf{¿Disjuntos?} \\",
             r"\midrule", r"\endhead"]
    for a in g.NO_TERMINALES:
        prods = g.producciones_de(a)
        if len(prods) < 2:
            continue
        selecciones = []
        for n, rhs in prods:
            f = g.first_de_cadena(rhs, g.FIRST)
            sel = set(f - {g.EPS})
            if g.EPS in f:
                sel |= g.FOLLOW[a]
            selecciones.append((n, sel))
        disjuntos = all(not (selecciones[i][1] & selecciones[j][1])
                        for i in range(len(selecciones)) for j in range(i + 1, len(selecciones)))
        for k, (n, sel) in enumerate(selecciones):
            cab = nt(a) if k == 0 else ""
            fin = (r"\textbf{sí}" if disjuntos else r"\textbf{NO}") if k == 0 else ""
            filas.append(f"{cab} & ({n}) {produccion_tex(n).split(r'$\rightarrow$')[1]} & {conjunto(sel)} & {fin} \\\\")
        filas.append(r"\midrule")
    filas[-1] = r"\bottomrule"
    filas.append(r"\end{longtable}")
    return "\n".join(filas)


def derivacion_izquierda(entrada):
    """Derivación por la izquierda reconstruida a partir de la traza del parser LL(1)."""
    traza = []
    parsear_ll1(analizador_lexico(entrada), traza)
    nums = [int(re.match(r"\((\d+)\)", acc).group(1)) for _, _, acc in traza if acc.startswith("(")]
    forma = [g.SIMBOLO_INICIAL]
    filas = [(0, "", list(forma))]
    for n in nums:
        pos = next(i for i, s in enumerate(forma) if g.es_no_terminal(s))
        _, rhs = g.PRODUCCIONES[n - 1]
        forma[pos:pos + 1] = [s for s in rhs if s != g.EPS]
        filas.append((len(filas), n, list(forma)))
    return filas


def tabla_derivacion(entrada):
    filas = [r"\begin{longtable}{@{}r r >{\raggedright\arraybackslash}p{12.2cm}@{}}", r"\toprule",
             r"\textbf{Paso} & \textbf{Prod.} & \textbf{Forma sentencial (derivación por la izquierda)} \\",
             r"\midrule", r"\endhead"]
    for paso, n, forma in derivacion_izquierda(entrada):
        flecha = "" if paso == 0 else r"$\Rightarrow$ "
        filas.append(f"{paso} & {n} & {flecha}\\footnotesize " + " ".join(simbolo(s) for s in forma) + r" \\")
    filas += [r"\bottomrule", r"\end{longtable}"]
    return "\n".join(filas)


# ---- pruebas -----------------------------------------------------------------------------------
MOSTRAR = {
    "L02": "(espacios, tabulaciones y saltos de línea)",
    "L05": "WHEN ((((((((((((((((((((a > 1)))))))))))))))))))) THEN x y;  [20 niveles]",
    "L06": "WHEN s0 > 0 AND s1 > 1 AND ... AND s199 > 199 THEN x y;  [200 comparaciones]",
    "L07": "WHEN s0 > 0 THEN activar r0;  ...  WHEN s99 > 99 THEN activar r99;  [100 reglas]",
    "L01": "(cadena vacía)",
}


def abreviar_mensaje(m):
    r = re.match(r"(Error \w+) \(línea (\d+), columna (\d+), posición \d+\): (.*)$", m, re.S)
    return f"{r.group(1)} [{r.group(2)}:{r.group(3)}]: {r.group(4)}" if r else m


def tabla_pruebas(categoria):
    from casos_prueba import CASOS
    meta = {c[0]: c for c in CASOS}
    filas = [r"\begin{longtable}{@{}>{\raggedright\arraybackslash}p{0.9cm} >{\raggedright\arraybackslash}p{6.4cm} >{\raggedright\arraybackslash}p{3.2cm} >{\raggedright\arraybackslash}p{6.8cm} >{\raggedright\arraybackslash}p{4.4cm}@{}}",
             r"\toprule", r"\textbf{ID} & \textbf{Entrada} & \textbf{Resultado esperado} & \textbf{Resultado obtenido} & \textbf{Observación} \\",
             r"\midrule", r"\endhead"]
    for p in PRUEBAS:
        if p["categoria"] != categoria:
            continue
        cid = p["id"]
        entrada = MOSTRAR.get(cid, p["entrada"].replace("\n", "\\n").replace("\t", "\\t"))
        frag = meta[cid][4]
        esperado = "ACEPTA" if p["esperado"] == "ACEPTA" else f"RECHAZA (el mensaje menciona «{frag}»)"
        if p["obtenido"] == "ACEPTA":
            obtenido = r"ACEPTA \ok"
        else:
            obtenido = r"RECHAZA \ok\newline \scriptsize " + esc(abreviar_mensaje(p["mensaje"]))
        filas.append(f"{cid} & \\footnotesize {tt(entrada)} & \\footnotesize {esc(esperado)} & \\footnotesize {obtenido} & \\footnotesize {esc(p['observacion'])} \\\\")
        filas.append(r"\addlinespace[2pt]")
    filas += [r"\bottomrule", r"\end{longtable}"]
    return "\n".join(filas)


def tabla_errores():
    ids = ["I01", "I02", "I03", "I05", "I06", "I07", "I08", "I09", "I10", "I15"]
    filas = [r"\begin{longtable}{@{}l >{\raggedright\arraybackslash}p{5.2cm} >{\raggedright\arraybackslash}p{8.4cm}@{}}",
             r"\toprule", r"\textbf{Caso} & \textbf{Entrada} & \textbf{Mensaje entregado por el analizador} \\", r"\midrule", r"\endhead"]
    for p in PRUEBAS:
        if p["id"] in ids:
            filas.append(f"{p['id']} & \\footnotesize {tt(p['entrada'])} & \\footnotesize {esc(abreviar_mensaje(p['mensaje']))} \\\\")
            filas.append(r"\addlinespace[2pt]")
    filas += [r"\bottomrule", r"\end{longtable}"]
    return "\n".join(filas)


def tabla_errores_ll1():
    ids = ["I01", "I02", "I10"]
    filas = [r"\begin{longtable}{@{}l >{\raggedright\arraybackslash}p{4.4cm} >{\raggedright\arraybackslash}p{9.2cm}@{}}",
             r"\toprule", r"\textbf{Caso} & \textbf{Entrada} & \textbf{Mensaje del analizador dirigido por tabla} \\", r"\midrule", r"\endhead"]
    for p in PRUEBAS:
        if p["id"] in ids:
            filas.append(f"{p['id']} & \\footnotesize {tt(p['entrada'])} & \\footnotesize {esc(abreviar_mensaje(p['mensaje_ll1']))} \\\\")
            filas.append(r"\addlinespace[2pt]")
    filas += [r"\bottomrule", r"\end{longtable}"]
    return "\n".join(filas)


def extracto(archivo, inicio_patron, fin_patron, caption):
    ini = numerar_linea(archivo, inicio_patron)
    fin = numerar_linea(archivo, fin_patron, desde=ini) - 1
    return (rf"\lstinputlisting[firstline={ini}, lastline={fin}, firstnumber={ini}, caption={{{caption}}}]"
            rf"{{../{archivo}}}")


# ----------------------------------------------------------------------------- documento
EJ_ENUNCIADO = "WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;"
EJ_EXT = ("WHEN NOT (puerta == TRUE) AND (hora >= 22 OR hora < 6) "
          "THEN bloquear puerta_principal, ajustar termostato 22;")
EJ_SIMPLE = "WHEN a > 1 THEN x y;"

n_val = sum(p["categoria"] == "válida" for p in PRUEBAS)
n_inv = sum(p["categoria"] == "inválida" for p in PRUEBAS)
n_lim = sum(p["categoria"] == "límite" for p in PRUEBAS)
n_ok = sum(p["ok"] for p in PRUEBAS)

PREAMBULO = r"""
\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{spanish}
\setmainfont{TeX Gyre Pagella}
\setmonofont{DejaVu Sans Mono}[Scale=0.8]
\emergencystretch=3em
\usepackage[margin=2.5cm]{geometry}
\usepackage{booktabs,longtable,array,graphicx,xcolor,colortbl,listings,fancyhdr,titlesec,enumitem,caption,float,pdflscape,microtype,amssymb,amsmath}
\usepackage[hidelinks]{hyperref}
\definecolor{azul}{HTML}{1F3A5F}
\definecolor{celda}{HTML}{E4EEF9}
\definecolor{gris}{HTML}{F5F5F5}
\definecolor{verde}{HTML}{2E7D32}
\titleformat{\section}{\Large\bfseries\color{azul}}{\thesection}{0.6em}{}
\titleformat{\subsection}{\large\bfseries\color{azul}}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}{\normalsize\bfseries\color{azul}}{\thesubsubsection}{0.6em}{}
\setlength{\parskip}{4pt}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small INFO1148 --- Proyecto de Análisis Sintáctico}
\fancyhead[R]{\small DomoDSL}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.3pt}
\captionsetup{font=small,labelfont=bf}
\lstset{basicstyle=\ttfamily\footnotesize, numbers=left, numberstyle=\tiny\color{gray}, numbersep=6pt,
  breaklines=true, breakatwhitespace=false, frame=single, rulecolor=\color{gray!60}, backgroundcolor=\color{gris},
  language=Python, keywordstyle=\color{azul}\bfseries, commentstyle=\color{verde}\itshape,
  stringstyle=\color{red!50!black}, showstringspaces=false, tabsize=4, columns=fullflexible,
  captionpos=b, xleftmargin=1.2em, framexleftmargin=1.2em}
\newcommand{\ok}{\textcolor{verde}{\ensuremath{\checkmark}}}
\begin{document}
"""

PORTADA = r"""
\begin{titlepage}
\centering
{\large Universidad Católica de Temuco\\ Ingeniería Civil Informática\par}
\vspace{0.6cm}
{\large Teoría de la Computación --- INFO1148\par}
\vspace{2.2cm}
{\Large\bfseries\color{azul} Proyecto: Diseño e implementación de un analizador sintáctico\par}
\vspace{0.6cm}
{\Huge\bfseries\color{azul} DomoDSL\par}
\vspace{0.3cm}
{\large Un lenguaje de reglas para la automatización de una casa inteligente (IoT)\par}
\vspace{1.4cm}
{\large Gramática libre de contexto \textperiodcentered{} FIRST y FOLLOW \textperiodcentered{} Tabla LL(1)\\
Parser predictivo \textperiodcentered{} AST \textperiodcentered{} Manejo de errores\par}
\vspace{2.6cm}
\begin{tabular}{rl}
\textbf{Integrantes:} & [Nombre Apellido 1] \\
 & [Nombre Apellido 2] \\
 & [Nombre Apellido 3] \\[6pt]
\textbf{Docente:} & [Nombre del docente] \\[6pt]
\textbf{Fecha:} & Octubre de 2026 \\[6pt]
\textbf{Repositorio:} & \texttt{https://github.com/[usuario]/[repositorio]}
\end{tabular}
\vfill
{\small Implementación en Python 3 \textperiodcentered{} sin generadores de parsers \textperiodcentered{} solo biblioteca estándar\par}
\end{titlepage}
\tableofcontents
\clearpage
"""

S1 = r"""
\section{Introducción y dominio seleccionado}

Los lenguajes de programación y los lenguajes de dominio específico (DSL) necesitan mecanismos que verifiquen si
una secuencia de símbolos cumple una estructura formal. Este proyecto diseña e implementa, \emph{desde cero},
un analizador sintáctico para un pequeño DSL, aplicando los contenidos del curso: gramáticas libres de contexto (GLC),
eliminación de recursión por la izquierda, factorización, conjuntos FIRST y FOLLOW, tabla predictiva LL(1),
construcción de árboles sintácticos y detección de errores.

\paragraph{Dominio escogido.} Se eligió la \textbf{automatización de una casa inteligente (IoT)}, el ejemplo
orientativo del enunciado. El usuario describe \emph{reglas} del tipo ``cuando ocurra esta condición, ejecuta estas acciones'':
\begin{center}\texttt{WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;}\end{center}
Este dominio es adecuado porque (i)~las reglas condición--acción son naturales y fáciles de validar, (ii)~las condiciones admiten
conectores lógicos, negación y agrupación, lo que obliga a resolver precedencia y asociatividad en la gramática, y
(iii)~las acciones admiten parámetros, lo que enriquece la sintaxis sin perder la propiedad LL(1).

\paragraph{Alcance.} El lenguaje se llama \textbf{DomoDSL}. Se entregan: la especificación del lenguaje, la GLC y su
análisis, FIRST/FOLLOW, la tabla LL(1), \textbf{dos} analizadores predictivos (descenso recursivo y dirigido por tabla),
AST y árbol de derivación, mensajes de error localizados, """ + f"{len(PRUEBAS)}" + r""" casos de prueba y 18 pruebas unitarias.

\paragraph{Estructura del informe.} Sigue la organización sugerida en el enunciado: especificación del lenguaje
(sección~2), gramática (3), análisis (4), FIRST y FOLLOW (5), tabla LL(1) (6), parser (7), árboles (8), errores (9),
pruebas (10), conclusiones (11) y anexos (12).
"""

S2 = r"""
\section{Especificación del lenguaje}

\subsection{Propósito}
DomoDSL permite escribir programas formados por una o más \textbf{reglas de automatización}. Cada regla evalúa una
\textbf{condición} sobre variables del hogar (temperatura, humedad, movimiento, hora, \dots) y, si se cumple, ordena
una o más \textbf{acciones} sobre dispositivos (ventilador, alarma, termostato, \dots). El lenguaje no ejecuta las
reglas: el objetivo del proyecto es \emph{reconocerlas} (decidir si son sintácticamente válidas), informar errores
útiles y producir una representación estructurada (AST).

\subsection{Alfabeto}
El alfabeto relevante $\Sigma$ está formado por:
\begin{itemize}[nosep]
\item letras \texttt{A--Z} y \texttt{a--z}, dígitos \texttt{0--9}, el guion bajo \texttt{\_} y el punto \texttt{.} (solo dentro de números decimales);
\item los símbolos \texttt{>}, \texttt{<}, \texttt{=}, \texttt{!}, \texttt{;}, \texttt{,}, \texttt{(} y \texttt{)};
\item espacio, tabulación y salto de línea (separadores que el lexer descarta).
\end{itemize}
Cualquier otro carácter produce un \emph{error léxico}.

\subsection{Categorías de tokens}
El analizador léxico (basado en el entregado por el docente) usa expresiones regulares. Los espacios se descartan.
Las palabras reservadas \textbf{no distinguen mayúsculas de minúsculas} (como en la función base).

\begin{center}\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.5cm} >{\raggedright\arraybackslash}p{4.0cm} >{\raggedright\arraybackslash}p{4.3cm} >{\raggedright\arraybackslash}p{3.3cm}@{}}
\toprule
\textbf{Token} & \textbf{Patrón} & \textbf{Descripción} & \textbf{Ejemplos} \\
\midrule
""" + " \\\\\n".join([
    f"{tt(a)} & {tt(b)} & {c} & {tt(d)}" for a, b, c, d in [
        ("WHEN, THEN", "WHEN | THEN", "Inicio y separador de la regla", "WHEN, then"),
        ("AND, OR, NOT", "AND | OR | NOT", "Operadores lógicos", "AND, not"),
        ("TRUE, FALSE", "TRUE | FALSE", "Valores booleanos", "TRUE"),
        ("ID", r"[A-Za-z_][A-Za-z0-9_]*", "Identificadores (variables, verbos y dispositivos)", "temperatura, sensor_1"),
        ("NUM", r"\d+(\.\d+)?", "Números enteros o decimales", "28, 0.5"),
        ("OP_REL", ">= | <= | == | != | > | <", "Operadores relacionales", ">=, =="),
        ("PUNTO_COMA", ";", "Fin de regla", ";"),
        ("COMA", ",", "Separador de acciones", ","),
        ("PARENT_IZQ", "(", "Abre agrupación", "("),
        ("PARENT_DER", ")", "Cierra agrupación", ")"),
    ]]) + r""" \\
\bottomrule
\end{tabular}
\end{center}

Un identificador cuyo texto coincide con una palabra reservada se convierte en el token reservado
(p.\,ej. \texttt{when} $\to$ \texttt{WHEN}), por lo que las palabras reservadas no pueden usarse como identificadores.
Al final de la entrada el lexer agrega el token \texttt{\$} (fin de entrada), que necesita el analizador LL(1).

\subsection{Cumplimiento de los requisitos mínimos del enunciado}
\begin{center}\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{5.6cm} >{\raggedright\arraybackslash}p{9.4cm}@{}}
\toprule
\textbf{Requisito} & \textbf{Cómo lo cumple DomoDSL} \\
\midrule
Al menos 4 palabras reservadas & 7: \texttt{WHEN}, \texttt{THEN}, \texttt{AND}, \texttt{OR}, \texttt{NOT}, \texttt{TRUE}, \texttt{FALSE} \\
Identificadores & Token \texttt{ID} \\
Valores numéricos y/o booleanos & \texttt{NUM} (enteros y decimales) y \texttt{TRUE}/\texttt{FALSE} \\
Al menos 3 operadores & 9: seis relacionales (\texttt{> < >= <= == !=}) y tres lógicos (\texttt{AND OR NOT}) \\
Estructura de sentencia principal & \texttt{WHEN <condición> THEN <acciones> ;} \\
Más de una sentencia & Un programa es una secuencia de una o más reglas \\
Construcción compuesta & Conectores \texttt{AND}/\texttt{OR}, paréntesis y listas de acciones con parámetros \\
Extensión creativa & \texttt{NOT}, paréntesis, múltiples acciones y acciones con parámetros (sección~4.6) \\
\bottomrule
\end{tabular}
\end{center}

\subsection{Ejemplos de sentencias válidas e inválidas}
\paragraph{Válidas.}
\begin{enumerate}[nosep]
\item \texttt{WHEN temperatura > 28 THEN encender ventilador;}
\item \texttt{WHEN movimiento == TRUE THEN activar alarma;}
\item \texttt{WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;}
\item \texttt{WHEN luz < 100 OR hora >= 20 THEN encender lampara;}
\item \texttt{WHEN NOT puerta == TRUE THEN activar alarma;}
\item \texttt{WHEN (temperatura > 30 OR humedad > 80) AND presencia == TRUE THEN encender aire;}
\item \texttt{WHEN temperatura > 28 THEN encender ventilador 3, activar alarma;}
\end{enumerate}
\paragraph{Inválidas.}
\begin{center}\small
\begin{tabular}{@{}l >{\raggedright\arraybackslash}p{7.2cm} >{\raggedright\arraybackslash}p{6.3cm}@{}}
\toprule
\textbf{N.º} & \textbf{Sentencia} & \textbf{Motivo} \\
\midrule
1 & \texttt{WHEN temperatura > 28 encender ventilador;} & Falta la palabra reservada \texttt{THEN} \\
2 & \texttt{WHEN temperatura > THEN encender ventilador;} & Falta el valor después de \texttt{>} \\
3 & \texttt{temperatura > 28 THEN encender ventilador;} & La regla no comienza con \texttt{WHEN} \\
4 & \texttt{WHEN temperatura > 28 THEN encender ventilador} & Falta el \texttt{;} final \\
5 & \texttt{WHEN (temperatura > 28 THEN encender ventilador;} & Paréntesis sin cerrar \\
6 & \texttt{WHEN temperatura = 28 THEN encender ventilador;} & \texttt{=} no es un operador (debe ser \texttt{==}): error léxico \\
\bottomrule
\end{tabular}
\end{center}
"""

S3 = r"""
\section{Gramática libre de contexto}

La gramática de DomoDSL es $G = (N, T, P, S)$ con:
\begin{itemize}[nosep]
\item \textbf{No terminales} $N$ (14): """ + ", ".join(nt(a) for a in g.NO_TERMINALES) + r""".
\item \textbf{Terminales} $T$ (14, son los tokens): """ + ", ".join(tt(t) for t in g.TERMINALES) + r""".
\item \textbf{Símbolo inicial} $S$ = \textit{programa}.
\item \textbf{Producciones} $P$: las 24 que muestra la tabla siguiente. (Las producciones numeradas son las que usa el
código; el símbolo \textit{x}$'$ se escribe \texttt{x\_p} en el programa.)
\end{itemize}

""" + tabla_producciones() + r"""

\paragraph{Lectura de la gramática.}
\begin{itemize}[nosep]
\item Un \textbf{programa} es una o más reglas (1--3). Una \textbf{regla} es \texttt{WHEN condición THEN acciones ;} (4).
\item Las \textbf{condiciones} se estratifican en tres niveles para codificar la precedencia: \textit{condicion} (OR, la menor),
\textit{termino} (AND) y \textit{factor} (NOT, paréntesis y comparaciones, la mayor) (5--13). Una \textbf{comparación} es
\texttt{ID OP\_REL valor} (14) y un \textbf{valor} es un número, un booleano o un identificador (15--18).
\item Las \textbf{acciones} son una lista separada por comas (19--21); cada una es \texttt{verbo dispositivo [parámetros]} (22--24), donde los
parámetros son cero o más valores.
\end{itemize}

\paragraph{Ejemplo de derivación.} Derivación por la izquierda de \texttt{""" + esc(EJ_SIMPLE) + r"""} (los terminales se muestran como
tipos de token: \texttt{ID}, \texttt{OP\_REL}, \texttt{NUM}, \dots). La derivación fue reconstruida a partir de la traza del analizador LL(1).

""" + tabla_derivacion(EJ_SIMPLE) + "\n"

S4 = r"""
\section{Análisis de la gramática}

\subsection{Terminales, no terminales y símbolo inicial}
Ya identificados en la sección~3: 14 terminales (los tokens), 14 no terminales y símbolo inicial \textit{programa}.
Los no terminales \textit{programa'}, \textit{condicion'}, \textit{termino'}, \textit{acciones'} son \emph{auxiliares}
introducidos al transformar la gramática; el resto tiene significado propio del dominio.

\subsection{Primera versión de la gramática ($G_0$)}
Al escribir la gramática de forma natural se obtiene:
\begin{lstlisting}[language={},numbers=none]
programa    → regla programa | regla
regla       → WHEN condicion THEN acciones PUNTO_COMA
condicion   → condicion OR condicion | condicion AND condicion
            | NOT condicion | PARENT_IZQ condicion PARENT_DER | comparacion
comparacion → ID OP_REL valor
valor       → NUM | TRUE | FALSE | ID
acciones    → acciones COMA accion | accion
accion      → ID ID parametros
parametros  → parametros valor | ε
\end{lstlisting}
$G_0$ describe el lenguaje deseado, pero \textbf{no sirve para un analizador predictivo}: tiene recursión por la
izquierda, prefijos comunes y es ambigua. A continuación se analiza cada problema.

\subsection{Recursión por la izquierda}
En $G_0$ hay recursión izquierda \emph{directa} en tres no terminales: \textit{condicion} ($\textit{condicion}\to\textit{condicion}\ \texttt{OR}\ \dots$),
\textit{acciones} y \textit{parametros}. Un parser de descenso recursivo entraría en bucle infinito. Se aplica la
transformación estándar $A\to A\alpha\mid\beta \;\Longrightarrow\; A\to\beta A',\ A'\to\alpha A'\mid\varepsilon$:

\begin{center}\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{5.2cm} >{\raggedright\arraybackslash}p{7.3cm} >{\raggedright\arraybackslash}p{2.6cm}@{}}
\toprule
\textbf{Original ($G_0$)} & \textbf{Transformado} & \textbf{En la gramática final} \\
\midrule
$\textit{acciones}\to\textit{acciones}\ \texttt{COMA}\ \textit{accion}\mid\textit{accion}$ &
$\textit{acciones}\to\textit{accion}\ \textit{acciones'}$ & prods. 19--21 \\
 & $\textit{acciones'}\to\texttt{COMA}\ \textit{accion}\ \textit{acciones'}\mid\varepsilon$ & \\
$\textit{parametros}\to\textit{parametros}\ \textit{valor}\mid\varepsilon$ &
$\textit{parametros}\to\textit{valor}\ \textit{parametros}\mid\varepsilon$ (recursión por la derecha, equivalente) & prods. 23--24 \\
$\textit{condicion}\to\textit{condicion}\ \texttt{OR}\ \textit{termino}\mid\textit{termino}$ &
$\textit{condicion}\to\textit{termino}\ \textit{condicion'}$ & prods. 5--7 \\
 & $\textit{condicion'}\to\texttt{OR}\ \textit{termino}\ \textit{condicion'}\mid\varepsilon$ & \\
$\textit{termino}\to\textit{termino}\ \texttt{AND}\ \textit{factor}\mid\textit{factor}$ &
$\textit{termino}\to\textit{factor}\ \textit{termino'}$ & prods. 8--10 \\
 & $\textit{termino'}\to\texttt{AND}\ \textit{factor}\ \textit{termino'}\mid\varepsilon$ & \\
\bottomrule
\end{tabular}
\end{center}

\paragraph{Verificación en la gramática final.} No hay recursión izquierda directa (lo comprueba una prueba unitaria: ninguna producción
empieza con su propio lado izquierdo). Tampoco indirecta: las dependencias por el primer símbolo forman cadenas sin ciclos:
\begin{itemize}[nosep]
\item $\textit{programa}\to\textit{regla}\to\texttt{WHEN}$;
\item $\textit{condicion}\to\textit{termino}\to\textit{factor}\to\textit{comparacion}\to\texttt{ID}$;
\item $\textit{acciones}\to\textit{accion}\to\texttt{ID}$.
\end{itemize}
La única recursión de \textit{factor} ($\textit{factor}\to\texttt{NOT}\ \textit{factor}$) empieza con un terminal, por lo que es inofensiva.

\subsection{Factorización por la izquierda}
En $G_0$, \textit{programa} tiene dos alternativas con prefijo común \textit{regla}
($\textit{programa}\to\textit{regla}\ \textit{programa}\mid\textit{regla}$): con un solo token de lookahead no se
puede elegir. Se factoriza: $\textit{programa}\to\textit{regla}\ \textit{programa'}$ con
$\textit{programa'}\to\textit{programa}\mid\varepsilon$; como $\textit{programa}$ empieza con $\textit{regla}$, se
sustituye y queda $\textit{programa'}\to\textit{regla}\ \textit{programa'}\mid\varepsilon$ (prods. 1--3).
En el resto de la gramática las alternativas de un mismo no terminal comienzan con terminales distintos
(p.\,ej. \textit{factor}: \texttt{NOT}, \texttt{PARENT\_IZQ}, \texttt{ID}), por lo que \textbf{no se requiere más factorización}; esto se
confirma formalmente en la sección~6 (conjuntos de selección disjuntos).

\subsection{Ambigüedad}
$G_0$ es \textbf{ambigua}: la cadena \texttt{a > 1 OR b > 2 AND c > 3} tiene dos árboles de derivación, según si la
producción $\textit{condicion}\to\textit{condicion}\ \texttt{OR}\ \textit{condicion}$ o
$\textit{condicion}\to\textit{condicion}\ \texttt{AND}\ \textit{condicion}$ se aplica en la raíz:
\begin{center}
\texttt{(a > 1 OR b > 2) AND c > 3} \quad frente a \quad \texttt{a > 1 OR (b > 2 AND c > 3)}.
\end{center}
Además \texttt{a OR b OR c} puede agruparse a la izquierda o a la derecha (ambigüedad de asociatividad). Esto cambiaría
el significado del programa, así que debe eliminarse en la gramática, no en el código.

\paragraph{Solución.} Se separan los \textbf{niveles de precedencia} (\textit{condicion} para OR, \textit{termino} para AND,
\textit{factor} para NOT/paréntesis/comparación): AND liga más fuerte que OR, y NOT más que AND. Con las producciones
5--13 la cadena anterior tiene un único árbol, el de \texttt{a > 1 OR (b > 2 AND c > 3)}. La asociatividad es
\textbf{izquierda}: el AST se construye en un ciclo que agrupa \texttt{((a OR b) OR c)} (sección~7).
Como además la gramática final es LL(1) (sección~6), es \textbf{no ambigua} (toda gramática LL(1) lo es).
La guía del enunciado (\textit{condicion2} con AND/OR mezclados) no define precedencia entre ambos conectores; la estratificación
usada aquí sí lo hace.

Otro punto revisado: en \textit{accion}, los parámetros son identificadores/valores y podrían confundirse con el
siguiente elemento; no hay ambigüedad porque la lista de parámetros termina siempre en \texttt{;} o \texttt{,}
(FOLLOW(parametros) = \{\texttt{PUNTO\_COMA}, \texttt{COMA}\}, ver sección~5).

\subsection{Extensión creativa y su efecto en la gramática}
La extensión de DomoDSL tiene tres componentes, todos integrados en la gramática, FIRST/FOLLOW, tabla, código y pruebas:
\begin{enumerate}[nosep]
\item \textbf{Negación} \texttt{NOT}: $\textit{factor}\to\texttt{NOT}\ \textit{factor}$ (prod.~11); permite \texttt{NOT NOT x == 1}.
\item \textbf{Agrupación con paréntesis}: $\textit{factor}\to\texttt{PARENT\_IZQ}\ \textit{condicion}\ \texttt{PARENT\_DER}$ (prod.~12); es la que introduce
\texttt{PARENT\_DER} en FOLLOW(\textit{condicion}) y justifica los mensajes ``falta \texttt{)}'' / ``\texttt{)} sobrante''.
\item \textbf{Acciones múltiples con parámetros} (propia del dominio): $\textit{acciones}$ con \texttt{COMA} (prods.~19--21) y
\textit{parametros} (prods.~23--24); p.\,ej. \texttt{ajustar termostato 22 TRUE, activar alarma}.
\end{enumerate}
"""

S5 = r"""
\section{FIRST y FOLLOW}

\paragraph{Definiciones.} $\mathrm{FIRST}(\alpha)$ es el conjunto de terminales que pueden iniciar una cadena derivada de $\alpha$
(incluye $\varepsilon$ si $\alpha\Rightarrow^{*}\varepsilon$). $\mathrm{FOLLOW}(A)$ es el conjunto de terminales que pueden aparecer
inmediatamente a la derecha de $A$ en alguna forma sentencial (incluye \texttt{\$} si $A$ puede ir al final).

\paragraph{Reglas usadas.}
\begin{enumerate}[nosep]
\item Si $X$ es terminal, $\mathrm{FIRST}(X)=\{X\}$. Si $X\to\varepsilon$, $\varepsilon\in\mathrm{FIRST}(X)$.
\item Si $X\to Y_1Y_2\cdots Y_k$: se agrega $\mathrm{FIRST}(Y_1)\setminus\{\varepsilon\}$; si $Y_1$ es anulable, también $\mathrm{FIRST}(Y_2)\setminus\{\varepsilon\}$, y así sucesivamente; $\varepsilon\in\mathrm{FIRST}(X)$ si todos los $Y_i$ son anulables.
\item \texttt{\$}$\in\mathrm{FOLLOW}(S)$.
\item Si $A\to\alpha B\beta$: $\mathrm{FIRST}(\beta)\setminus\{\varepsilon\}\subseteq\mathrm{FOLLOW}(B)$.
\item Si $A\to\alpha B$ o $A\to\alpha B\beta$ con $\varepsilon\in\mathrm{FIRST}(\beta)$: $\mathrm{FOLLOW}(A)\subseteq\mathrm{FOLLOW}(B)$.
\end{enumerate}
Los conjuntos se calculan iterando hasta alcanzar el punto fijo (\texttt{calcular\_first} y \texttt{calcular\_follow} en
\texttt{gramatica.py}); los resultados coinciden con el cálculo manual justificado en las tablas y están verificados por
pruebas unitarias (\texttt{test\_first}, \texttt{test\_follow}).

\subsection{Conjuntos FIRST}
""" + tabla_conjuntos("FIRST", g.FIRST, JUST_FIRST) + r"""

Los no terminales anulables son \textit{programa'}, \textit{condicion'}, \textit{termino'}, \textit{acciones'} y \textit{parametros}.

\subsection{Conjuntos FOLLOW}
""" + tabla_conjuntos("FOLLOW", g.FOLLOW, JUST_FOLLOW) + "\n"

S6 = r"""
\section{Tabla LL(1)}

\paragraph{Construcción.} Para cada producción $A\to\alpha$ (numerada $n$): (a) para cada terminal $a\in\mathrm{FIRST}(\alpha)\setminus\{\varepsilon\}$,
se escribe $n$ en $M[A,a]$; (b) si $\varepsilon\in\mathrm{FIRST}(\alpha)$, se escribe $n$ en $M[A,b]$ para cada
$b\in\mathrm{FOLLOW}(A)$ (incluido \texttt{\$}). Una celda vacía significa error sintáctico.

\begin{landscape}
\begin{table}[H]
\centering
\caption{Tabla predictiva LL(1) de DomoDSL (cada número es la producción de la sección 3; celda vacía = error).}
\normalsize\setlength{\tabcolsep}{2pt}\renewcommand{\arraystretch}{1.25}
""" + tabla_ll1() + r"""
\end{table}
\end{landscape}

\subsection{¿Es la gramática LL(1)?}
\textbf{Sí.} Ninguna celda contiene más de una producción (el programa lo verifica: \texttt{CONFLICTOS = []}).
Equivalentemente, para cada no terminal con varias alternativas los \emph{conjuntos de selección}
$\mathrm{SEL}(A\to\alpha)=\mathrm{FIRST}(\alpha)\setminus\{\varepsilon\}\ \cup\ (\mathrm{FOLLOW}(A)\text{ si }\varepsilon\in\mathrm{FIRST}(\alpha))$
son disjuntos de a pares:

""" + tabla_select() + r"""

\paragraph{Puntos delicados y por qué no hay conflicto.}
\begin{itemize}[nosep]
\item \textit{parametros}: las producciones $\textit{valor}\ \textit{parametros}$ (selección $\{\texttt{NUM},\texttt{TRUE},\texttt{FALSE},\texttt{ID}\}$) y $\varepsilon$ (selección
$\mathrm{FOLLOW}=\{\texttt{PUNTO\_COMA},\texttt{COMA}\}$) no se solapan, precisamente porque la lista de parámetros siempre termina en
\texttt{;} o \texttt{,}.
\item \textit{termino'} y \textit{condicion'}: la alternativa vacía se elige con $\mathrm{FOLLOW}$ (\texttt{OR}, \texttt{THEN}, \texttt{)}), que no
contiene \texttt{AND}; por eso AND se asocia siempre antes que OR (precedencia).
\item \textit{programa'}: \texttt{WHEN} inicia otra regla y \texttt{\$} termina el programa.
\end{itemize}
\paragraph{Conclusión.} No fue necesario modificar la gramática después de calcular la tabla: las transformaciones de la
sección~4 ya dejaron una gramática LL(1) utilizable por ambos analizadores.
"""

S7 = r"""
\section{Diseño e implementación del parser}

\subsection{Arquitectura}
\begin{center}\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{4.4cm} >{\raggedright\arraybackslash}p{10.2cm}@{}}
\toprule
\textbf{Módulo} & \textbf{Responsabilidad} \\
\midrule
\texttt{lexer.py} & Texto $\to$ lista de \texttt{Token} (tipo, lexema, posición, línea, columna) terminada en \texttt{\$}. Error léxico para símbolos desconocidos. \\
\texttt{gramatica.py} & Lista \texttt{PRODUCCIONES}; \texttt{calcular\_first}, \texttt{calcular\_follow}, \texttt{construir\_tabla}; detección de conflictos. \\
\texttt{parser\_rd.py} & Parser predictivo por \textbf{descenso recursivo}; construye el \textbf{AST}. \\
\texttt{parser\_ll1.py} & Parser \textbf{dirigido por la tabla LL(1)} con pila; construye el árbol de derivación y una traza. \\
\texttt{arbol.py} & Clases del AST, árbol genérico, texto jerárquico y exportación a Graphviz. \\
\texttt{errores.py} & \texttt{ErrorLexico} y \texttt{ErrorSintactico} (mensaje, posición, línea, columna, puntero \texttt{\^{}}). \\
\texttt{main.py} & Interfaz de línea de comandos (archivo, texto, modo interactivo, opciones de visualización). \\
\texttt{casos\_prueba.py}, \texttt{ejecutar\_pruebas.py}, \texttt{test\_parser.py} & Casos, ejecutor con ambos parsers y pruebas unitarias. \\
\bottomrule
\end{tabular}
\end{center}
Ningún módulo usa bibliotecas de generación de parsers: solo la biblioteca estándar de Python
(\texttt{re}, \texttt{dataclasses}, \texttt{argparse}, \dots).

\subsection{Analizador léxico}
Parte de la función \texttt{analizador\_lexico} entregada por el docente (expresiones regulares nombradas combinadas en un patrón único).
Se ampliaron: el token \texttt{COMA}; números decimales; el \textbf{registro de posición} (offset, línea y columna) de cada token,
necesario para ubicar los errores; el token de fin \texttt{\$}; y mensajes léxicos con sugerencia (``¿quiso escribir \texttt{==}?'').

\subsection{Parser por descenso recursivo}
Hay \textbf{un método por cada no terminal}, y cada método implementa sus producciones; los comentarios del código indican el
número de producción. Los no terminales auxiliares (\textit{programa'}, \textit{condicion'}, \textit{termino'}, \textit{acciones'},
\textit{parametros}) se implementan como ciclos \texttt{while}, que equivalen a la recursión por la derecha de la gramática
pero (i)~no desbordan la pila de Python con programas largos y (ii)~permiten construir el AST con asociatividad izquierda.
Cuando la alternativa elegida es $\varepsilon$, el parser verifica que el lookahead pertenezca a FOLLOW del no terminal, para
informar el error en el punto exacto en que aparece.

\begin{center}\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{6cm} >{\raggedright\arraybackslash}p{9.3cm}@{}}
\toprule
\textbf{Producciones} & \textbf{Método (\texttt{ParserDescendente})} \\
\midrule
1--3 \;(\textit{programa}, \textit{programa'}) & \texttt{programa()} \\
4 \;(\textit{regla}) & \texttt{regla()} \\
5--7 \;(\textit{condicion}, \textit{condicion'}) & \texttt{condicion()} --- ciclo \texttt{while OR} \\
8--10 \;(\textit{termino}, \textit{termino'}) & \texttt{termino()} --- ciclo \texttt{while AND} + verificación FOLLOW \\
11--13 \;(\textit{factor}) & \texttt{factor()} \\
14 \;(\textit{comparacion}) & \texttt{comparacion()} \\
15--18 \;(\textit{valor}) & \texttt{valor()} \\
19--21 \;(\textit{acciones}, \textit{acciones'}) & \texttt{acciones()} --- ciclo \texttt{while COMA} \\
22--24 \;(\textit{accion}, \textit{parametros}) & \texttt{accion()} --- ciclo \texttt{while} lookahead $\in$ FIRST(valor) \\
\bottomrule
\end{tabular}
\end{center}

""" + extracto("parser_rd.py", r"def condicion\(", r"def comparacion\(",
               "Extracto de parser\\_rd.py: condicion, termino y factor (niveles de precedencia).") + r"""

\subsection{Parser dirigido por tabla LL(1)}
El segundo analizador usa la \emph{misma} lista de producciones: la tabla se genera automáticamente desde \texttt{gramatica.py} y se
interpreta con una pila (inicializada con \texttt{\$ programa}). Si el tope es un terminal, debe coincidir con el token actual; si es un
no terminal, se consulta $M[X,a]$, se reemplaza $X$ por el lado derecho de la producción (en orden inverso) y se agregan los
nodos hijos al árbol de derivación. Una celda vacía produce un error que lista los terminales esperados (la fila de la tabla).
La opción \texttt{--traza} imprime cada paso (pila, entrada restante, acción); ver la captura del Anexo~B.

""" + extracto("parser_ll1.py", r"while pila:", r"return raiz",
               "Extracto de parser\\_ll1.py: bucle principal del analizador LL(1).") + r"""

\subsection{Coherencia entre gramática, informe y código}
La lista \texttt{PRODUCCIONES} es la \emph{única} fuente de verdad: de ella salen FIRST, FOLLOW, la tabla, el parser LL(1) y las tablas de este
informe (generadas por \texttt{informe/generar\_informe.py}). El parser por descenso recursivo se escribió a mano siguiendo cada
producción, y la suite de pruebas comprueba que ambos analizadores aceptan y rechazan exactamente las mismas entradas
(""" + f"{len(PRUEBAS)}" + r""" casos).
"""

S8 = r"""
\section{Árbol sintáctico / AST}

El sistema construye dos representaciones:
\begin{itemize}[nosep]
\item \textbf{Árbol de derivación} (concreto), generado por el parser LL(1): contiene todos los no terminales, incluidos los auxiliares y las hojas $\varepsilon$.
\item \textbf{AST} (abstracto), generado por el parser de descenso recursivo: elimina los no terminales auxiliares, los paréntesis y las hojas $\varepsilon$; los
operadores son nodos internos y la asociatividad izquierda queda explícita (\texttt{Or(Or(a,b),c)}).
\end{itemize}
Ambos pueden mostrarse como texto jerárquico o exportarse a Graphviz (\texttt{--dot}).

\subsection{AST de la regla del enunciado}
Entrada: \texttt{""" + esc(EJ_ENUNCIADO) + r"""}
{\small
\begin{verbatim}
""" + a_texto(parsear(EJ_ENUNCIADO).a_nodo()) + r"""
\end{verbatim}}
\begin{figure}[H]
\centering
\includegraphics[width=0.55\textwidth]{../docs/img/ast_enunciado.png}
\caption{AST generado (Graphviz) para la regla del enunciado. Óvalos: nodos internos; cajas: hojas.}
\end{figure}

\subsection{AST con la extensión (NOT, paréntesis, acciones múltiples con parámetros)}
Entrada: \texttt{""" + esc(EJ_EXT) + r"""}

Se observa que el AST refleja la precedencia (\texttt{AND} es la raíz de la condición; \texttt{OR} queda dentro del segundo operando por los paréntesis)
y que los paréntesis no aparecen como nodos: su efecto está en la forma del árbol.
\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{../docs/img/ast_extension.png}
\caption{AST de una regla con \texttt{NOT}, paréntesis, dos acciones y un parámetro.}
\end{figure}

\subsection{Árbol de derivación (parser LL(1))}
Para \texttt{""" + esc(EJ_SIMPLE) + r"""}; las hojas $\varepsilon$ corresponden a las producciones vacías 3, 7, 10, 21 y 24.
\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{../docs/img/derivacion_simple.png}
\caption{Árbol de derivación obtenido con la tabla LL(1).}
\end{figure}
"""

S9 = r"""
\section{Manejo de errores}

\paragraph{Estrategia.} El analizador se detiene en el \textbf{primer error} y lo informa con tres datos de ubicación
(línea, columna y posición/offset), el mensaje, la línea de código afectada y un puntero \texttt{\^{}} bajo el token problemático.
Hay dos clases de error: \texttt{ErrorLexico} (carácter fuera del alfabeto) y \texttt{ErrorSintactico}.
Los mensajes siguen el formato \emph{se esperaba} $X$ \emph{[contexto]}, \emph{pero se encontró} $Y$, y dependen del contexto sintáctico:
\begin{itemize}[nosep]
\item Después de la condición se pide \texttt{THEN} (o un conector AND/OR) y, dentro de un paréntesis, se pide \texttt{)} indicando la columna donde se abrió.
\item Un \texttt{)} sin \texttt{(} se informa como ``paréntesis de cierre sin su \texttt{(} correspondiente''.
\item Cada punto de la gramática tiene su mensaje: valor tras el operador, operador tras el identificador, dispositivo tras la acción, \texttt{;} al final, etc.
\item La entrada vacía tiene un mensaje propio.
\end{itemize}
La notación $[l{:}c]$ indica línea y columna. En el programa, el mensaje completo incluye también la posición (offset).

\subsection{Mensajes del analizador de descenso recursivo}
""" + tabla_errores() + r"""

\subsection{Mensajes del analizador dirigido por tabla}
El parser LL(1) usa un mensaje más genérico, construido a partir de la fila de la tabla (los terminales para los que existe producción):

""" + tabla_errores_ll1() + r"""

Ambos analizadores coinciden siempre en \emph{aceptar o rechazar}; el de descenso recursivo da mensajes más específicos porque conoce el contexto
(el motivo por el que se llegó a cada método). Las capturas de los Anexos~B muestran el formato real, con puntero.

\paragraph{Limitación.} No hay recuperación de errores (modo pánico): tras el primer error el análisis termina. Sería una extensión natural
sincronizar en \texttt{;} (que pertenece a FOLLOW de \textit{acciones}) para informar varios errores por ejecución.
"""

S10 = r"""
\section{Casos de prueba}

Se documentan \textbf{""" + f"{len(PRUEBAS)}" + r""" casos}: """ + f"{n_val} válidas, {n_inv} inválidas y {n_lim} casos límite" + r""" (el enunciado exige 10, 10 y 5; la rúbrica premia
25 o más pruebas variadas). Cada caso se ejecutó con \textbf{ambos analizadores}; el resultado de las tablas es el obtenido por el programa
(\texttt{python ejecutar\_pruebas.py}). Resultado global: \textbf{""" + f"{n_ok}/{len(PRUEBAS)}" + r""" casos correctos}.
Además hay 18 pruebas unitarias (\texttt{python -m unittest}) que verifican el léxico, FIRST, FOLLOW, la ausencia de conflictos, la precedencia
y asociatividad del AST y la posición de los errores. Los casos de entradas muy largas (L05--L07) se muestran abreviados; su texto completo se genera
en \texttt{casos\_prueba.py}.

\begin{landscape}
\subsection{Entradas sintácticamente válidas}
""" + tabla_pruebas("válida") + r"""
\subsection{Entradas sintácticamente inválidas}
""" + tabla_pruebas("inválida") + r"""
\subsection{Casos límite}
""" + tabla_pruebas("límite") + r"""
\end{landscape}

\paragraph{Análisis de los casos límite.} Cubren: entrada vacía y solo espacios (L01--L02); regla truncada (L03); regla mínima sin espacios (L04);
anidamiento profundo de 20 paréntesis (L05); 200 conectores (L06) y 100 reglas (L07), que prueban que los ciclos no desbordan la pila;
mayúsculas/minúsculas (L08); identificadores con \texttt{\_} y dígitos y decimales (L09); palabra reservada como identificador (L10);
número pegado a letras (L11); error ubicado en la línea 3 de una entrada multilínea (L12); decimal incompleto (L13) y paréntesis redundantes (L14).
"""

S11 = r"""
\section{Conclusiones}

\begin{itemize}[nosep]
\item Se diseñó un DSL completo para automatización de una casa inteligente y se formalizó con una GLC de 24 producciones,
obtenida transformando una primera versión natural ($G_0$) que era recursiva por la izquierda, tenía prefijos comunes y era ambigua.
\item Las transformaciones (eliminación de recursión izquierda, factorización y estratificación por precedencia) llevaron a una gramática
\textbf{LL(1) sin conflictos}, comprobada con FIRST, FOLLOW, conjuntos de selección y la tabla.
\item Se implementaron \textbf{dos analizadores predictivos escritos a mano} (descenso recursivo y dirigido por tabla) que coinciden en los """ + f"{len(PRUEBAS)}" + r""" casos;
el primero construye un AST legible y el segundo el árbol de derivación y una traza.
\item El manejo de errores entrega mensajes útiles y localizados (línea, columna, posición, puntero), sensibles al contexto.
\item La extensión (\texttt{NOT}, paréntesis, acciones múltiples con parámetros) no es decorativa: modifica la gramática, FIRST/FOLLOW, la tabla, ambos
parsers y las pruebas.
\end{itemize}

\paragraph{Limitaciones y trabajo futuro.} Un solo error por ejecución (sin recuperación en modo pánico); no se analiza la semántica
(p.\,ej. que \texttt{temperatura} sea una variable existente o que \texttt{encender} sea aplicable a \texttt{ventilador}); y las palabras reservadas
son insensibles a mayúsculas, decisión heredada de la función base. Extensiones posibles: bloques \texttt{IF--ELSE}, comentarios, unidades de medida y
un verificador semántico.

\paragraph{Correspondencia con la rúbrica.}
\begin{center}\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{5.3cm} >{\raggedright\arraybackslash}p{9.3cm}@{}}
\toprule
\textbf{Criterio (puntos)} & \textbf{Dónde se cubre} \\
\midrule
1. Lenguaje y dominio (10) & Sección 2: tokens, requisitos, 7 ejemplos válidos y 6 inválidos \\
2. GLC (15) & Sección 3: 24 producciones, terminales, no terminales y símbolo inicial \\
3. Análisis, FIRST y FOLLOW (20) & Secciones 4 y 5: recursión, factorización, ambigüedad, FIRST/FOLLOW justificados \\
4. Tabla LL(1) (10) & Sección 6: tabla, conjuntos de selección y conclusión (sin conflictos) \\
5. Parser (20) & Sección 7 y Anexo C; dos analizadores sin generadores automáticos \\
6. AST y errores (10) & Secciones 8 y 9 \\
7. Pruebas y extensión (10) & Secciones 4.6 y 10: """ + f"{len(PRUEBAS)}" + r""" casos + 18 pruebas unitarias \\
8. Informe y README (5) & Este informe, \texttt{README.md}, repositorio (Anexo A) y capturas (Anexo B) \\
\bottomrule
\end{tabular}
\end{center}
"""

S12 = r"""
\section{Anexos}
\appendix
\renewcommand{\thesubsection}{\Alph{subsection}}

\subsection*{Anexo A. Repositorio}
El código fuente completo, el \texttt{README.md} (instrucciones de ejecución, dependencias, formato de entrada y ejemplos), los casos de prueba, los
ejemplos y las imágenes están en el repositorio:\\[2pt]
\centerline{\texttt{https://github.com/[usuario]/[repositorio]}}\\[2pt]
Para reproducir: \texttt{python main.py "WHEN temperatura > 28 THEN encender ventilador;"}, \texttt{python ejecutar\_pruebas.py} y \texttt{python -m unittest -v}.

\subsection*{Anexo B. Demostración funcional (capturas de pantalla)}
Salidas reales del programa (captura de la terminal).

\begin{figure}[H]\centering
\includegraphics[width=0.78\textwidth]{../docs/img/cap_valida.png}
\caption{Entrada válida: se informa el resultado y se imprime el AST.}
\end{figure}
\begin{figure}[H]\centering
\includegraphics[width=0.95\textwidth]{../docs/img/cap_archivo.png}
\caption{Análisis de un archivo con cuatro reglas (\texttt{ejemplos/casa\_inteligente.dsl}).}
\end{figure}
\begin{figure}[H]\centering
\includegraphics[width=0.95\textwidth]{../docs/img/cap_error_then.png}
\caption{Error sintáctico: falta \texttt{THEN}.}
\end{figure}
\begin{figure}[H]\centering
\includegraphics[width=0.95\textwidth]{../docs/img/cap_error_parentesis.png}
\caption{Error sintáctico: paréntesis sin cerrar.}
\end{figure}
\begin{figure}[H]\centering
\includegraphics[width=0.95\textwidth]{../docs/img/cap_error_lexico.png}
\caption{Error léxico: \texttt{=} en lugar de \texttt{==}.}
\end{figure}
\begin{figure}[H]\centering
\includegraphics[width=\textwidth]{../docs/img/cap_traza_ll1.png}
\caption{Traza del analizador LL(1) (\texttt{--traza}): pila, entrada restante y producción aplicada.}
\end{figure}
\begin{figure}[H]\centering
\includegraphics[width=0.85\textwidth]{../docs/img/cap_first_follow.png}
\caption{FIRST y FOLLOW calculados por el programa (\texttt{--first-follow}).}
\end{figure}
\begin{figure}[H]\centering
\includegraphics[width=0.95\textwidth]{../docs/img/cap_pruebas.png}
\caption{Resultado de \texttt{ejecutar\_pruebas.py}.}
\end{figure}
\begin{figure}[H]\centering
\includegraphics[width=0.95\textwidth]{../docs/img/cap_unittest.png}
\caption{Resultado de las pruebas unitarias.}
\end{figure}

\clearpage
\subsection*{Anexo C. Código fuente de los módulos principales}
\lstinputlisting[caption={lexer.py --- analizador léxico}]{../lexer.py}
\lstinputlisting[caption={gramatica.py --- GLC, FIRST, FOLLOW y tabla LL(1)}]{../gramatica.py}
\lstinputlisting[caption={parser\_rd.py --- parser por descenso recursivo}]{../parser_rd.py}
\lstinputlisting[caption={parser\_ll1.py --- parser dirigido por tabla LL(1)}]{../parser_ll1.py}
"""

def escribir(nombre, texto, cabecera):
    with open(nombre, "w", encoding="utf-8") as f:
        f.write(cabecera + "\n" + texto.lstrip("\n") + "\n")


if __name__ == "__main__":
    # Un archivo por autor (ver hoja "Propiedad de archivos" de la planilla de reparto):
    escribir("sec_02_lenguaje.tex", S2,
             "% Sección 2 (tarea C1) - autor: Persona C. Editar solo este archivo.")
    escribir("sec_03_06.tex", S3 + S4 + S5 + S6,
             "% Secciones 3 a 6: GLC, análisis, FIRST/FOLLOW, tabla LL(1) (tarea R1) - autor: Persona B.")
    escribir("sec_07_09.tex", S7 + S8 + S9,
             "% Secciones 7 a 9: parser, AST, errores (tarea R2) - autor: Persona A.")
    escribir("sec_01_10_12.tex",
             "\\ifnum\\parte=1\n" + S1 + "\n\\fi\n\\ifnum\\parte=2\n" + S10 + S11 + S12 + "\n\\fi",
             "% Secciones 1, 10, 11, 12 y anexos (tarea R3) - autor: Persona C.\n"
             "% \\parte=1 imprime la introduccion; \\parte=2 imprime pruebas, conclusiones y anexos.")
    principal = (PREAMBULO + PORTADA +
                 "\\newcommand{\\parte}{1}\n"
                 "\\input{sec_01_10_12}   % seccion 1 (parte 1)\n"
                 "\\input{sec_02_lenguaje}\n"
                 "\\input{sec_03_06}\n"
                 "\\input{sec_07_09}\n"
                 "\\renewcommand{\\parte}{2}\n"
                 "\\input{sec_01_10_12}   % secciones 10, 11 y 12 (parte 2)\n"
                 "\\end{document}\n")
    with open("Informe_DomoDSL.tex", "w", encoding="utf-8") as f:
        f.write(principal)
    print("Informe_DomoDSL.tex y secciones generados")
