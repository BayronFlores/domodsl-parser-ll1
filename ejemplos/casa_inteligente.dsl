WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;
WHEN movimiento == TRUE THEN activar alarma, encender luz_pasillo 80;
WHEN NOT (puerta == TRUE) AND (hora >= 22 OR hora < 6) THEN bloquear puerta_principal;
WHEN temperatura < 15 THEN ajustar termostato 22 TRUE;
