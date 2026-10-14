"""
Descarga de páginas con requests: timeout, User-Agent identificable, manejo de errores,
respeto de robots.txt y pausa entre pedidos para no sobrecargar el sitio.
"""

import time

import requests

from config.ajustes import PARAMETROS_HTTP, SCRAPING_HABILITADO
from scraping.robots import puede_descargar


class ErrorScraping(Exception):
    """No se pudo descargar la página (bloqueo por robots, red, HTTP, scraping deshabilitado)."""


_ultimo_pedido = 0.0


def _esperar_turno():
    global _ultimo_pedido
    faltante = PARAMETROS_HTTP["pausa_entre_pedidos"] - (time.monotonic() - _ultimo_pedido)
    if faltante > 0:
        time.sleep(faltante)
    _ultimo_pedido = time.monotonic()


def descargar_html(url):
    """Devuelve el HTML (texto) de una URL permitida. Lanza ErrorScraping si no se puede."""
    if not SCRAPING_HABILITADO:
        raise ErrorScraping("El scraping está deshabilitado (SCRAPING_HABILITADO=false).")
    if not puede_descargar(url):
        raise ErrorScraping(f"robots.txt no permite descargar {url}")

    _esperar_turno()
    try:
        respuesta = requests.get(
            url,
            headers={"User-Agent": PARAMETROS_HTTP["user_agent"], "Accept": "text/html"},
            timeout=PARAMETROS_HTTP["timeout"],
        )
    except requests.exceptions.Timeout as error:
        raise ErrorScraping(f"Tiempo de espera agotado al pedir {url}") from error
    except requests.exceptions.RequestException as error:
        raise ErrorScraping(f"Error de red al pedir {url}: {error}") from error

    if respuesta.status_code == 404:
        raise ErrorScraping(f"No existe la página {url} (404). Puede no haber edición ese día.")
    if respuesta.status_code != 200:
        raise ErrorScraping(f"{url} respondió HTTP {respuesta.status_code}")

    respuesta.encoding = respuesta.encoding or "utf-8"
    return respuesta.text
