"""
Información de las fuentes web reales que usa el proyecto: dominio, IP y estado.
Sirve de evidencia de qué sitios se consultan (N09).
"""

import socket
from urllib.parse import urlparse

from config.ajustes import FUENTES


def resolver_ip(url):
    """Devuelve la IP del dominio de la URL, o None si no se pudo resolver."""
    dominio = urlparse(url).hostname
    try:
        return socket.gethostbyname(dominio)
    except (socket.gaierror, TypeError):
        return None


def describir_fuentes():
    """Lista de {nombre, url, dominio, ip} de cada fuente configurada."""
    descripcion = []
    for nombre, url in FUENTES.items():
        descripcion.append({
            "nombre": nombre,
            "url": url,
            "dominio": urlparse(url).hostname,
            "ip": resolver_ip(url),
        })
    return descripcion
