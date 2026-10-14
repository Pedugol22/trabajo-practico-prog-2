"""
Respeto de robots.txt (buenas prácticas de scraping, N09/N10).

Antes de descargar una página se lee el robots.txt del sitio y se consulta si la URL
está permitida para nuestro User-Agent. Si no se puede leer el archivo por un error de
red o del servidor, se actúa de forma conservadora y no se descarga nada.
"""

from urllib import robotparser
from urllib.parse import urlparse

import requests

from config.ajustes import PARAMETROS_HTTP

_cache = {}


def _cargar_robots(base):
    parser = robotparser.RobotFileParser()
    try:
        respuesta = requests.get(
            f"{base}/robots.txt",
            headers={"User-Agent": PARAMETROS_HTTP["user_agent"]},
            timeout=PARAMETROS_HTTP["timeout"],
        )
    except requests.RequestException:
        parser.disallow_all = True
        return parser

    if respuesta.status_code == 200:
        parser.parse(respuesta.text.splitlines())
    elif 400 <= respuesta.status_code < 500:
        parser.allow_all = True
    else:
        parser.disallow_all = True
    return parser


def puede_descargar(url):
    """True si el robots.txt del sitio permite pedir esa URL con nuestro User-Agent."""
    partes = urlparse(url)
    base = f"{partes.scheme}://{partes.netloc}"
    if base not in _cache:
        _cache[base] = _cargar_robots(base)
    return _cache[base].can_fetch(PARAMETROS_HTTP["user_agent"], url)


def limpiar_cache():
    _cache.clear()
