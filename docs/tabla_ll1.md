# Tabla LL(1) (tareas B3 y B4)

**Construcción.** Para cada producción A → α (número n): (a) para cada terminal a ∈ FIRST(α) − {ε}, se escribe n en M[A, a];
(b) si ε ∈ FIRST(α), se escribe n en M[A, b] para cada b ∈ FOLLOW(A) (incluido `$`). Celda vacía = error sintáctico.

## Tabla (cada número es una producción de `gramatica_v1.md`)
| | `WHEN` | `THEN` | `PUNTO_COMA` | `OR` | `AND` | `NOT` | `PARENT_IZQ` | `PARENT_DER` | `ID` | `OP_REL` | `NUM` | `TRUE` | `FALSE` | `COMA` | `$` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `programa` | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `programa_p` | 2 |  |  |  |  |  |  |  |  |  |  |  |  |  | 3 |
| `regla` | 4 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `condicion` |  |  |  |  |  | 5 | 5 |  | 5 |  |  |  |  |  |  |
| `condicion_p` |  | 7 |  | 6 |  |  |  | 7 |  |  |  |  |  |  |  |
| `termino` |  |  |  |  |  | 8 | 8 |  | 8 |  |  |  |  |  |  |
| `termino_p` |  | 10 |  | 10 | 9 |  |  | 10 |  |  |  |  |  |  |  |
| `factor` |  |  |  |  |  | 11 | 12 |  | 13 |  |  |  |  |  |  |
| `comparacion` |  |  |  |  |  |  |  |  | 14 |  |  |  |  |  |  |
| `valor` |  |  |  |  |  |  |  |  | 18 |  | 15 | 16 | 17 |  |  |
| `acciones` |  |  |  |  |  |  |  |  | 19 |  |  |  |  |  |  |
| `acciones_p` |  |  | 21 |  |  |  |  |  |  |  |  |  |  | 20 |  |
| `accion` |  |  |  |  |  |  |  |  | 22 |  |  |  |  |  |  |
| `parametros` |  |  | 24 |  |  |  |  |  | 23 |  | 23 | 23 | 23 | 24 |  |

## ¿Es LL(1)?
**Sí.** Conflictos detectados por `gramatica.py`: `[]`. Equivalentemente, los conjuntos de selección
SEL(A → α) = FIRST(α) − {ε} ∪ (FOLLOW(A) si ε ∈ FIRST(α)) son disjuntos de a pares:

| No terminal | Producción | Conjunto de selección | ¿Disjuntos? |
|---|---|---|---|
| `programa_p` | (2) `regla programa_p` | `{ WHEN }` | sí |
|  | (3) `ε` | `{ $ }` |  |
| `condicion_p` | (6) `OR termino condicion_p` | `{ OR }` | sí |
|  | (7) `ε` | `{ THEN, PARENT_DER }` |  |
| `termino_p` | (9) `AND factor termino_p` | `{ AND }` | sí |
|  | (10) `ε` | `{ THEN, OR, PARENT_DER }` |  |
| `factor` | (11) `NOT factor` | `{ NOT }` | sí |
|  | (12) `PARENT_IZQ condicion PARENT_DER` | `{ PARENT_IZQ }` |  |
|  | (13) `comparacion` | `{ ID }` |  |
| `valor` | (15) `NUM` | `{ NUM }` | sí |
|  | (16) `TRUE` | `{ TRUE }` |  |
|  | (17) `FALSE` | `{ FALSE }` |  |
|  | (18) `ID` | `{ ID }` |  |
| `acciones_p` | (20) `COMA accion acciones_p` | `{ COMA }` | sí |
|  | (21) `ε` | `{ PUNTO_COMA }` |  |
| `parametros` | (23) `valor parametros` | `{ ID, NUM, TRUE, FALSE }` | sí |
|  | (24) `ε` | `{ PUNTO_COMA, COMA }` |  |

## Puntos delicados
* `parametros`: `valor parametros` (selección {NUM, TRUE, FALSE, ID}) y `ε` (FOLLOW = {PUNTO_COMA, COMA}) no se solapan porque la
  lista de parámetros siempre termina en `;` o `,`.
* `termino_p` y `condicion_p`: la alternativa vacía se elige con FOLLOW (OR, THEN, PARENT_DER), que no contiene AND; por eso AND se
  asocia siempre antes que OR.
* `programa_p`: `WHEN` inicia otra regla y `$` termina el programa.

**Conclusión:** no fue necesario modificar la gramática después de calcular la tabla.
