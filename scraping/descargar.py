"""Descarga de páginas web con requests."""

import time
import requests

USER_AGENT = "TP UADE - Programacion 2 - Seguimiento de proveedores"


def descargar_html(url, timeout=10):
    respuesta = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    respuesta.raise_for_status()
    return respuesta.text


def descargar_varias(urls, pausa_segundos=2):
    # Pausa entre pedidos para no saturar el servidor
    resultados = []
    for url in urls:
        try:
            html = descargar_html(url)
        except requests.RequestException as error:
            print(f"No se pudo descargar {url}: {error}")
            html = None
        resultados.append((url, html))
        time.sleep(pausa_segundos)
    return resultados
