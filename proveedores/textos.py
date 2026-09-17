"""Procesamiento de texto: expedientes y observaciones."""


def extraer_codigo_expediente(texto):
    if "Expediente:" not in texto:
        return None
    partes = texto.split(":")
    codigo = partes[1].strip().split(" - ")[0]
    return codigo


def preparar_observacion(nombre_proveedor, lista_motivos):
    motivos_texto = ", ".join(lista_motivos)
    return (
        f"El proveedor {nombre_proveedor} presenta las siguientes "
        f"observaciones: {motivos_texto}."
    )


def detectar_palabras_clave(texto, palabras_clave):
    texto_normalizado = texto.lower()
    return [palabra for palabra in palabras_clave if palabra in texto_normalizado]
