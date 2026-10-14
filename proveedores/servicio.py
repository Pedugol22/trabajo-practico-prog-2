"""
Servicio que junta todo: consulta el BCRA por CUIT y evalúa al proveedor.
Lo usa la API propia (api_propia/servidor.py).
"""

from apis import bcra
from proveedores.scoring import evaluar_proveedor, RESUMEN_BCRA_VACIO


def evaluar_por_cuit(cuit, incidencias_internas=0, cumplimiento_documental=1.0):
    """
    Consulta deudas y cheques rechazados en el BCRA y devuelve la evaluación.
    Propaga BcraNoDisponible / BcraError para que quien llame decida qué responder.
    """
    try:
        resumen = bcra.resumir_deudas(bcra.consultar_deudas(cuit))
        encontrado = True
    except bcra.BcraNoEncontrado:
        resumen = dict(RESUMEN_BCRA_VACIO)
        encontrado = False

    cheques = bcra.resumir_cheques(bcra.consultar_cheques_rechazados(cuit))
    return evaluar_proveedor(cuit, resumen, cheques, incidencias_internas,
                             cumplimiento_documental, encontrado)
