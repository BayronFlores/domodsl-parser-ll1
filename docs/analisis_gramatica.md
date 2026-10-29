# Análisis de la gramática (tarea B1)

## 1. Versión inicial G0 (la forma "natural")
```
programa    → regla programa | regla
regla       → WHEN condicion THEN acciones PUNTO_COMA
condicion   → condicion OR condicion | condicion AND condicion
            | NOT condicion | PARENT_IZQ condicion PARENT_DER | comparacion
comparacion → ID OP_REL valor
valor       → NUM | TRUE | FALSE | ID
acciones    → acciones COMA accion | accion
accion      → ID ID parametros
parametros  → parametros valor | ε
```
G0 describe el lenguaje pero **no sirve para un parser predictivo**: tiene recursión por la izquierda,
prefijos comunes y es ambigua.

## 2. Recursión por la izquierda
Recursión izquierda **directa** en `condicion`, `acciones` y `parametros`. Se aplica
`A → Aα | β  ⇒  A → βA′, A′ → αA′ | ε`:

| Original (G0) | Transformado | Producciones finales |
|---|---|---|
| `acciones → acciones COMA accion \| accion` | `acciones → accion acciones_p`; `acciones_p → COMA accion acciones_p \| ε` | 19–21 |
| `parametros → parametros valor \| ε` | `parametros → valor parametros \| ε` (recursión por la derecha, equivalente) | 23–24 |
| `condicion → condicion OR condicion \| …` | `condicion → termino condicion_p`; `condicion_p → OR termino condicion_p \| ε` | 5–7 |
| (nivel de AND) | `termino → factor termino_p`; `termino_p → AND factor termino_p \| ε` | 8–10 |

**Verificación:** ninguna producción de la gramática final empieza con su propio lado izquierdo. Tampoco hay
recursión indirecta: las dependencias por el primer símbolo son `programa → regla → WHEN`,
`condicion → termino → factor → comparacion → ID` y `acciones → accion → ID` (sin ciclos). La recursión
`factor → NOT factor` empieza con un terminal y es inofensiva.

## 3. Factorización por la izquierda
En G0, `programa` tiene dos alternativas con el prefijo común `regla`. Se factoriza:
`programa → regla programa_p` con `programa_p → programa | ε`; como `programa` empieza con `regla`, se sustituye y queda
`programa_p → regla programa_p | ε` (producciones 1–3). En el resto de la gramática las alternativas de un mismo no
terminal comienzan con terminales distintos (por ejemplo `factor`: `NOT`, `PARENT_IZQ`, `ID`); se confirma con los
conjuntos de selección disjuntos (ver `tabla_ll1.md`).

## 4. Ambigüedad
G0 es **ambigua**: `a > 1 OR b > 2 AND c > 3` tiene dos árboles:
`(a > 1 OR b > 2) AND c > 3` frente a `a > 1 OR (b > 2 AND c > 3)`. Además `a OR b OR c` puede agruparse a la izquierda o a
la derecha.

**Solución:** niveles de precedencia (`condicion` = OR, `termino` = AND, `factor` = NOT / paréntesis / comparación).
AND liga más fuerte que OR y NOT más que AND. La asociatividad es **izquierda**: el AST se construye con un ciclo que agrupa
`((a OR b) OR c)`. Como la gramática final es LL(1), es **no ambigua** (toda gramática LL(1) lo es).

En `accion`, los parámetros podrían confundirse con el siguiente elemento, pero no hay ambigüedad porque la lista de
parámetros termina siempre en `;` o `,` (FOLLOW(parametros) = { PUNTO_COMA, COMA }).

## 5. Gramática final
 1. `programa → regla programa_p`
 2. `programa_p → regla programa_p`
 3. `programa_p → ε`
 4. `regla → WHEN condicion THEN acciones PUNTO_COMA`
 5. `condicion → termino condicion_p`
 6. `condicion_p → OR termino condicion_p`
 7. `condicion_p → ε`
 8. `termino → factor termino_p`
 9. `termino_p → AND factor termino_p`
10. `termino_p → ε`
11. `factor → NOT factor`
12. `factor → PARENT_IZQ condicion PARENT_DER`
13. `factor → comparacion`
14. `comparacion → ID OP_REL valor`
15. `valor → NUM`
16. `valor → TRUE`
17. `valor → FALSE`
18. `valor → ID`
19. `acciones → accion acciones_p`
20. `acciones_p → COMA accion acciones_p`
21. `acciones_p → ε`
22. `accion → ID ID parametros`
23. `parametros → valor parametros`
24. `parametros → ε`
