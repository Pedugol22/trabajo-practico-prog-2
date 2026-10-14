import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from api_propia.servidor import app
from config import ajustes
from proveedores import scoring
from proveedores.documentos import estado_del_documento, evaluar_documentos
from proveedores.servicio import evaluar_por_cuit
from scraping import busquedas
from scraping.boletin_oficial import listar_expedientes
from scraping.descargar import ErrorScraping, descargar_html

FIXTURES = Path(__file__).parent / "fixtures"
HOY = date(2026, 10, 14)
CUIT = "30711111111"
SIN_RIESGO = {"periodos": [{"periodo": "202509", "entidades": [{"situacion": 1, "monto": 5}]}]}
SITUACION_2 = {"periodos": [{"periodo": "202509", "entidades": [{"situacion": 2, "monto": 5}]}]}
SIN_CHEQUES = {"causales": []}


class TestDocumentos(unittest.TestCase):
    def test_estados_segun_fecha(self):
        self.assertEqual(estado_del_documento({"vence": date(2026, 1, 1)}, HOY), "vencido")
        self.assertEqual(estado_del_documento({"vence": date(2026, 10, 30)}, HOY), "por_vencer")
        self.assertEqual(estado_del_documento({"vence": date(2027, 6, 1)}, HOY), "vigente")
        self.assertEqual(estado_del_documento({"estado": "faltante", "vence": date(2027, 6, 1)}, HOY), "faltante")

    def test_estado_desconocido(self):
        with self.assertRaises(ValueError):
            estado_del_documento({"estado": "inventado"}, HOY)

    def test_resumen(self):
        resumen = evaluar_documentos([
            {"nombre": "constancia", "estado": "vigente"},
            {"nombre": "seguro", "vence": date(2026, 1, 1)},
            {"nombre": "balance", "estado": "faltante"},
            {"nombre": "poder", "vence": date(2026, 10, 20)},
        ], HOY)
        self.assertEqual(resumen["vencidos"], 1)
        self.assertEqual(resumen["faltantes"], 1)
        self.assertEqual(resumen["por_vencer"], 1)
        self.assertEqual(resumen["cumplimiento"], 0.38)   # (1 + 0 + 0 + 0.5) / 4

    def test_sin_documentos_cumple(self):
        self.assertEqual(evaluar_documentos([])["cumplimiento"], 1.0)


class TestScoringNuevo(unittest.TestCase):
    def setUp(self):
        from apis import bcra
        self.bcra_normal = bcra.resumir_deudas(SIN_RIESGO)
        self.bcra_situacion_2 = bcra.resumir_deudas(SITUACION_2)
        self.cheques = {"cheques_rechazados": 0, "multas_impagas": 0}

    def test_documento_vencido_pide_revision_y_suma_puntos(self):
        evaluacion = scoring.evaluar_proveedor(CUIT, self.bcra_normal, self.cheques, documentos_vencidos=2)
        self.assertEqual(evaluacion["estado"], "requiere revisión")
        self.assertIn("documentos vencidos", [e["factor"] for e in evaluacion["evidencias"]])
        self.assertEqual(evaluacion["puntaje"], 16.0)

    def test_proveedor_critico_es_mas_estricto(self):
        comun = scoring.evaluar_proveedor(CUIT, self.bcra_situacion_2, self.cheques)
        critico = scoring.evaluar_proveedor(CUIT, self.bcra_situacion_2, self.cheques, es_critico=True)
        self.assertEqual(comun["estado"], "observado")
        self.assertEqual(critico["estado"], "requiere revisión")
        self.assertGreater(critico["puntaje"], comun["puntaje"])

    def test_critico_sin_riesgo_no_cambia(self):
        evaluacion = scoring.evaluar_proveedor(CUIT, self.bcra_normal, self.cheques, es_critico=True)
        self.assertEqual(evaluacion["estado"], "habilitado")


class TestServicioYApi(unittest.TestCase):
    @patch("proveedores.servicio.bcra.consultar_cheques_rechazados", return_value=SIN_CHEQUES)
    @patch("proveedores.servicio.bcra.consultar_deudas", return_value=SIN_RIESGO)
    def test_servicio_usa_la_lista_de_criticos(self, *_):
        with patch.object(ajustes, "PROVEEDORES_CRITICOS", [CUIT]):
            self.assertTrue(evaluar_por_cuit(CUIT)["es_critico"])
        with patch.object(ajustes, "PROVEEDORES_CRITICOS", []):
            self.assertFalse(evaluar_por_cuit(CUIT)["es_critico"])

    @patch("proveedores.servicio.bcra.consultar_cheques_rechazados", return_value=SIN_CHEQUES)
    @patch("proveedores.servicio.bcra.consultar_deudas", return_value=SIN_RIESGO)
    def test_api_post_con_documentos(self, *_):
        with patch.object(ajustes, "API_KEYS_VALIDAS", ["clave"]):
            r = TestClient(app).post("/proveedores/evaluar", headers={"X-API-Key": "clave"}, json={
                "cuit": CUIT,
                "documentos": [
                    {"nombre": "constancia", "estado": "vigente"},
                    {"nombre": "seguro", "vence": "2020-01-01"},
                ],
            })
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertEqual(cuerpo["estado"], "requiere revisión")
        self.assertEqual(cuerpo["documentos"]["vencidos"], 1)

    def test_api_rechaza_estado_documental_invalido(self):
        with patch.object(ajustes, "API_KEYS_VALIDAS", ["clave"]):
            r = TestClient(app).post("/proveedores/evaluar", headers={"X-API-Key": "clave"}, json={
                "cuit": CUIT, "documentos": [{"nombre": "x", "estado": "raro"}],
            })
        self.assertEqual(r.status_code, 422)


class TestBusquedas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (FIXTURES / "listado_tercera.html").read_text(encoding="utf-8")
        cls.sopa = BeautifulSoup(cls.html, "html.parser")

    def test_cada_tecnica(self):
        self.assertEqual(len(busquedas.por_etiqueta(self.sopa)), 2)
        self.assertEqual(len(busquedas.por_clase(self.sopa)), 4)
        self.assertEqual(busquedas.por_id(self.sopa).name, "div")
        self.assertEqual(len(busquedas.por_atributos(self.sopa)), 3)
        self.assertEqual(len(busquedas.por_texto(self.sopa)), 1)
        self.assertEqual(len(busquedas.por_funcion(self.sopa)), 3)
        self.assertEqual(len(busquedas.combinada(self.sopa)), 2)

    def test_resumen(self):
        resumen = busquedas.resumen_busquedas(self.html)
        self.assertEqual(len(resumen), 7)
        self.assertTrue(all(cantidad >= 1 for cantidad in resumen.values()))

    def test_extraer_valores_incluye_data_attributes(self):
        sopa = BeautifulSoup(
            '<a id="x" class="b c" href="/ruta" data-id="7" data-tipo="aviso"><img src="f.png"> Texto</a>',
            "html.parser",
        )
        valores = busquedas.extraer_valores(sopa.a)
        self.assertEqual(valores["href"], "/ruta")
        self.assertEqual(valores["clases"], ["b", "c"])
        self.assertEqual(valores["id"], "x")
        self.assertEqual(valores["data"], {"data-id": "7", "data-tipo": "aviso"})
        self.assertEqual(valores["texto"], "Texto")
        self.assertEqual(busquedas.extraer_valores(sopa.img)["src"], "f.png")


class TestListasDeControl(unittest.TestCase):
    def test_expedientes_sin_repetir(self):
        adjudicatarios = [{"expediente": "A"}, {"expediente": "B"}, {"expediente": "A"}, {"expediente": None}]
        self.assertEqual(listar_expedientes(adjudicatarios), ["A", "B"])

    def test_dominios_permitidos_son_las_fuentes_reales(self):
        self.assertIn("www.boletinoficial.gob.ar", ajustes.DOMINIOS_PERMITIDOS)
        self.assertIn("api.bcra.gob.ar", ajustes.DOMINIOS_PERMITIDOS)

    def test_descarga_rechaza_dominios_no_permitidos(self):
        with self.assertRaises(ErrorScraping):
            descargar_html("https://sitio-no-permitido.example.com/pagina")


if __name__ == "__main__":
    unittest.main()
