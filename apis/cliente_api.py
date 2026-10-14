"""
Cliente de NUESTRA API (api_propia). Usa requests con autenticación por API key.

Métodos HTTP usados en el proyecto:
  GET   -> consultar datos sin modificar nada (/salud, /proveedores/{cuit}/bcra)
  POST  -> enviar datos para que el servidor los procese (/proveedores/evaluar)

Cuándo serían necesarios los demás métodos (no se usan acá porque la API no guarda datos):
  PUT    -> reemplazar completo un recurso existente (ej: reescribir la ficha de un proveedor)
  PATCH  -> modificar solo algunos campos (ej: cambiar solo el estado de un proveedor)
  DELETE -> borrar un recurso (ej: dar de baja un proveedor de la base interna)
"""

import requests

from config.ajustes import API_URL, API_KEY_CLIENTE, PARAMETROS_HTTP


class ErrorApiPropia(Exception):
    """La API propia respondió con error o no está disponible."""


def _encabezados():
    if not API_KEY_CLIENTE:
        raise ErrorApiPropia(
            "Falta la variable de entorno PROVEEDORES_API_KEY (ver .env.example)."
        )
    return {"X-API-Key": API_KEY_CLIENTE, "Accept": "application/json"}


def _interpretar(respuesta):
    """Traduce los códigos de estado en resultados o errores claros."""
    if respuesta.status_code == 200:
        return respuesta.json()
    try:
        detalle = respuesta.json().get("detail", respuesta.text)
    except ValueError:
        detalle = respuesta.text
    mensajes = {
        401: "No autorizado: la API key es inválida o falta.",
        404: "No se encontraron datos para ese CUIT.",
        422: "Datos inválidos",
        502: "La API propia no pudo consultar al BCRA",
        503: "La API propia no está configurada (sin API keys)",
    }
    base = mensajes.get(respuesta.status_code, f"Error HTTP {respuesta.status_code}")
    raise ErrorApiPropia(f"{base}: {detalle}")


def _llamar(metodo, ruta, **kwargs):
    try:
        respuesta = requests.request(
            metodo, f"{API_URL}{ruta}", headers=_encabezados(),
            timeout=PARAMETROS_HTTP["timeout"], **kwargs
        )
    except requests.exceptions.ConnectionError as error:
        raise ErrorApiPropia(
            f"No se pudo conectar con la API en {API_URL}. ¿Está corriendo 'python main.py servidor'?"
        ) from error
    except requests.exceptions.Timeout as error:
        raise ErrorApiPropia("La API propia no respondió a tiempo.") from error
    return _interpretar(respuesta)


def consultar_bcra(cuit):
    """GET /proveedores/{cuit}/bcra"""
    return _llamar("GET", f"/proveedores/{cuit}/bcra")


def evaluar_proveedor(cuit, incidencias_internas=0, cumplimiento_documental=1.0):
    """POST /proveedores/evaluar con el CUIT y las evaluaciones internas en el cuerpo JSON."""
    cuerpo = {
        "cuit": cuit,
        "incidencias_internas": incidencias_internas,
        "cumplimiento_documental": cumplimiento_documental,
    }
    return _llamar("POST", "/proveedores/evaluar", json=cuerpo)
