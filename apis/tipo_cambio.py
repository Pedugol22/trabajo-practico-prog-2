"""
Segunda API pública de práctica: cotización del dólar oficial (dolarapi.com).
No requiere clave. Se deja como ejemplo adicional de consumo de API pública (N18).
"""

import requests

from config.ajustes import PARAMETROS_HTTP

URL_DOLAR = "https://dolarapi.com/v1/dolares/oficial"


def obtener_dolar_actual():
    """Devuelve el valor de venta del dólar oficial, o None si no se pudo consultar."""
    try:
        respuesta = requests.get(URL_DOLAR, timeout=PARAMETROS_HTTP["timeout"])
        respuesta.raise_for_status()
        return respuesta.json()["venta"]
    except (requests.RequestException, KeyError, ValueError) as error:
        print(f"No fue posible consultar la API de tipo de cambio: {error}")
        return None
