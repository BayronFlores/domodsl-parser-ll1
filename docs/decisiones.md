# Decisiones del grupo (tarea T01 — Día 1, los tres integrantes)

## Dominio y propósito
**DomoDSL** es un lenguaje de reglas para la **automatización de una casa inteligente (IoT)**:
"cuando ocurra esta condición, ejecuta estas acciones". El programa no ejecuta las reglas; el objetivo
del proyecto es *reconocerlas* (validar su sintaxis), informar errores útiles y construir un AST.

Se eligió este dominio porque es el ejemplo orientativo del enunciado, las reglas condición→acción son naturales,
y las condiciones obligan a resolver precedencia y asociatividad en la gramática.

## Tres reglas de ejemplo acordadas
```
WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;
WHEN movimiento == TRUE THEN activar alarma, encender luz_pasillo 80;
WHEN NOT (puerta == TRUE) AND (hora >= 22 OR hora < 6) THEN bloquear puerta_principal;
```

## Decisiones de diseño
| Decisión | Motivo |
|---|---|
| Palabras reservadas insensibles a mayúsculas (`WHEN` = `when`) | Mantiene el comportamiento de la función léxica base entregada por el docente. |
| Un programa es una o más reglas; cada regla termina en `;` | Cumple "más de una sentencia"; el `;` da un delimitador claro para el parser. |
| Precedencia `NOT` > `AND` > `OR`, asociatividad izquierda | Se codifica en la gramática (no en el código) para evitar ambigüedad. |
| Extensión creativa: `NOT`, paréntesis, múltiples acciones separadas por coma y acciones con parámetros | Propia del dominio y no decorativa: modifica gramática, FIRST/FOLLOW, tabla, parsers y pruebas. |
| Dos parsers: descenso recursivo (AST) y dirigido por tabla LL(1) (árbol de derivación + traza) | Permite verificar que gramática, tabla y código coinciden. |
| Se informa solo el primer error | Simplicidad; la recuperación en modo pánico queda como trabajo futuro. |
| Sin generadores de parsers; solo biblioteca estándar de Python | Exigencia del enunciado. |
