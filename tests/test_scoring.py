"""
Pruebas simples de las funciones principales.
Se corren con: python tests/test_scoring.py
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proveedores.validaciones import limpiar_razon_social, validar_cuit_simulado
from proveedores.scoring import calcular_puntaje_riesgo, clasificar_proveedor
from proveedores.textos import extraer_codigo_expediente, detectar_palabras_clave

PONDERACIONES_TEST = {"incidencias": 5, "dias_vencido": 0.5}


def test_limpiar_razon_social():
    assert limpiar_razon_social("  proveedor sur s.a.  ") == "Proveedor Sur S.A."


def test_validar_cuit_simulado():
    assert validar_cuit_simulado("30-71234567-9") is True
    assert validar_cuit_simulado("123") is False


def test_calcular_puntaje_riesgo():
    puntaje = calcular_puntaje_riesgo(3, 15, PONDERACIONES_TEST)
    assert puntaje == 22.5


def test_clasificar_proveedor():
    assert clasificar_proveedor(35, 0.9) == "suspendido"
    assert clasificar_proveedor(20, 0.9) == "requiere revisión"
    assert clasificar_proveedor(10, 0.9) == "observado"
    assert clasificar_proveedor(2, 0.95) == "habilitado"


def test_extraer_codigo_expediente():
    texto = "Expediente: EXP-2024-00123 - Estado: en revisión"
    assert extraer_codigo_expediente(texto) == "EXP-2024-00123"
    assert extraer_codigo_expediente("texto sin expediente") is None


def test_detectar_palabras_clave():
    texto = "el proveedor fue sancionado por incumplimiento de plazos"
    encontradas = detectar_palabras_clave(texto, ["incumplimiento", "sancionado", "inhabilitado"])
    assert encontradas == ["incumplimiento", "sancionado"]


if __name__ == "__main__":
    test_limpiar_razon_social()
    test_validar_cuit_simulado()
    test_calcular_puntaje_riesgo()
    test_clasificar_proveedor()
    test_extraer_codigo_expediente()
    test_detectar_palabras_clave()
    print("Todas las pruebas pasaron correctamente.")
