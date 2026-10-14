import unittest

from proveedores.textos import (
    convertir_monto, detectar_palabras_clave, extraer_adjudicatarios,
    extraer_codigo_expediente, extraer_objeto,
)
from proveedores.validaciones import (
    es_persona_juridica, formatear_cuit, limpiar_cuit, normalizar_razon_social, validar_cuit,
)

# CUIT sintéticos con dígito verificador correcto (no corresponden a empresas reales conocidas)
CUIT_JURIDICA = "30711111111"
CUIT_FISICA = "20711111116"


class TestValidaciones(unittest.TestCase):
    def test_cuit_valido_con_y_sin_guiones(self):
        self.assertTrue(validar_cuit(CUIT_JURIDICA))
        self.assertTrue(validar_cuit("30-71111111-1"))

    def test_cuit_con_digito_incorrecto(self):
        self.assertFalse(validar_cuit("30711111112"))

    def test_cuit_largo_incorrecto_o_con_letras(self):
        self.assertFalse(validar_cuit("1234"))
        self.assertFalse(validar_cuit("3071111111A"))

    def test_persona_juridica(self):
        self.assertTrue(es_persona_juridica(CUIT_JURIDICA))
        self.assertFalse(es_persona_juridica(CUIT_FISICA))

    def test_formato(self):
        self.assertEqual(limpiar_cuit("30-71111111-1"), CUIT_JURIDICA)
        self.assertEqual(formatear_cuit(CUIT_JURIDICA), "30-71111111-1")

    def test_normalizar_razon_social(self):
        self.assertEqual(normalizar_razon_social("  empresa   de prueba s.a.,"), "EMPRESA DE PRUEBA S.A")


class TestTextos(unittest.TestCase):
    TEXTO = (
        "Expediente N°: EX-2026-1-APN-X Objeto: Compra de insumos Texto del Aviso: "
        "Adjudicar a la Firma ALFA S.A. CUIT NRO 30711111111, el renglón Nro: 1; "
        "por un total de PESOS UNO ($ 1.250.000,50), a la Firma BETA S.R.L. "
        "CUIT NRO 33711111137, el renglón Nro: 2; por un total de PESOS DOS ($ 2.000,00)."
    )

    def test_expediente_y_objeto(self):
        self.assertEqual(extraer_codigo_expediente(self.TEXTO), "EX-2026-1-APN-X")
        self.assertEqual(extraer_objeto(self.TEXTO)[:16], "Compra de insumo")

    def test_monto(self):
        self.assertEqual(convertir_monto("1.250.000,50"), 1250000.50)

    def test_adjudicatarios(self):
        adjudicatarios = extraer_adjudicatarios(self.TEXTO)
        self.assertEqual([a["cuit"] for a in adjudicatarios], [CUIT_JURIDICA, "33711111137"])
        self.assertEqual(adjudicatarios[0]["razon_social"], "ALFA S.A.")
        self.assertEqual(adjudicatarios[0]["monto"], 1250000.50)
        self.assertEqual(adjudicatarios[1]["monto"], 2000.0)

    def test_palabras_clave(self):
        self.assertEqual(detectar_palabras_clave("Se declara fracasado el renglón"), ["fracasad"])


if __name__ == "__main__":
    unittest.main()
