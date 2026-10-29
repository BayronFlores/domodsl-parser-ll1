# FIRST y FOLLOW (tarea B2)

## Reglas usadas
1. Si X es terminal, FIRST(X) = {X}. Si X → ε, ε ∈ FIRST(X).
2. Si X → Y1 Y2 … Yk: se agrega FIRST(Y1) − {ε}; si Y1 es anulable, también FIRST(Y2) − {ε}, y así sucesivamente;
   ε ∈ FIRST(X) si todos los Yi son anulables.
3. `$` ∈ FOLLOW(símbolo inicial).
4. Si A → αBβ: FIRST(β) − {ε} ⊆ FOLLOW(B).
5. Si A → αB, o A → αBβ con ε ∈ FIRST(β): FOLLOW(A) ⊆ FOLLOW(B).

Los resultados coinciden con los que calcula `gramatica.py` (verificado por `test_parser.py`).

## FIRST
| No terminal | Conjunto | Justificación |
|---|---|---|
| `programa` | `{ WHEN }` | Prod. 1 empieza por `regla`, que no es anulable: FIRST(programa) = FIRST(regla). |
| `programa_p` | `{ WHEN, ε }` | Prod. 2: FIRST(regla) = {WHEN}; la prod. 3 aporta ε. |
| `regla` | `{ WHEN }` | Prod. 4 empieza con el terminal WHEN. |
| `condicion` | `{ NOT, PARENT_IZQ, ID }` | Prod. 5: `termino` no es anulable, luego FIRST(condicion) = FIRST(termino). |
| `condicion_p` | `{ OR, ε }` | Prod. 6 empieza con OR; prod. 7 aporta ε. |
| `termino` | `{ NOT, PARENT_IZQ, ID }` | Prod. 8: `factor` no es anulable, luego FIRST(termino) = FIRST(factor). |
| `termino_p` | `{ AND, ε }` | Prod. 9 empieza con AND; prod. 10 aporta ε. |
| `factor` | `{ NOT, PARENT_IZQ, ID }` | Prod. 11: NOT; prod. 12: PARENT_IZQ; prod. 13: FIRST(comparacion) = {ID}. |
| `comparacion` | `{ ID }` | Prod. 14 empieza con el terminal ID. |
| `valor` | `{ ID, NUM, TRUE, FALSE }` | Prods. 15–18: NUM, TRUE, FALSE e ID. |
| `acciones` | `{ ID }` | Prod. 19: FIRST(accion) = {ID}; `accion` no es anulable. |
| `acciones_p` | `{ COMA, ε }` | Prod. 20 empieza con COMA; prod. 21 aporta ε. |
| `accion` | `{ ID }` | Prod. 22 empieza con el terminal ID. |
| `parametros` | `{ ID, NUM, TRUE, FALSE, ε }` | Prod. 23: FIRST(valor); la prod. 24 aporta ε. |

No terminales anulables: `programa_p`, `condicion_p`, `termino_p`, `acciones_p`, `parametros`.

## FOLLOW
| No terminal | Conjunto | Justificación |
|---|---|---|
| `programa` | `{ $ }` | Símbolo inicial: se agrega `$`. |
| `programa_p` | `{ $ }` | Prod. 1: `programa_p` está al final, luego FOLLOW(programa) ⊆ FOLLOW(programa_p). |
| `regla` | `{ WHEN, $ }` | Prods. 1 y 2: sigue `programa_p`; FIRST(programa_p) − {ε} = {WHEN} y, como es anulable, se agrega FOLLOW(programa_p) = {$}. |
| `condicion` | `{ THEN, PARENT_DER }` | Prod. 4: sigue THEN. Prod. 12: sigue PARENT_DER. |
| `condicion_p` | `{ THEN, PARENT_DER }` | Prods. 5 y 6: va al final, luego hereda FOLLOW(condicion). |
| `termino` | `{ THEN, OR, PARENT_DER }` | Prods. 5 y 6: sigue `condicion_p`: OR, y por ser anulable se agrega FOLLOW(condicion). |
| `termino_p` | `{ THEN, OR, PARENT_DER }` | Prods. 8 y 9: va al final, luego hereda FOLLOW(termino). |
| `factor` | `{ THEN, OR, AND, PARENT_DER }` | Prods. 8 y 9: sigue `termino_p`: AND, y por ser anulable FOLLOW(termino). |
| `comparacion` | `{ THEN, OR, AND, PARENT_DER }` | Prod. 13: va al final, luego hereda FOLLOW(factor). |
| `valor` | `{ THEN, PUNTO_COMA, OR, AND, PARENT_DER, ID, NUM, TRUE, FALSE, COMA }` | Prod. 14: va al final, hereda FOLLOW(comparacion). Prod. 23: sigue `parametros`: FIRST(parametros) − {ε} y, al ser anulable, FOLLOW(parametros). |
| `acciones` | `{ PUNTO_COMA }` | Prod. 4: sigue PUNTO_COMA. |
| `acciones_p` | `{ PUNTO_COMA }` | Prods. 19 y 20: va al final, luego hereda FOLLOW(acciones). |
| `accion` | `{ PUNTO_COMA, COMA }` | Prods. 19 y 20: sigue `acciones_p`: COMA, y por ser anulable FOLLOW(acciones). |
| `parametros` | `{ PUNTO_COMA, COMA }` | Prod. 22: va al final, hereda FOLLOW(accion). Prod. 23: hereda FOLLOW(parametros). |
