import unittest
from unittest.mock import MagicMock, patch

import requests

from apis import bcra
from proveedores import scoring
from proveedores.servicio import evaluar_por_cuit

CUIT = "30711111111"


def respuesta(status, cuerpo=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = cuerpo if cuerpo is not None else {}
    return r


DEUDAS = {
    "identificacion": 30711111111,
    "denominacion": "EMPRESA DE PRUEBA S.A.",
    "periodos": [
        {"periodo": "202508", "entidades": [{"situacion": 1, "monto": 10}]},
        {"periodo": "202509", "entidades": [
            {"situacion": 2, "monto": 100.5, "diasAtrasoPago": 40, "procesoJud": False},
            {"situacion": 3, "monto": 50, "diasAtrasoPago": 100, "enRevision": True},
        ]},
    ],
}

CHEQUES = {"causales": [{"causal": "SIN FONDOS", "entidades": [
    {"entidad": 11, "detalle": [{"estadoMulta": "IMPAGA"}, {"estadoMulta": "PAGADA"}]},
]}]}


class TestClienteBcra(unittest.TestCase):
    def setUp(self):
        parche = patch("apis.bcra.time.sleep")
        self.sleep = parche.start()
        self.addCleanup(parche.stop)

    @patch("apis.bcra.requests.get")
    def test_reintenta_si_el_bcra_corta_la_conexion(self, get):
        get.side_effect = [
            requests.exceptions.ConnectionError("Connection aborted"),
            respuesta(200, {"results": DEUDAS}),
        ]
        self.assertEqual(bcra.consultar_deudas(CUIT)["denominacion"], "EMPRESA DE PRUEBA S.A.")
        self.assertEqual(get.call_count, 2)

    @patch("apis.bcra.requests.get")
    def test_desiste_tras_los_reintentos(self, get):
        get.side_effect = requests.exceptions.ConnectionError("Connection aborted")
        with self.assertRaises(bcra.BcraNoDisponible):
            bcra.consultar_deudas(CUIT)
        self.assertEqual(get.call_count, bcra.REINTENTOS)

    @patch("apis.bcra.requests.get")
    def test_404_no_se_reintenta(self, get):
        get.return_value = respuesta(404)
        with self.assertRaises(bcra.BcraNoEncontrado):
            bcra.consultar_deudas(CUIT)
        self.assertEqual(get.call_count, 1)

    @patch("apis.bcra.requests.get")
    def test_consulta_ok_devuelve_results(self, get):
        get.return_value = respuesta(200, {"status": 200, "results": DEUDAS})
        self.assertEqual(bcra.consultar_deudas(CUIT)["denominacion"], "EMPRESA DE PRUEBA S.A.")
        self.assertIn(f"Deudas/{CUIT}", get.call_args.args[0])

    @patch("apis.bcra.requests.get")
    def test_404_es_no_encontrado(self, get):
        get.return_value = respuesta(404)
        with self.assertRaises(bcra.BcraNoEncontrado):
            bcra.consultar_deudas(CUIT)

    @patch("apis.bcra.requests.get")
    def test_404_en_cheques_es_lista_vacia(self, get):
        get.return_value = respuesta(404)
        self.assertEqual(bcra.consultar_cheques_rechazados(CUIT), {"causales": []})

    @patch("apis.bcra.requests.get")
    def test_5xx_y_timeout_son_no_disponible(self, get):
        get.return_value = respuesta(500)
        with self.assertRaises(bcra.BcraNoDisponible):
            bcra.consultar_deudas(CUIT)
        get.side_effect = requests.exceptions.Timeout()
        with self.assertRaises(bcra.BcraNoDisponible):
            bcra.consultar_deudas(CUIT)

    @patch("apis.bcra.requests.get")
    def test_error_ssl_da_mensaje_util(self, get):
        get.side_effect = requests.exceptions.SSLError("certificate verify failed")
        with self.assertRaises(bcra.BcraNoDisponible) as ctx:
            bcra.consultar_deudas(CUIT)
        self.assertIn("certifi", str(ctx.exception))

    def test_resumen_toma_el_ultimo_periodo(self):
        resumen = bcra.resumir_deudas(DEUDAS)
        self.assertEqual(resumen["periodo"], "202509")
        self.assertEqual(resumen["situacion_maxima"], 3)
        self.assertEqual(resumen["monto_total_miles"], 150.5)
        self.assertEqual(resumen["dias_atraso_max"], 100)
        self.assertTrue(resumen["en_revision"])
        self.assertFalse(resumen["proceso_judicial"])

    def test_resumen_de_cheques(self):
        self.assertEqual(bcra.resumir_cheques(CHEQUES), {"cheques_rechazados": 2, "multas_impagas": 1})


class TestScoring(unittest.TestCase):
    def test_sin_deudas_es_habilitado(self):
        evaluacion = scoring.evaluar_proveedor(
            CUIT, bcra.resumir_deudas({"periodos": [{"periodo": "202509", "entidades": [{"situacion": 1, "monto": 5}]}]}),
            {"cheques_rechazados": 0, "multas_impagas": 0},
        )
        self.assertEqual(evaluacion["estado"], "habilitado")

    def test_proceso_judicial_suspende(self):
        deudas = bcra.resumir_deudas({"periodos": [{"periodo": "202509", "entidades": [
            {"situacion": 2, "monto": 5, "procesoJud": True}]}]})
        evaluacion = scoring.evaluar_proveedor(CUIT, deudas, {"cheques_rechazados": 0, "multas_impagas": 0})
        self.assertEqual(evaluacion["estado"], "suspendido")
        self.assertTrue(any(e["factor"] for e in evaluacion["evidencias"]))

    def test_situacion_3_requiere_revision(self):
        evaluacion = scoring.evaluar_proveedor(
            CUIT, bcra.resumir_deudas(DEUDAS), bcra.resumir_cheques(CHEQUES))
        self.assertIn(evaluacion["estado"], ("requiere revisión", "suspendido"))
        self.assertGreater(evaluacion["puntaje"], 0)

    def test_incumplimiento_documental_baja_el_estado(self):
        evaluacion = scoring.evaluar_proveedor(
            CUIT, bcra.resumir_deudas({"periodos": [{"periodo": "202509", "entidades": [{"situacion": 1, "monto": 5}]}]}),
            {"cheques_rechazados": 0, "multas_impagas": 0}, cumplimiento_documental=0.5)
        self.assertEqual(evaluacion["estado"], "requiere revisión")


class TestServicio(unittest.TestCase):
    @patch("proveedores.servicio.bcra.consultar_cheques_rechazados", return_value={"causales": []})
    @patch("proveedores.servicio.bcra.consultar_deudas", side_effect=bcra.BcraNoEncontrado("x"))
    def test_cuit_sin_datos_en_bcra(self, *_):
        evaluacion = evaluar_por_cuit(CUIT)
        self.assertFalse(evaluacion["encontrado_en_bcra"])
        self.assertTrue(any("BCRA" in e["detalle"] or "BCRA" in e["factor"] for e in evaluacion["evidencias"]))

    @patch("proveedores.servicio.bcra.consultar_deudas", side_effect=bcra.BcraNoDisponible("caído"))
    def test_bcra_caido_se_propaga(self, _):
        with self.assertRaises(bcra.BcraNoDisponible):
            evaluar_por_cuit(CUIT)


if __name__ == "__main__":
    unittest.main()
