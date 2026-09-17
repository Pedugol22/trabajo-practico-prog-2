"""Extracción de texto y atributos de elementos HTML."""


def extraer_datos_proveedor(fila_tag):
    # .get() en vez de [...] para no romper si falta algún atributo
    enlace = fila_tag.find("a")

    return {
        "nombre": enlace.get_text(strip=True) if enlace else "sin nombre",
        "url_detalle": enlace.get("href") if enlace else None,
        "estado_web": enlace.get("data-estado", "sin dato") if enlace else "sin dato",
    }
