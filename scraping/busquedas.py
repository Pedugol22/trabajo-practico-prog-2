"""
Formas de buscar elementos con BeautifulSoup (N11 y N12), aplicadas al HTML real del
listado de la tercera sección del Boletín Oficial.

Cada función muestra una técnica distinta de find / find_all. `resumen_busquedas`
las ejecuta todas y devuelve cuántos elementos encontró cada una.
"""

import re

from bs4 import BeautifulSoup

PATRON_AVISO = re.compile(r"^/detalleAviso/tercera/\d+/\d{8}")


def por_etiqueta(sopa):
    """Por nombre de etiqueta: todos los títulos de rubro (h5)."""
    return sopa.find_all("h5")


def por_clase(sopa):
    """Por clase CSS (class_ lleva guion bajo porque class es palabra reservada en Python)."""
    return sopa.find_all("p", class_="item")


def por_id(sopa):
    """Por id: find devuelve un solo elemento (o None)."""
    return sopa.find(id="avisosSeccionDiv")


def por_atributos(sopa):
    """Por atributos con expresión regular: enlaces cuyo href apunta a un aviso."""
    return sopa.find_all("a", attrs={"href": PATRON_AVISO})


def por_texto(sopa, patron="adjudicaci"):
    """Por texto contenido (string=): rubros cuyo texto contiene la palabra buscada."""
    return sopa.find_all("h5", string=re.compile(patron, re.IGNORECASE))


def por_funcion(sopa):
    """Con una función lambda: enlaces a avisos que además contienen un organismo (p.item)."""
    return sopa.find_all(
        lambda etiqueta: etiqueta.name == "a"
        and etiqueta.get("href", "").startswith("/detalleAviso")
        and etiqueta.find("p", class_="item") is not None
    )


def combinada(sopa, limite=2):
    """Combina etiqueta + clase + límite de resultados."""
    return sopa.find_all("div", class_="linea-aviso", limit=limite)


def extraer_valores(etiqueta):
    """
    Valores típicos de una etiqueta: texto, href, src, class, id y atributos data-*.
    Lo que no existe se devuelve vacío (None, lista o diccionario vacío).
    """
    return {
        "texto": etiqueta.get_text(" ", strip=True),
        "href": etiqueta.get("href"),
        "src": etiqueta.get("src"),
        "clases": etiqueta.get("class", []),
        "id": etiqueta.get("id"),
        "data": {
            nombre: valor for nombre, valor in etiqueta.attrs.items() if nombre.startswith("data-")
        },
    }


def resumen_busquedas(html):
    """Ejecuta todas las técnicas sobre un HTML y cuenta los resultados de cada una."""
    sopa = BeautifulSoup(html, "html.parser")
    return {
        "por etiqueta (h5)": len(por_etiqueta(sopa)),
        "por clase (p.item)": len(por_clase(sopa)),
        "por id (#avisosSeccionDiv)": 1 if por_id(sopa) is not None else 0,
        "por atributos (href con regex)": len(por_atributos(sopa)),
        "por texto (rubros 'adjudicaci')": len(por_texto(sopa)),
        "por función lambda (a + p.item)": len(por_funcion(sopa)),
        "combinada (div.linea-aviso, límite 2)": len(combinada(sopa)),
    }
