"""
Scraping REAL del Boletín Oficial de la República Argentina (tercera sección:
contrataciones del Estado). Se extraen las ADJUDICACIONES: a qué empresas (razón social
y CUIT) adjudicó el Estado, por qué monto y en qué expediente.

robots.txt del sitio (verificado el 14/10/2026) sólo restringe la segunda sección.
"""

from datetime import date

from config.ajustes import FUENTES
from proveedores.textos import (
    detectar_palabras_clave, extraer_adjudicatarios, extraer_codigo_expediente, extraer_objeto,
)
from proveedores.validaciones import es_persona_juridica, validar_cuit
from scraping.buscador import filtrar_por_rubro
from scraping.descargar import descargar_html
from scraping.parsear import parsear_detalle, parsear_listado


def url_listado(fecha=None):
    """URL del listado de la tercera sección. Sin fecha: la edición vigente."""
    base = f"{FUENTES['boletin_oficial']}/seccion/tercera"
    if fecha is None:
        return base
    if isinstance(fecha, date):
        fecha = fecha.strftime("%Y%m%d")
    return f"{base}/{fecha}"


def obtener_avisos_adjudicacion(fecha=None):
    """Descarga el listado del día y devuelve sólo los avisos del rubro ADJUDICACIONES."""
    html = descargar_html(url_listado(fecha))
    return filtrar_por_rubro(parsear_listado(html, FUENTES["boletin_oficial"]))


def obtener_adjudicatarios(fecha=None, limite_avisos=10):
    """
    Recorre hasta `limite_avisos` avisos de adjudicación y devuelve una lista de
    adjudicatarios con CUIT válido de persona jurídica:
    {razon_social, cuit, monto, organismo, expediente, objeto, alertas, fuente}.
    """
    resultados = []
    for aviso in obtener_avisos_adjudicacion(fecha)[:limite_avisos]:
        detalle = parsear_detalle(descargar_html(aviso["url_detalle"]))
        texto = detalle["texto"]
        expediente = extraer_codigo_expediente(texto)
        objeto = extraer_objeto(texto)
        alertas = detectar_palabras_clave(texto)
        for adj in extraer_adjudicatarios(texto):
            if not validar_cuit(adj["cuit"]) or not es_persona_juridica(adj["cuit"]):
                continue
            resultados.append({
                **adj,
                "organismo": aviso["organismo"],
                "expediente": expediente,
                "objeto": objeto,
                "alertas": alertas,
                "fuente": aviso["url_detalle"],
            })
    return resultados
