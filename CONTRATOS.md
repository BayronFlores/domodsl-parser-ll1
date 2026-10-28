# CONTRATOS DE INTERFAZ (tareas T02 y T05)

Aprobados por los tres integrantes al fin del Día 2. Un contrato es lo mínimo que los demás necesitan saber de un
módulo; si se respeta, nadie espera a nadie (se trabaja con *stubs* o datos escritos a mano).

| ID | Contrato | Definición exacta | Dueño | Lo usan |
|---|---|---|---|---|
| K1 | **Token** | `Token(tipo, lexema, pos, linea, columna)`. `analizador_lexico(texto)` devuelve una lista de `Token` que termina con tipo `'$'`. Tipos: `WHEN THEN AND OR NOT TRUE FALSE ID NUM OP_REL PUNTO_COMA COMA PARENT_IZQ PARENT_DER`. | A | B, C |
| K2 | **Producciones numeradas** | `PRODUCCIONES = [(no_terminal, [símbolos]), ...]`; ε se escribe `'ε'`; fin de entrada `'$'`. Numeración 1..24 según `docs/gramatica_v1.md`. | B | A, C |
| K3 | **API de los parsers** | Descenso recursivo: `ParserDescendente(tokens).programa()` → AST. Tabla: `parsear_ll1(tokens, traza=None)` → `Nodo`. Ambos lanzan `ErrorSintactico(mensaje, pos, linea, columna)` ante el primer error. | A (RD), B (LL1) | C, main.py |
| K4 | **Errores** | `ErrorDSL(mensaje, pos, linea, columna)` con subclases `ErrorLexico` y `ErrorSintactico`; `con_contexto(entrada)` imprime la línea y un puntero `^`. | A | B, C |
| K5 | **AST y Nodo genérico** | `Nodo(etiqueta, hijos, terminal)`. Cada clase del AST tiene `a_nodo()`. `a_texto(nodo)` y `a_dot(nodo)` (Graphviz). | A | B, C |
| K6 | **Formato de caso de prueba** | `(id, categoría, entrada, esperado 'ACEPTA'\|'RECHAZA', fragmento_del_mensaje_de_error, observación)`. | C | A, B |
| K7 | **Gramática congelada** | Desde el fin del Día 2 no se modifica. Un cambio exige una solicitud aprobada por los 3, registrada abajo con fecha y motivo. | Todos | Todos |
| K8 | **Convención de git** | Ramas `feature/A`, `feature/B`, `feature/C`. Cada persona edita solo sus archivos. Merge a `main` con pull request revisado por la persona indicada como revisor. | C | Todos |

## Propiedad de archivos (solo el dueño edita)
| Archivo | Dueño |
|---|---|
| `lexer.py`, `errores.py`, `arbol.py`, `parser_rd.py`, `main.py` | A |
| `gramatica.py`, `parser_ll1.py`, `docs/analisis_gramatica.md`, `docs/first_follow.md`, `docs/tabla_ll1.md` | B |
| `casos_prueba.py`, `ejecutar_pruebas.py`, `test_parser.py`, `ejemplos/`, `README.md` | C |
| `informe/sec_03_06.tex` | B |
| `informe/sec_07_09.tex` | A |
| `informe/sec_02_lenguaje.tex`, `informe/sec_01_10_12.tex`, portada y ensamblado (`informe/Informe_DomoDSL.tex`) | C |

> En este repositorio final los archivos del informe se generan con `informe/generar_informe.py` para que las tablas coincidan con el código.

## Registro de solicitudes de cambio a la gramática (K7)
| Fecha | Solicitud | Motivo | Aprobada por | Resultado |
|---|---|---|---|---|
| — | Ninguna: la gramática no se modificó después del congelamiento. | — | — | — |
