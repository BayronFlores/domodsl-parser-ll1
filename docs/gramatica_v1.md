# Gramática v1 de DomoDSL — **CONGELADA** (tarea T03, fin del Día 2)

Desde este momento la numeración de producciones no cambia. Un cambio exige una *solicitud de cambio*
aprobada por los tres (ver `CONTRATOS.md`, contrato K7).

* **Símbolo inicial:** `programa`
* **No terminales (14):** `programa`, `programa_p`, `regla`, `condicion`, `condicion_p`, `termino`, `termino_p`, `factor`, `comparacion`, `valor`, `acciones`, `acciones_p`, `accion`, `parametros`
* **Terminales (14):** `WHEN`, `THEN`, `PUNTO_COMA`, `OR`, `AND`, `NOT`, `PARENT_IZQ`, `PARENT_DER`, `ID`, `OP_REL`, `NUM`, `TRUE`, `FALSE`, `COMA` (más el marcador de fin de entrada `$`)
* `ε` = cadena vacía. El sufijo `_p` indica un no terminal auxiliar (x′).

## Producciones
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

## Cómo leerla
* Un **programa** es una o más reglas (1–3). Una **regla** es `WHEN condición THEN acciones ;` (4).
* **Condiciones** en tres niveles para codificar la precedencia: `condicion` (OR, la menor), `termino` (AND) y
  `factor` (NOT, paréntesis o comparación, la mayor) (5–13). Una **comparación** es `ID OP_REL valor` (14).
* **Valores:** número, `TRUE`, `FALSE` o identificador (15–18).
* **Acciones:** lista separada por comas (19–21); cada una es `verbo dispositivo [parámetros]` (22–24).

## Extensión creativa incluida
1. `NOT` (producción 11).
2. Paréntesis de agrupación (producción 12).
3. Múltiples acciones con parámetros (producciones 19–24).

## Requisitos mínimos del enunciado
* 7 palabras reservadas: `WHEN THEN AND OR NOT TRUE FALSE` (≥ 4).
* Identificadores (`ID`) y valores numéricos (`NUM`) y booleanos (`TRUE`/`FALSE`).
* 9 operadores: `> < >= <= == !=` más `AND OR NOT` (≥ 3).
* Sentencia principal `WHEN … THEN … ;`, varias reglas por programa y construcciones compuestas.
