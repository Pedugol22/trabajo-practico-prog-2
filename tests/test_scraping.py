import unittest
from pathlib import Path
from unittest.mock import patch

from scraping import boletin_oficial
from scraping.buscador import buscar_en_avisos, filtrar_por_rubro
from scraping.parsear import parsear_detalle, parsear_listado

FIXTURES = Path(__file__).parent / "fixtures"


def leer(nombre):
    return (FIXTURES / nombre).read_text(encoding="utf-8")


class TestParseo(unittest.TestCase):
    def test_listado_ignora_links_que_no_son_avisos(self):
        avisos = parsear_listado(leer("listado_tercera.html"))
        self.assertEqual(len(avisos), 3)
        self.assertEqual(avisos[0]["id_aviso"], "900001")
        self.assertEqual(avisos[0]["organismo"], "MINISTERIO DE PRUEBA")
        self.assertEqual(avisos[0]["proceso"], "Licitación Pública Nº 1/2026")
        self.assertTrue(avisos[0]["url_detalle"].endswith("/detalleAviso/tercera/900001/20261014"))

    def test_listado_vacio_si_no_hay_contenedor(self):
        self.assertEqual(parsear_listado("<html><body></body></html>"), [])

    def test_filtro_por_rubro(self):
        avisos = parsear_listado(leer("listado_tercera.html"))
        adjudicaciones = filtrar_por_rubro(avisos)
        self.assertEqual([a["id_aviso"] for a in adjudicaciones], ["900001", "900002"])

    def test_buscar_en_avisos(self):
        avisos = parsear_listado(leer("listado_tercera.html"))
        self.assertEqual(len(buscar_en_avisos(avisos, "ejemplo")), 1)

    def test_detalle(self):
        detalle = parsear_detalle(leer("detalle_adjudicacion.html"))
        self.assertIn("Licitación Pública", detalle["titulo"])
        self.assertIn("CUIT NRO 30711111111", detalle["texto"])


class TestBoletinOficial(unittest.TestCase):
    def test_url_listado(self):
        self.assertTrue(boletin_oficial.url_listado().endswith("/seccion/tercera"))
        self.assertTrue(boletin_oficial.url_listado("20261014").endswith("/seccion/tercera/20261014"))

    def test_adjudicatarios_filtra_personas_fisicas(self):
        def falso_descargar(url):
            return leer("listado_tercera.html") if "/seccion/" in url else leer("detalle_adjudicacion.html")

        with patch.object(boletin_oficial, "descargar_html", side_effect=falso_descargar):
            resultado = boletin_oficial.obtener_adjudicatarios("20261014", limite_avisos=1)

        cuits = [r["cuit"] for r in resultado]
        self.assertEqual(cuits, ["30711111111", "33711111137"])
        self.assertNotIn("20711111116", cuits)
        self.assertEqual(resultado[0]["expediente"], "EX-2026-00000001-APN-DGA#MPR")
        self.assertIn("fracasad", resultado[0]["alertas"])
        self.assertEqual(resultado[0]["organismo"], "MINISTERIO DE PRUEBA")


if __name__ == "__main__":
    unittest.main()
