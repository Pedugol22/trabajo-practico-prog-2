import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api_propia.servidor import app
from apis import bcra
from config import ajustes

CUIT = "30711111111"
CLAVE = "clave-de-prueba"
CABECERAS = {"X-API-Key": CLAVE}

DEUDAS = {"denominacion": "EMPRESA DE PRUEBA S.A.", "periodos": [
    {"periodo": "202509", "entidades": [{"situacion": 1, "monto": 20}]}]}


class TestApiPropia(unittest.TestCase):
    def setUp(self):
        self.cliente = TestClient(app)
        parche = patch.object(ajustes, "API_KEYS_VALIDAS", [CLAVE])
        parche.start()
        self.addCleanup(parche.stop)

    def test_salud_es_publica(self):
        self.assertEqual(self.cliente.get("/salud").json(), {"estado": "ok"})

    def test_sin_api_key_401(self):
        self.assertEqual(self.cliente.get(f"/proveedores/{CUIT}/bcra").status_code, 401)

    def test_api_key_incorrecta_401(self):
        r = self.cliente.get(f"/proveedores/{CUIT}/bcra", headers={"X-API-Key": "mala"})
        self.assertEqual(r.status_code, 401)

    def test_sin_claves_configuradas_503(self):
        with patch.object(ajustes, "API_KEYS_VALIDAS", []):
            r = self.cliente.get(f"/proveedores/{CUIT}/bcra", headers=CABECERAS)
        self.assertEqual(r.status_code, 503)

    def test_cuit_invalido_422(self):
        r = self.cliente.get("/proveedores/30711111112/bcra", headers=CABECERAS)
        self.assertEqual(r.status_code, 422)

    def test_persona_fisica_422(self):
        r = self.cliente.get("/proveedores/20711111116/bcra", headers=CABECERAS)
        self.assertEqual(r.status_code, 422)

    @patch("api_propia.servidor.bcra.consultar_cheques_rechazados", return_value={"causales": []})
    @patch("api_propia.servidor.bcra.consultar_deudas", return_value=DEUDAS)
    def test_consulta_bcra_ok(self, *_):
        r = self.cliente.get(f"/proveedores/30-71111111-1/bcra", headers=CABECERAS)
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertEqual(cuerpo["cuit"], CUIT)
        self.assertEqual(cuerpo["deudas"]["situacion_maxima"], 1)

    @patch("api_propia.servidor.bcra.consultar_deudas", side_effect=bcra.BcraNoEncontrado("x"))
    def test_consulta_bcra_sin_datos_404(self, _):
        r = self.cliente.get(f"/proveedores/{CUIT}/bcra", headers=CABECERAS)
        self.assertEqual(r.status_code, 404)

    @patch("api_propia.servidor.bcra.consultar_deudas", side_effect=bcra.BcraNoDisponible("caído"))
    def test_bcra_caido_502(self, _):
        r = self.cliente.get(f"/proveedores/{CUIT}/bcra", headers=CABECERAS)
        self.assertEqual(r.status_code, 502)

    @patch("proveedores.servicio.bcra.consultar_cheques_rechazados", return_value={"causales": []})
    @patch("proveedores.servicio.bcra.consultar_deudas", return_value=DEUDAS)
    def test_evaluar_post_ok(self, *_):
        r = self.cliente.post("/proveedores/evaluar", headers=CABECERAS,
                              json={"cuit": CUIT, "incidencias_internas": 0, "cumplimiento_documental": 1.0})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["estado"], "habilitado")

    def test_evaluar_post_valida_el_cuerpo(self):
        r = self.cliente.post("/proveedores/evaluar", headers=CABECERAS,
                              json={"cuit": CUIT, "cumplimiento_documental": 5})
        self.assertEqual(r.status_code, 422)

    def test_evaluar_post_requiere_clave(self):
        r = self.cliente.post("/proveedores/evaluar", json={"cuit": CUIT})
        self.assertEqual(r.status_code, 401)


if __name__ == "__main__":
    unittest.main()
