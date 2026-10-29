"""Pruebas automáticas (unittest). Ejecutar:  python -m unittest -v   o   python test_parser.py"""
import unittest

import gramatica as g
from arbol import And, Comparacion, Not, Or
from casos_prueba import CASOS
from errores import ErrorDSL, ErrorSintactico
from ejecutar_pruebas import ejecutar
from lexer import analizador_lexico, tokens_a_tuplas
from parser_ll1 import parsear_texto_ll1
from parser_rd import parsear


class TestLexer(unittest.TestCase):
    def test_ejemplo_del_enunciado(self):
        t = tokens_a_tuplas(analizador_lexico("WHEN temperatura > 28 THEN encender ventilador;"))
        self.assertEqual(t, [("WHEN", "WHEN"), ("ID", "temperatura"), ("OP_REL", ">"),
                             ("NUM", "28"), ("THEN", "THEN"), ("ID", "encender"),
                             ("ID", "ventilador"), ("PUNTO_COMA", ";")])

    def test_posiciones(self):
        t = analizador_lexico("WHEN a\n> 1")
        self.assertEqual((t[2].linea, t[2].columna, t[2].pos), (2, 1, 7))

    def test_token_fin(self):
        self.assertEqual(analizador_lexico("")[-1].tipo, "$")


class TestGramatica(unittest.TestCase):
    def test_first(self):
        esperado = {
            "programa": {"WHEN"}, "programa_p": {"WHEN", "ε"}, "regla": {"WHEN"},
            "condicion": {"NOT", "PARENT_IZQ", "ID"}, "condicion_p": {"OR", "ε"},
            "termino": {"NOT", "PARENT_IZQ", "ID"}, "termino_p": {"AND", "ε"},
            "factor": {"NOT", "PARENT_IZQ", "ID"}, "comparacion": {"ID"},
            "valor": {"NUM", "TRUE", "FALSE", "ID"}, "acciones": {"ID"},
            "acciones_p": {"COMA", "ε"}, "accion": {"ID"},
            "parametros": {"NUM", "TRUE", "FALSE", "ID", "ε"},
        }
        self.assertEqual(g.FIRST, esperado)

    def test_follow(self):
        cierre = {"THEN", "PARENT_DER"}
        esperado = {
            "programa": {"$"}, "programa_p": {"$"}, "regla": {"WHEN", "$"},
            "condicion": cierre, "condicion_p": cierre,
            "termino": cierre | {"OR"}, "termino_p": cierre | {"OR"},
            "factor": cierre | {"OR", "AND"}, "comparacion": cierre | {"OR", "AND"},
            "valor": cierre | {"OR", "AND", "PUNTO_COMA", "COMA", "NUM", "TRUE", "FALSE", "ID"},
            "acciones": {"PUNTO_COMA"}, "acciones_p": {"PUNTO_COMA"},
            "accion": {"COMA", "PUNTO_COMA"}, "parametros": {"COMA", "PUNTO_COMA"},
        }
        self.assertEqual(g.FOLLOW, esperado)

    def test_es_ll1_sin_conflictos(self):
        self.assertEqual(g.CONFLICTOS, [])
        self.assertTrue(g.es_ll1())

    def test_sin_recursion_izquierda(self):
        for a, rhs in g.PRODUCCIONES:
            self.assertNotEqual(rhs[0], a, f"recursión izquierda directa en {a}")

    def test_celdas_clave_de_la_tabla(self):
        self.assertEqual(g.TABLA["programa_p"]["$"], 3)
        self.assertEqual(g.TABLA["termino_p"]["AND"], 9)
        self.assertEqual(g.TABLA["termino_p"]["OR"], 10)
        self.assertEqual(g.TABLA["factor"]["NOT"], 11)
        self.assertEqual(g.TABLA["parametros"]["PUNTO_COMA"], 24)
        self.assertNotIn("THEN", g.TABLA["valor"])


class TestCasos(unittest.TestCase):
    def test_todos_los_casos_con_ambos_parsers(self):
        for cid, _cat, entrada, esperado, fragmento, _obs in CASOS:
            with self.subTest(caso=cid):
                ok_rd, msg_rd, ok_ll1, _msg_ll1 = ejecutar(entrada)
                self.assertEqual("ACEPTA" if ok_rd else "RECHAZA", esperado)
                self.assertEqual(ok_rd, ok_ll1, "ambos analizadores deben coincidir")
                if esperado == "RECHAZA":
                    self.assertIn(fragmento, msg_rd)

    def test_cantidad_minima_de_casos(self):
        cats = [c[1] for c in CASOS]
        self.assertGreaterEqual(cats.count("válida"), 10)
        self.assertGreaterEqual(cats.count("inválida"), 10)
        self.assertGreaterEqual(cats.count("límite"), 5)
        self.assertGreaterEqual(len(CASOS), 25)


class TestAST(unittest.TestCase):
    def cond(self, texto):
        return parsear(f"WHEN {texto} THEN x y;").reglas[0].condicion

    def test_and_tiene_mayor_precedencia_que_or(self):
        c = self.cond("a > 1 OR b > 2 AND c > 3")
        self.assertIsInstance(c, Or)
        self.assertIsInstance(c.der, And)

    def test_asociatividad_izquierda(self):
        c = self.cond("a > 1 OR b > 2 OR c > 3")
        self.assertIsInstance(c.izq, Or)
        self.assertIsInstance(c.der, Comparacion)

    def test_parentesis_cambian_la_agrupacion(self):
        c = self.cond("(a > 1 OR b > 2) AND c > 3")
        self.assertIsInstance(c, And)
        self.assertIsInstance(c.izq, Or)

    def test_not_se_aplica_al_factor(self):
        c = self.cond("NOT a > 1 AND b > 2")
        self.assertIsInstance(c, And)
        self.assertIsInstance(c.izq, Not)

    def test_acciones_y_parametros(self):
        r = parsear("WHEN a > 1 THEN ajustar termostato 22 TRUE, activar alarma;").reglas[0]
        self.assertEqual(len(r.acciones), 2)
        self.assertEqual([p.texto for p in r.acciones[0].parametros], ["22", "TRUE"])

    def test_arbol_de_derivacion_ll1_tiene_hoja_epsilon(self):
        raiz = parsear_texto_ll1("WHEN a > 1 THEN x y;")
        self.assertEqual(raiz.etiqueta, "programa")
        self.assertEqual(raiz.hijos[-1].hijos[0].etiqueta, "ε")


class TestErrores(unittest.TestCase):
    def test_posicion_del_error(self):
        with self.assertRaises(ErrorSintactico) as cm:
            parsear("WHEN temperatura > 28 encender ventilador;")
        e = cm.exception
        self.assertEqual((e.linea, e.columna, e.pos), (1, 23, 22))

    def test_mensaje_incluye_puntero(self):
        with self.assertRaises(ErrorDSL) as cm:
            parsear("WHEN a > THEN x y;")
        self.assertIn("^", cm.exception.con_contexto("WHEN a > THEN x y;"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
