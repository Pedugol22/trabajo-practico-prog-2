"""Cálculo de puntaje de riesgo y clasificación de proveedores."""

from proveedores.validaciones import limpiar_razon_social, validar_cuit_simulado


def calcular_puntaje_riesgo(incidencias, dias_vencido, ponderaciones):
    return (
        incidencias * ponderaciones["incidencias"]
        + dias_vencido * ponderaciones["dias_vencido"]
    )


def clasificar_proveedor(puntaje_riesgo, cumplimiento_documental):
    if puntaje_riesgo >= 30:
        return "suspendido"
    elif puntaje_riesgo >= 15 or cumplimiento_documental < 0.8:
        return "requiere revisión"
    elif puntaje_riesgo >= 5:
        return "observado"
    else:
        return "habilitado"


def evaluar_proveedor(nombre, cuit, incidencias, dias_vencido,
                       cumplimiento_documental, ponderaciones):
    nombre_limpio = limpiar_razon_social(nombre)
    cuit_valido = validar_cuit_simulado(cuit)
    puntaje = calcular_puntaje_riesgo(incidencias, dias_vencido, ponderaciones)
    estado = clasificar_proveedor(puntaje, cumplimiento_documental)

    return {
        "nombre": nombre_limpio,
        "cuit_valido": cuit_valido,
        "puntaje": puntaje,
        "estado": estado,
    }
