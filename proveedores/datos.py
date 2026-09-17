"""Datos base de proveedores."""

PROVEEDORES = [
    {
        "nombre": "proveedor sur s.a.",
        "cuit": "30-71234567-9",
        "incidencias": 3,
        "dias_vencido": 15,
        "cumplimiento_documental": 0.7,
    },
    {
        "nombre": "insumos norte srl",
        "cuit": "30-98765432-1",
        "incidencias": 0,
        "dias_vencido": 2,
        "cumplimiento_documental": 1.0,
    },
    {
        "nombre": "  logistica del plata  ",
        "cuit": "20-33445566-7",
        "incidencias": 6,
        "dias_vencido": 40,
        "cumplimiento_documental": 0.4,
    },
    {
        "nombre": "repuestos central",
        "cuit": "123",  # CUIT inválido a propósito, para probar la validación
        "incidencias": 1,
        "dias_vencido": 0,
        "cumplimiento_documental": 0.95,
    },
]

# Peso de cada factor en el cálculo del puntaje de riesgo
PONDERACIONES = {
    "incidencias": 5,
    "dias_vencido": 0.5,
}

ESTADOS_DOCUMENTALES = {
    "completo": "Toda la documentación fue entregada",
    "parcial": "Falta al menos un documento",
    "vencido": "Hay documentación con fecha vencida",
}

PALABRAS_CLAVE_LEGALES = ["incumplimiento", "sancionado", "inhabilitado"]

DESTINATARIOS_COMITE = ["comite.compras@empresa.com", "auditoria@empresa.com"]
