"""Búsquedas sobre el árbol HTML usando find_all con distintos filtros."""

import re


def buscar_filas_proveedores(soup):
    return soup.find_all("tr", class_="fila-proveedor")


def buscar_filas_por_estado(soup, estado):
    return soup.find_all("tr", attrs={"data-estado": estado})


def buscar_texto_con_patron(soup, patron):
    return soup.find_all(string=re.compile(patron))


def es_fila_de_riesgo(tag):
    return tag.name == "tr" and tag.get("data-estado") in ["suspendido", "observado"]


def buscar_filas_de_riesgo(soup, limite=None):
    if limite is not None:
        return soup.find_all(es_fila_de_riesgo, limit=limite)
    return soup.find_all(es_fila_de_riesgo)
