"""Procesamiento de cadenas: expedientes, adjudicatarios, observaciones y alertas."""

import re

# Palabras clave legales que, si aparecen en un aviso, merecen atención.
PALABRAS_CLAVE_LEGALES = [
    "incumplimiento", "sancion", "inhabilit", "rescisi", "fracasad", "desiert",
]

# Ejemplo real de redacción en el Boletín Oficial:
#   "Adjudicar a la Firma NOMBRE CUIT NRO 30XXXXXXXXX, el renglón Nro: 1;
#    por un total de PESOS ... ($ 1.234.567,89)"
_PATRON_CUIT = re.compile(
    r"CUIT\s*(?:N[°ºo]\.?|NRO\.?|N[úu]mero)?\s*:?\s*(\d{2}-?\d{8}-?\d)",
    re.IGNORECASE,
)
_PATRON_MONTO = re.compile(r"\$\s*([\d.]+,\d{2})")
_PREFIJOS_NOMBRE = re.compile(
    r"(?:a\s+la\s+firma|a\s+la\s+empresa|a\s+la\s+razón\s+social|a\s+la\s+razon\s+social|"
    r"adjudicatari[oa]\s*:|oferente\s*:|proveedor\s*:)\s*",
    re.IGNORECASE,
)


def extraer_codigo_expediente(texto):
    """
    Extrae el número de expediente de un aviso. Formato real observado:
    "Expediente N°: EX-2026-XXXX-APN-... Objeto: ..."
    Devuelve None si el texto no lo trae.
    """
    coincidencia = re.search(r"Expediente\s*N[°º]?\s*:\s*(.+?)\s+Objeto\s*:", texto, re.IGNORECASE)
    return coincidencia.group(1).strip() if coincidencia else None


def extraer_objeto(texto):
    """Extrae el 'Objeto:' de la contratación (hasta 'Texto del Aviso' si existe)."""
    coincidencia = re.search(r"Objeto\s*:\s*(.+?)(?:\s+Texto del Aviso\s*:|$)", texto, re.IGNORECASE)
    return coincidencia.group(1).strip() if coincidencia else None


def convertir_monto(texto_monto):
    """'1.234.567,89' -> 1234567.89"""
    return float(texto_monto.replace(".", "").replace(",", "."))


def extraer_adjudicatarios(texto):
    """
    Busca en el texto de un aviso cada 'Firma ... CUIT ...' y devuelve una lista
    de diccionarios: {"razon_social", "cuit", "monto"}.

    Estrategia: se localiza cada CUIT; el nombre es el texto que lo precede
    (después de 'a la Firma') y el monto es el primer '$ ...' que aparece
    entre ese CUIT y el siguiente.
    """
    texto = " ".join(texto.split())
    cuits = list(_PATRON_CUIT.finditer(texto))
    resultado = []
    visto = set()

    for i, cuit_match in enumerate(cuits):
        inicio_previo = cuits[i - 1].end() if i > 0 else 0
        previo = texto[inicio_previo:cuit_match.start()]
        partes = _PREFIJOS_NOMBRE.split(previo)
        nombre = partes[-1] if len(partes) > 1 else previo[-70:]
        nombre = nombre.strip(" ,;:-")
        if not nombre:
            continue

        fin = cuits[i + 1].start() if i + 1 < len(cuits) else len(texto)
        monto_match = _PATRON_MONTO.search(texto[cuit_match.end():fin])
        monto = convertir_monto(monto_match.group(1)) if monto_match else None

        cuit = re.sub(r"\D", "", cuit_match.group(1))
        if (cuit, nombre) in visto:
            continue
        visto.add((cuit, nombre))
        resultado.append({"razon_social": nombre, "cuit": cuit, "monto": monto})

    return resultado


def detectar_palabras_clave(texto, palabras_clave=PALABRAS_CLAVE_LEGALES):
    """Devuelve las palabras clave (raíces) que aparecen en el texto."""
    texto_normalizado = texto.lower()
    return [palabra for palabra in palabras_clave if palabra in texto_normalizado]


def preparar_observacion(nombre_proveedor, lista_motivos):
    """Arma una observación legible uniendo los motivos con .join()."""
    if not lista_motivos:
        return f"El proveedor {nombre_proveedor} no presenta observaciones."
    motivos_texto = "; ".join(lista_motivos)
    return f"El proveedor {nombre_proveedor} presenta las siguientes observaciones: {motivos_texto}."
