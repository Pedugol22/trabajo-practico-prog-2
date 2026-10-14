"""
Cliente de la API pública "Central de Deudores" del Banco Central (BCRA).

API PÚBLICA vs. PRIVADA (N13)
-----------------------------
Esta API es pública: cualquier desarrollador puede usarla, está documentada
abiertamente y no requiere autenticación (el BCRA solo limita el tráfico por IP).
Una API privada/interna (por ejemplo el sistema de compras de la empresa) exigiría
token corporativo y solo sería accesible desde la red interna.

Endpoints usados (todos GET), según la documentación oficial v1.0:
    /Deudas/{identificacion}                     situación en el último período
    /Deudas/Historicas/{identificacion}          últimos 24 meses
    /Deudas/ChequesRechazados/{identificacion}   cheques rechazados y causales

Códigos de error documentados: 400 (el identificador no tiene 11 dígitos),
404 (sin datos para ese CUIT) y 500 (falla del servidor).
"""

import requests

from config.ajustes import FUENTES, PARAMETROS_HTTP, BCRA_CA_BUNDLE


class BcraError(Exception):
    """Error genérico al consultar el BCRA."""


class BcraNoEncontrado(BcraError):
    """El BCRA no tiene datos registrados para ese CUIT (HTTP 404)."""


class BcraNoDisponible(BcraError):
    """No se pudo llegar al BCRA (timeout, red caída, error 5xx, SSL)."""


def _pedir(ruta):
    url = f"{FUENTES['bcra_deudores']}/{ruta}"
    encabezados = {
        "Accept": "application/json",
        "User-Agent": PARAMETROS_HTTP["user_agent"],
    }
    try:
        respuesta = requests.get(
            url, headers=encabezados, timeout=PARAMETROS_HTTP["timeout"], verify=BCRA_CA_BUNDLE
        )
    except requests.exceptions.SSLError as error:
        raise BcraNoDisponible(
            "Error de certificado SSL al conectar con el BCRA. Probá actualizar certifi "
            "(pip install --upgrade certifi) o definir BCRA_CA_BUNDLE en el .env. "
            f"Detalle: {error}"
        ) from error
    except requests.exceptions.Timeout as error:
        raise BcraNoDisponible("El BCRA no respondió a tiempo (timeout).") from error
    except requests.exceptions.RequestException as error:
        raise BcraNoDisponible(f"No se pudo conectar con el BCRA: {error}") from error

    if respuesta.status_code == 404:
        raise BcraNoEncontrado("El BCRA no tiene datos para la identificación consultada.")
    if respuesta.status_code == 400:
        raise BcraError("El BCRA rechazó la identificación (deben ser 11 dígitos).")
    if respuesta.status_code >= 500:
        raise BcraNoDisponible(f"El BCRA respondió con error de servidor ({respuesta.status_code}).")
    if respuesta.status_code != 200:
        raise BcraError(f"Respuesta inesperada del BCRA: HTTP {respuesta.status_code}.")

    try:
        return respuesta.json().get("results", {})
    except ValueError as error:
        raise BcraError("El BCRA devolvió una respuesta que no es JSON válido.") from error


def consultar_deudas(cuit):
    """Deudas del último período informado (JSON 'results' del BCRA)."""
    return _pedir(f"Deudas/{cuit}")


def consultar_deudas_historicas(cuit):
    """Deudas de los últimos 24 meses."""
    return _pedir(f"Deudas/Historicas/{cuit}")


def consultar_cheques_rechazados(cuit):
    """
    Cheques rechazados. Un 404 significa que no hay cheques rechazados
    registrados, por eso se devuelve una estructura vacía en vez de un error.
    """
    try:
        return _pedir(f"Deudas/ChequesRechazados/{cuit}")
    except BcraNoEncontrado:
        return {"causales": []}


def resumir_deudas(resultado):
    """
    Resume la respuesta de /Deudas tomando el período más reciente.

    Campos del BCRA que se usan: situacion (1 a 5), monto (miles de pesos),
    diasAtrasoPago, refinanciaciones, situacionJuridica, irrecDisposicionTecnica,
    enRevision, procesoJud.
    """
    periodos = resultado.get("periodos") or []
    if not periodos:
        return {
            "denominacion": resultado.get("denominacion"), "periodo": None, "entidades": 0,
            "situacion_maxima": 0, "monto_total_miles": 0.0, "dias_atraso_max": 0,
            "proceso_judicial": False, "situacion_juridica": False,
            "irrecuperable": False, "en_revision": False, "refinanciaciones": False,
        }

    periodo = max(periodos, key=lambda p: p.get("periodo", ""))
    entidades = periodo.get("entidades") or []

    return {
        "denominacion": resultado.get("denominacion"),
        "periodo": periodo.get("periodo"),
        "entidades": len(entidades),
        "situacion_maxima": max((e.get("situacion") or 0 for e in entidades), default=0),
        "monto_total_miles": sum(e.get("monto") or 0 for e in entidades),
        "dias_atraso_max": max((e.get("diasAtrasoPago") or 0 for e in entidades), default=0),
        "proceso_judicial": any(e.get("procesoJud") for e in entidades),
        "situacion_juridica": any(e.get("situacionJuridica") for e in entidades),
        "irrecuperable": any(e.get("irrecDisposicionTecnica") for e in entidades),
        "en_revision": any(e.get("enRevision") for e in entidades),
        "refinanciaciones": any(e.get("refinanciaciones") for e in entidades),
    }


def resumir_cheques(resultado):
    """Cuenta cheques rechazados y multas impagas a partir de /ChequesRechazados."""
    total = 0
    impagos = 0
    for causal in resultado.get("causales") or []:
        for entidad in causal.get("entidades") or []:
            for cheque in entidad.get("detalle") or []:
                total += 1
                if str(cheque.get("estadoMulta") or "").upper() == "IMPAGA":
                    impagos += 1
    return {"cheques_rechazados": total, "multas_impagas": impagos}
