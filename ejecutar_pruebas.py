#!/usr/bin/env python3
"""Ejecuta todos los casos de casos_prueba.py con AMBOS analizadores y muestra una tabla."""
import json
import sys

from casos_prueba import CASOS
from errores import ErrorDSL
from lexer import analizador_lexico
from parser_ll1 import parsear_ll1
from parser_rd import ParserDescendente


def ejecutar(entrada):
    """Devuelve (acepta_rd, mensaje_rd, acepta_ll1, mensaje_ll1)."""
    resultados = []
    for nombre in ("rd", "ll1"):
        try:
            tokens = analizador_lexico(entrada)
            if nombre == "rd":
                ParserDescendente(tokens).programa()
            else:
                parsear_ll1(tokens)
            resultados.append((True, ""))
        except ErrorDSL as e:
            resultados.append((False, str(e)))
    return resultados[0] + resultados[1]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    filas, fallos = [], 0
    for cid, cat, entrada, esperado, fragmento, obs in CASOS:
        ok_rd, msg_rd, ok_ll1, msg_ll1 = ejecutar(entrada)
        obtenido = "ACEPTA" if ok_rd else "RECHAZA"
        correcto = (obtenido == esperado and ok_rd == ok_ll1
                    and (esperado == "ACEPTA" or fragmento in msg_rd))
        fallos += not correcto
        filas.append(dict(id=cid, categoria=cat, entrada=entrada, esperado=esperado,
                          obtenido=obtenido, mensaje=msg_rd, mensaje_ll1=msg_ll1,
                          observacion=obs, coincide_ll1=(ok_rd == ok_ll1), ok=correcto))
        marca = "OK " if correcto else "FALLA"
        corto = entrada.replace("\n", "\\n")
        corto = corto if len(corto) <= 60 else corto[:57] + "..."
        print(f"[{marca}] {cid} {cat:<9} esperado={esperado:<8} obtenido={obtenido:<8} {corto}")
    total = len(CASOS)
    print(f"\n{total - fallos}/{total} casos correctos "
          f"(válidas: {sum(c[1]=='válida' for c in CASOS)}, "
          f"inválidas: {sum(c[1]=='inválida' for c in CASOS)}, "
          f"límite: {sum(c[1]=='límite' for c in CASOS)}).")
    with open("docs/resultados_pruebas.json", "w", encoding="utf-8") as f:
        json.dump(filas, f, ensure_ascii=False, indent=1)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
