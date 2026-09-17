"""Registro de fuentes web públicas: URL, dominio e IP."""

import socket

# Reemplazar por las URLs reales elegidas por el equipo tras revisar
# términos de uso y robots.txt de cada sitio.
FUENTES_PUBLICAS = [
    {
        "nombre": "Boletín Oficial",
        "url": "https://www.boletinoficial.gob.ar",
        "dominio": "www.boletinoficial.gob.ar",
    },
    {
        "nombre": "Portal de Compras Públicas",
        "url": "https://comprar.gob.ar",
        "dominio": "comprar.gob.ar",
    },
]


def obtener_ip(dominio):
    try:
        return socket.gethostbyname(dominio)
    except socket.gaierror:
        return None


def listar_fuentes_con_ip(fuentes=FUENTES_PUBLICAS):
    resultado = []
    for fuente in fuentes:
        ip = obtener_ip(fuente["dominio"])
        resultado.append({**fuente, "ip": ip})
    return resultado
