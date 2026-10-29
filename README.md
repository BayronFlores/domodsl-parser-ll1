# DomoDSL — Analizador sintáctico para automatización de una casa inteligente

Proyecto de **Teoría de la Computación (INFO1148)** — _Diseño e implementación de un analizador sintáctico_.

DomoDSL es un pequeño lenguaje de dominio específico (DSL) para escribir **reglas de automatización IoT**
("cuando ocurra esta condición, ejecuta estas acciones"). Este repositorio contiene:

- un **analizador léxico** (ampliado a partir del entregado por el docente),
- la **gramática libre de contexto** del lenguaje, con cálculo de **FIRST**, **FOLLOW** y **tabla LL(1)**,
- **dos analizadores sintácticos predictivos escritos a mano** (sin generadores de parsers):
  descenso recursivo (construye el **AST**) y dirigido por la **tabla LL(1)** (construye el árbol de derivación),
- manejo de **errores léxicos y sintácticos** con línea, columna y posición,
- **46 casos de prueba** + 18 pruebas unitarias,
- el informe del proyecto (se entrega aparte en PDF; sus capturas están en `docs/img/`).

```
WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;
WHEN movimiento == TRUE THEN activar alarma, encender luz_pasillo 80;
WHEN NOT (puerta == TRUE) AND (hora >= 22 OR hora < 6) THEN bloquear puerta_principal;
```

## Requisitos

- **Python 3.9 o superior** (probado con 3.12).
- **No requiere bibliotecas externas.**
- _Opcional:_ [Graphviz](https://graphviz.org/download/) para convertir los archivos `.dot` exportados en imágenes.

## Estructura del repositorio

| Archivo                        | Contenido                                                                                    |
| ------------------------------ | -------------------------------------------------------------------------------------------- |
| `lexer.py`                     | Analizador léxico: tokens con posición, palabras reservadas, token de fin `$`.               |
| `gramatica.py`                 | La GLC (24 producciones), cálculo de FIRST/FOLLOW, tabla LL(1) y detección de conflictos.    |
| `parser_rd.py`                 | Parser por **descenso recursivo** → construye el **AST**. Un método por no terminal.         |
| `parser_ll1.py`                | Parser **dirigido por tabla LL(1)** con pila → construye el árbol de derivación y una traza. |
| `arbol.py`                     | Clases del AST, árbol genérico, impresión jerárquica y exportación a Graphviz (`.dot`).      |
| `errores.py`                   | Excepciones `ErrorLexico` y `ErrorSintactico` (línea, columna, posición, puntero `^`).       |
| `main.py`                      | Interfaz de línea de comandos.                                                               |
| `casos_prueba.py`              | Tabla de 46 casos (12 válidos, 20 inválidos, 14 límite).                                     |
| `ejecutar_pruebas.py`          | Ejecuta los casos con **ambos** parsers y muestra el resultado.                              |
| `test_parser.py`               | Pruebas unitarias (`unittest`): léxico, FIRST/FOLLOW, tabla, AST, errores.                   |
| `ejemplos/`                    | Programas `.dsl` de ejemplo (válidos e inválidos).                                           |
| `docs/gramatica_v1.md`         | Gramática congelada, numerada (T03).                                                         |
| `docs/analisis_gramatica.md`   | Recursión izquierda, factorización y ambigüedad (B1).                                        |
| `docs/first_follow.md`         | FIRST y FOLLOW justificados (B2).                                                            |
| `docs/tabla_ll1.md`            | Tabla LL(1) y conjuntos de selección (B3, B4).                                               |
| `docs/resultados_pruebas.json` | Resultados de `ejecutar_pruebas.py` (se regenera al ejecutarlo).                             |
| `docs/img/`                    | Árboles (`.dot` y `.png`) y capturas de la ejecución.                                        |

## Cómo ejecutar

```bash
# 1) Analizar una entrada escrita directamente
python main.py "WHEN temperatura > 28 THEN encender ventilador;"

# 2) Analizar un archivo
python main.py -f ejemplos/casa_inteligente.dsl

# 3) Modo interactivo (escriba reglas; 'salir' para terminar)
python main.py -i

# 4) Elegir el analizador y el tipo de árbol
python main.py "WHEN a > 1 THEN x y;" --parser ll1 --arbol derivacion
python main.py "WHEN a > 1 THEN x y;" --parser ll1 --traza          # traza paso a paso de la pila

# 5) Ver la teoría calculada por el programa
python main.py --gramatica --first-follow --tabla

# 6) Exportar el árbol a Graphviz y generar la imagen
python main.py -f ejemplos/casa_inteligente.dsl --dot arbol.dot
dot -Tpng arbol.dot -o arbol.png

# 7) Mostrar los tokens
python main.py "WHEN a > 1 THEN x y;" --tokens
```

Opciones de `main.py`: `--parser {rd,ll1}` · `--arbol {ast,derivacion,no}` · `--dot ARCHIVO` · `--tokens` ·
`--traza` · `--gramatica` · `--first-follow` · `--tabla` · `-f ARCHIVO` · `-i`.
El programa termina con código `0` si la entrada es válida y `1` si hay error.

## Ejecutar las pruebas

```bash
python ejecutar_pruebas.py     # tabla de los 46 casos, con ambos parsers (genera docs/resultados_pruebas.json)
python -m unittest -v          # 18 pruebas unitarias
```

## Formato de entrada

Un **programa** es una o más **reglas**. Cada regla termina en `;`. Los espacios, tabulaciones y saltos de línea
se ignoran, y las palabras reservadas no distinguen mayúsculas de minúsculas (`WHEN` = `when`).

```
regla      := WHEN condición THEN acción [, acción]* ;
condición  := comparaciones unidas con AND / OR, con NOT y paréntesis
comparación:= identificador  operador  valor         (operadores: > < >= <= == !=)
acción     := verbo dispositivo [parámetros]         (ej.: ajustar termostato 22 TRUE)
valor      := número (28, 26.5) | TRUE | FALSE | identificador
```

Precedencia (de mayor a menor): `NOT`, `AND`, `OR`; ambos conectores asocian a la izquierda. Los paréntesis agrupan.

### Tokens

| Token               | Ejemplos                                      |
| ------------------- | --------------------------------------------- |
| Palabras reservadas | `WHEN` `THEN` `AND` `OR` `NOT` `TRUE` `FALSE` |
| `ID`                | `temperatura`, `sensor_1`, `luz_pasillo`      |
| `NUM`               | `28`, `0.5`                                   |
| `OP_REL`            | `>` `<` `>=` `<=` `==` `!=`                   |
| Separadores         | `;` `,` `(` `)`                               |

## Gramática (resumen)

```
programa    → regla programa_p                 acciones    → accion acciones_p
programa_p  → regla programa_p | ε             acciones_p  → , accion acciones_p | ε
regla       → WHEN condicion THEN acciones ;   accion      → ID ID parametros
condicion   → termino condicion_p              parametros  → valor parametros | ε
condicion_p → OR termino condicion_p | ε       comparacion → ID OP_REL valor
termino     → factor termino_p                 valor       → NUM | TRUE | FALSE | ID
termino_p   → AND factor termino_p | ε
factor      → NOT factor | ( condicion ) | comparacion
```

La gramática es **LL(1)** (sin conflictos en la tabla). El detalle (análisis de recursión izquierda, factorización,
ambigüedad, FIRST, FOLLOW y tabla) está en el informe y se puede regenerar con
`python main.py --gramatica --first-follow --tabla`.

**Extensión creativa** (integrada en la gramática, FIRST/FOLLOW, tabla, parsers y pruebas): operador `NOT`,
**paréntesis** de agrupación, **múltiples acciones** separadas por coma y **acciones con parámetros**.

## Ejemplos de ejecución

Entrada válida:

```text
$ python main.py "WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;"
✔ Entrada sintácticamente VÁLIDA (analizador: descenso recursivo)

AST:
Programa
└── Regla (línea 1)
    ├── Condición
    │   └── AND
    │       ├── >
    │       │   ├── temperatura  [ID]
    │       │   └── 28  [NUM]
    │       └── <
    │           ├── humedad  [ID]
    │           └── 40  [NUM]
    └── Acciones
        └── Acción: encender
            └── objeto: ventilador
```

Errores (con línea, columna y puntero):

```text
$ python main.py "WHEN temperatura > 28 encender ventilador;"
Error sintáctico (línea 1, columna 23, posición 22): se esperaba la palabra reservada THEN (o un conector AND / OR) después de la condición, pero se encontró el identificador 'encender'.
    WHEN temperatura > 28 encender ventilador;
                          ^

$ python main.py "WHEN temperatura > THEN encender ventilador;"
Error sintáctico (línea 1, columna 20, posición 19): se esperaba un valor (número, TRUE, FALSE o identificador) después del operador >, pero se encontró la palabra reservada THEN.

$ python main.py "WHEN temperatura = 28 THEN x y;"
Error léxico (línea 1, columna 18, posición 17): símbolo no reconocido '='. ¿quiso escribir '==' para comparar?
```

## Decisiones de diseño

- **Sin generadores de parsers**: FIRST, FOLLOW, tabla y ambos analizadores están implementados desde cero
  (solo se usa la biblioteca estándar de Python).
- **Coherencia gramática ↔ código**: cada método de `parser_rd.py` indica en un comentario la producción que implementa
  y la tabla de `parser_ll1.py` se construye a partir de la **misma** lista `PRODUCCIONES` de `gramatica.py`.
  Las pruebas verifican que ambos analizadores aceptan/rechazan exactamente las mismas entradas.
- **Errores**: el analizador se detiene en el primer error y lo informa con posición; los mensajes dependen del contexto
  (por ejemplo, distinguen "falta `)`" de "`)` sobrante").
- **Limitación conocida**: no hay recuperación de errores (no se informan varios errores en una misma ejecución).
