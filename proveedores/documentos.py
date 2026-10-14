"""
Cumplimiento documental y vencimientos de un proveedor (N02, N04, N06).

Cada documento tiene un nombre, un estado (ver ESTADOS_DOCUMENTALES en config) y, opcionalmente,
una fecha de vencimiento. La fecha manda: si ya pasó, el documento está vencido aunque el
estado informado diga "vigente".
"""

from datetime import date, timedelta

from config.ajustes import ESTADOS_DOCUMENTALES

DIAS_AVISO_VENCIMIENTO = 30   # un documento que vence dentro de este plazo figura "por vencer"


def estado_del_documento(documento, hoy=None):
    """Devuelve el estado efectivo de un documento: vigente, por_vencer, vencido o faltante."""
    hoy = hoy or date.today()
    estado = documento.get("estado") or "vigente"
    if estado not in ESTADOS_DOCUMENTALES:
        raise ValueError(f"Estado documental desconocido: {estado!r}. "
                         f"Opciones: {', '.join(ESTADOS_DOCUMENTALES)}")
    if estado == "faltante":
        return estado

    vence = documento.get("vence")
    if vence is not None:
        if vence < hoy:
            return "vencido"
        if vence - hoy <= timedelta(days=DIAS_AVISO_VENCIMIENTO):
            return "por_vencer"
    return estado


def evaluar_documentos(documentos, hoy=None):
    """
    Resume una lista de documentos (diccionarios con nombre, estado y vence).
    cumplimiento = promedio del aporte de cada estado (0 a 1).
    """
    if not documentos:
        return {"cumplimiento": 1.0, "vencidos": 0, "por_vencer": 0, "faltantes": 0, "detalle": []}

    detalle = [
        {"nombre": doc.get("nombre", "documento"), "estado": estado_del_documento(doc, hoy)}
        for doc in documentos
    ]
    aportes = [ESTADOS_DOCUMENTALES[item["estado"]] for item in detalle]
    estados = [item["estado"] for item in detalle]
    return {
        "cumplimiento": round(sum(aportes) / len(aportes), 2),
        "vencidos": estados.count("vencido"),
        "por_vencer": estados.count("por_vencer"),
        "faltantes": estados.count("faltante"),
        "detalle": detalle,
    }
