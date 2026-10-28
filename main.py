#!/usr/bin/env python3
"""
DomoDSL - analizador sintáctico (INFO1148, Teoría de la Computación).

Uso rápido:
  python main.py "WHEN temperatura > 28 THEN encender ventilador;"
  python main.py -f ejemplos/casa_inteligente.dsl --arbol derivacion
  python main.py -i                      # modo interactivo
  python main.py --gramatica --first-follow --tabla
  python main.py "WHEN a > 1 THEN x y;" --parser ll1 --traza
"""
import argparse
import sys

import gramatica
from arbol import a_dot, a_texto
from errores import ErrorDSL
from lexer import analizador_lexico, tokens_a_tuplas
from parser_ll1 import parsear_ll1
from parser_rd import ParserDescendente


def analizar(entrada, parser="rd", arbol="ast", mostrar_tokens=False, traza=False,
             dot=None, salida=print):
    """Analiza `entrada`. Devuelve True si es válida, False si hay error."""
    try:
        tokens = analizador_lexico(entrada)
        if mostrar_tokens:
            salida("Tokens:")
            for t in tokens_a_tuplas(tokens):
                salida(f"  {t}")
        pasos = [] if traza else None
        ast = derivacion = None
        if parser == "ll1" or arbol == "derivacion":
            derivacion = parsear_ll1(tokens, pasos)
        if parser == "rd" or arbol == "ast":
            ast = ParserDescendente(tokens).programa()
    except ErrorDSL as e:
        salida(e.con_contexto(entrada))
        return False

    salida("✔ Entrada sintácticamente VÁLIDA "
           f"(analizador: {'descenso recursivo' if parser == 'rd' else 'tabla LL(1)'})")
    if traza and pasos:
        salida("\nTraza del analizador LL(1):")
        salida(f"{'PILA (tope a la izquierda)':<60} | {'ENTRADA':<45} | ACCIÓN")
        for pila, resto, accion in pasos:
            salida(f"{pila:<60} | {resto:<45} | {accion}")
    nodo = None
    if arbol == "ast" and ast is not None:
        salida("\nAST:")
        nodo = ast.a_nodo()
    elif arbol == "derivacion" and derivacion is not None:
        salida("\nÁrbol sintáctico (derivación):")
        nodo = derivacion
    if nodo is not None:
        salida(a_texto(nodo))
        if dot:
            with open(dot, "w", encoding="utf-8") as f:
                f.write(a_dot(nodo))
            salida(f"\n(DOT escrito en {dot}; genere imagen con: dot -Tpng {dot} -o arbol.png)")
    return True


def modo_interactivo(args):
    print("DomoDSL interactivo. Escriba una regla (termine con ENTER). 'salir' para terminar.")
    while True:
        try:
            linea = input("domo> ").strip()
        except EOFError:
            break
        if linea.lower() in ("salir", "exit", "quit"):
            break
        if linea:
            analizar(linea, args.parser, args.arbol, args.tokens, args.traza)
            print()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Analizador sintáctico de DomoDSL")
    p.add_argument("texto", nargs="?", help="programa DomoDSL a analizar (entre comillas)")
    p.add_argument("-f", "--archivo", help="leer el programa desde un archivo")
    p.add_argument("-i", "--interactivo", action="store_true", help="modo interactivo")
    p.add_argument("--parser", choices=["rd", "ll1"], default="rd",
                   help="rd = descenso recursivo (por defecto), ll1 = dirigido por tabla")
    p.add_argument("--arbol", choices=["ast", "derivacion", "no"], default="ast")
    p.add_argument("--dot", metavar="ARCHIVO.dot", help="exportar el árbol a Graphviz")
    p.add_argument("--tokens", action="store_true", help="mostrar los tokens")
    p.add_argument("--traza", action="store_true", help="traza del analizador LL(1)")
    p.add_argument("--gramatica", action="store_true", help="mostrar la GLC")
    p.add_argument("--first-follow", action="store_true", help="mostrar FIRST y FOLLOW")
    p.add_argument("--tabla", action="store_true", help="mostrar la tabla LL(1)")
    args = p.parse_args()
    if args.traza:
        args.parser = "ll1"

    informacion = False
    if args.gramatica:
        print(gramatica.formatear_gramatica(), end="\n\n"); informacion = True
    if args.first_follow:
        print(gramatica.formatear_first_follow(), end="\n\n"); informacion = True
    if args.tabla:
        print(gramatica.formatear_tabla(), end="\n\n"); informacion = True

    if args.interactivo:
        modo_interactivo(args)
        return 0
    if args.archivo:
        with open(args.archivo, encoding="utf-8") as f:
            entrada = f.read()
    elif args.texto is not None:
        entrada = args.texto
    elif informacion:
        return 0
    else:
        p.print_help()
        return 2
    return 0 if analizar(entrada, args.parser, args.arbol, args.tokens, args.traza,
                         args.dot) else 1


if __name__ == "__main__":
    sys.exit(main())
