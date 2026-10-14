"""
Puntaje de riesgo y clasificación de proveedores.

Entradas: datos REALES de la Central de Deudores del BCRA (situación crediticia,
atrasos, cheques rechazados, procesos judiciales) + evaluaciones internas de la
empresa (incidencias y cumplimiento documental).
"""

# Peso de cada factor (diccionario): si el comité cambia criterios, se edita acá
# y no la lógica de las funciones.
PONDERACIONES = {
    "situacion": 12,                  # puntos por cada nivel por encima de 1 (1 = normal)
    "dias_atraso": 0.1,               # puntos por día de atraso en el pago
    "tope_dias_atraso": 360,          # los días de atraso se cuentan hasta este tope
    "cheque_rechazado": 4,            # puntos por cada cheque rechazado
    "multa_impaga": 6,                # puntos por cada multa de cheque impaga
    "proceso_judicial": 25,
    "situacion_juridica": 20,
    "irrecuperable": 25,
    "en_revision": 3,
    "refinanciaciones": 5,
    "incidencia_interna": 5,          # puntos por incidencia registrada por la empresa
    "incumplimiento_documental": 20,  # se multiplica por (1 - cumplimiento documental)
}

UMBRALES = {"suspendido": 60, "requiere_revision": 30, "observado": 10}

NOMBRES_SITUACION = {
    0: "sin informar", 1: "normal", 2: "con seguimiento especial / riesgo bajo",
    3: "con problemas / riesgo medio", 4: "alto riesgo de insolvencia / riesgo alto",
    5: "irrecuperable",
}


def calcular_puntaje_riesgo(bcra, cheques, incidencias_internas, cumplimiento_documental,
                            ponderaciones=PONDERACIONES):
    """
    Suma puntos de riesgo usando operadores aritméticos y devuelve
    (puntaje_total, evidencias), donde evidencias explica cada aporte.
    """
    evidencias = []

    def sumar(factor, detalle, puntos):
        if puntos > 0:
            evidencias.append({"factor": factor, "detalle": detalle, "puntos": round(puntos, 2)})
        return puntos

    total = 0.0
    situacion = bcra["situacion_maxima"]
    total += sumar(
        "situacion crediticia",
        f"peor situación informada: {situacion} ({NOMBRES_SITUACION.get(situacion, '?')})",
        max(situacion - 1, 0) * ponderaciones["situacion"],
    )

    dias = min(bcra["dias_atraso_max"], ponderaciones["tope_dias_atraso"])
    total += sumar("atraso de pago", f"{bcra['dias_atraso_max']} días de atraso máximo",
                   dias * ponderaciones["dias_atraso"])

    total += sumar("cheques rechazados", f"{cheques['cheques_rechazados']} cheque(s) rechazado(s)",
                   cheques["cheques_rechazados"] * ponderaciones["cheque_rechazado"])
    total += sumar("multas impagas", f"{cheques['multas_impagas']} multa(s) impaga(s)",
                   cheques["multas_impagas"] * ponderaciones["multa_impaga"])

    if bcra["proceso_judicial"]:
        total += sumar("proceso judicial", "informa proceso judicial", ponderaciones["proceso_judicial"])
    if bcra["situacion_juridica"]:
        total += sumar("situación jurídica", "informa situación jurídica", ponderaciones["situacion_juridica"])
    if bcra["irrecuperable"]:
        total += sumar("irrecuperable", "irrecuperable por disposición técnica", ponderaciones["irrecuperable"])
    if bcra["en_revision"]:
        total += sumar("en revisión", "deuda en revisión", ponderaciones["en_revision"])
    if bcra["refinanciaciones"]:
        total += sumar("refinanciaciones", "tiene refinanciaciones", ponderaciones["refinanciaciones"])

    total += sumar("incidencias internas", f"{incidencias_internas} incidencia(s) registradas por la empresa",
                   incidencias_internas * ponderaciones["incidencia_interna"])
    total += sumar("cumplimiento documental", f"cumplimiento documental {cumplimiento_documental:.0%}",
                   (1 - cumplimiento_documental) * ponderaciones["incumplimiento_documental"])

    return round(total, 2), evidencias


def clasificar_proveedor(puntaje, bcra, cheques, cumplimiento_documental, umbrales=UMBRALES):
    """
    Clasifica en: habilitado, observado, requiere revisión o suspendido.
    Las condiciones graves (situación 4-5, proceso judicial, irrecuperable)
    suspenden sin importar el puntaje.
    """
    if (bcra["situacion_maxima"] >= 4 or bcra["proceso_judicial"] or bcra["irrecuperable"]
            or puntaje >= umbrales["suspendido"]):
        return "suspendido"
    elif (bcra["situacion_maxima"] == 3 or puntaje >= umbrales["requiere_revision"]
            or cumplimiento_documental < 0.8):
        return "requiere revisión"
    elif (bcra["situacion_maxima"] == 2 or puntaje >= umbrales["observado"]
            or cheques["cheques_rechazados"] > 0):
        return "observado"
    else:
        return "habilitado"


RESUMEN_BCRA_VACIO = {
    "denominacion": None, "periodo": None, "entidades": 0, "situacion_maxima": 0,
    "monto_total_miles": 0.0, "dias_atraso_max": 0, "proceso_judicial": False,
    "situacion_juridica": False, "irrecuperable": False, "en_revision": False,
    "refinanciaciones": False,
}


def evaluar_proveedor(cuit, bcra, cheques, incidencias_internas=0, cumplimiento_documental=1.0,
                      encontrado_en_bcra=True):
    """
    Consolida todo en un solo resultado: puntaje, estado y evidencias.
    Si el BCRA no tiene datos del CUIT, se aclara: ausencia de datos no es lo
    mismo que ausencia de riesgo.
    """
    puntaje, evidencias = calcular_puntaje_riesgo(
        bcra, cheques, incidencias_internas, cumplimiento_documental
    )
    estado = clasificar_proveedor(puntaje, bcra, cheques, cumplimiento_documental)

    if not encontrado_en_bcra:
        evidencias.append({
            "factor": "sin datos del BCRA",
            "detalle": "El CUIT no figura en la Central de Deudores (404): no registra deudas "
                       "informadas, lo que no garantiza ausencia de riesgo.",
            "puntos": 0,
        })

    return {
        "cuit": cuit,
        "denominacion": bcra.get("denominacion"),
        "estado": estado,
        "puntaje": puntaje,
        "evidencias": evidencias,
        "datos_bcra": bcra,
        "datos_cheques": cheques,
        "encontrado_en_bcra": encontrado_en_bcra,
    }
