"""
Consumo de una API pública: cotización del dólar oficial (dolarapi.com).

API pública vs. privada: esta API es pública, no requiere autenticación
corporativa y su documentación es abierta para cualquier desarrollador.
Una API privada/interna (por ejemplo, el ERP de compras de una empresa)
en cambio exigiría un token corporativo y solo sería accesible desde la
red interna, sin documentación pública.

Se eligió una API de tipo de cambio porque varios proveedores cotizan
en dólares, y la plataforma necesita poder convertir esos montos.
"""

import requests

URL_DOLAR = "https://dolarapi.com/v1/dolares/oficial"


def obtener_dolar_actual():
    try:
        respuesta = requests.get(URL_DOLAR, timeout=10)
        respuesta.raise_for_status()
        datos = respuesta.json()
        return datos["venta"]
    except requests.RequestException as error:
        print(f"No fue posible consultar la API de tipo de cambio: {error}")
        return None
