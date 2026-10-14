"""Filtros sobre los avisos ya parseados (uso de patrones y búsqueda de texto)."""

import re


def filtrar_por_rubro(avisos, palabra="adjudicaci"):
    """Se queda con los avisos cuyo rubro contiene la palabra (sin distinguir mayúsculas)."""
    patron = re.compile(palabra, re.IGNORECASE)
    return [a for a in avisos if patron.search(a.get("rubro", ""))]


def buscar_en_avisos(avisos, texto):
    """Avisos cuyo organismo o proceso mencionan el texto buscado."""
    patron = re.compile(re.escape(texto), re.IGNORECASE)
    return [
        a for a in avisos
        if patron.search(a.get("organismo", "")) or patron.search(a.get("proceso", ""))
    ]
