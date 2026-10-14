"""
Servicio que junta todo: consulta el BCRA por CUIT y evalúa al proveedor.
Lo usa la API propia (api_propia/servidor.py).
"""

from apis import bcra
from config import ajustes
from proveedores.documentos import evaluar_documentos
from proveedores.scoring import evaluar_proveedor, RESUMEN_BCRA_VACIO


def evaluar_por_cuit(cuit, incidencias_internas=0, cumplimiento_documental=1.0, documentos=None):
    """
    Consulta deudas y cheques rechazados en el BCRA y devuelve la evaluación.
    Si se envía la lista de documentos, el cumplimiento y los vencimientos se calculan
    a partir de ella (y reemplazan al valor suelto de cumplimiento_documental).
    Propaga BcraNoDisponible / BcraError para que quien llame decida qué responder.
    """
    try:
        resumen = bcra.resumir_deudas(bcra.consultar_deudas(cuit))
        encontrado = True
    except bcra.BcraNoEncontrado:
        resumen = dict(RESUMEN_BCRA_VACIO)
        encontrado = False

    cheques = bcra.resumir_cheques(bcra.consultar_cheques_rechazados(cuit))

    resumen_documentos = None
    documentos_vencidos = 0
    if documentos:
        resumen_documentos = evaluar_documentos(documentos)
        cumplimiento_documental = resumen_documentos["cumplimiento"]
        documentos_vencidos = resumen_documentos["vencidos"]

    return evaluar_proveedor(
        cuit, resumen, cheques, incidencias_internas, cumplimiento_documental, encontrado,
        documentos_vencidos=documentos_vencidos,
        es_critico=cuit in ajustes.PROVEEDORES_CRITICOS,
        resumen_documentos=resumen_documentos,
    )
