"""Validación y limpieza de datos de proveedores."""


def limpiar_razon_social(nombre):
    return nombre.strip().title()


def validar_cuit_simulado(cuit):
    # Validación de formato (no consulta AFIP real): 11 dígitos sin guiones
    cuit_limpio = cuit.replace("-", "")
    return len(cuit_limpio) == 11 and cuit_limpio.isdigit()
