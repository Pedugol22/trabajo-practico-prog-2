"""Validación y limpieza de datos de proveedores (CUIT y razón social)."""

import re

# CUIT que empiezan con estos prefijos corresponden a personas jurídicas (empresas).
# Los prefijos 20, 23, 24 y 27 son personas humanas: el proyecto no cruza datos
# de deuda de personas humanas, solo de empresas proveedoras.
PREFIJOS_PERSONA_JURIDICA = ("30", "33", "34")

_PESOS_CUIT = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]


def limpiar_cuit(cuit):
    """Deja solo los dígitos: '30-50001091-2' -> '30500010912'."""
    return re.sub(r"\D", "", str(cuit))


def validar_cuit(cuit):
    """
    Valida un CUIT/CUIL real: 11 dígitos y dígito verificador correcto
    (algoritmo módulo 11).
    """
    digitos = limpiar_cuit(cuit)
    if len(digitos) != 11:
        return False

    suma = sum(int(d) * peso for d, peso in zip(digitos[:10], _PESOS_CUIT))
    resto = suma % 11
    verificador = 0 if resto == 0 else 11 - resto
    if verificador == 10:
        return False
    return verificador == int(digitos[10])


def es_persona_juridica(cuit):
    return limpiar_cuit(cuit)[:2] in PREFIJOS_PERSONA_JURIDICA


def formatear_cuit(cuit):
    d = limpiar_cuit(cuit)
    return f"{d[:2]}-{d[2:10]}-{d[10]}" if len(d) == 11 else d


def normalizar_razon_social(nombre):
    """
    Unifica una razón social para poder compararla: sin espacios repetidos,
    en mayúsculas y sin puntuación suelta al final.
    """
    return " ".join(str(nombre).split()).upper().rstrip(".,;:")


def limpiar_razon_social(nombre):
    """Versión legible para mostrar: sin espacios de más y con Mayúsculas Iniciales."""
    return " ".join(str(nombre).split()).title()
