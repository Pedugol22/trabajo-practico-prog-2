"""
Plataforma de evaluación y seguimiento de proveedores
Solicitud de proyecto 3 - Programación 2 (UADE)

Para correrlo: python main.py
"""

from proveedores.datos import PROVEEDORES, PONDERACIONES, PALABRAS_CLAVE_LEGALES
from proveedores.scoring import evaluar_proveedor
from proveedores.textos import extraer_codigo_expediente, preparar_observacion, detectar_palabras_clave

from web_info.fuentes import listar_fuentes_con_ip

from scraping.parsear import obtener_soup
from scraping.buscador import buscar_filas_proveedores, buscar_filas_de_riesgo
from scraping.extractor import extraer_datos_proveedor
from scraping.pagina_ejemplo import HTML_EJEMPLO

from apis.tipo_cambio import obtener_dolar_actual


def seccion(titulo):
    print("\n" + "=" * 60)
    print(titulo)
    print("=" * 60)


def parte_1_evaluacion_proveedores():
    seccion("1) EVALUACIÓN DE PROVEEDORES")
    for datos_proveedor in PROVEEDORES:
        resultado = evaluar_proveedor(
            datos_proveedor["nombre"],
            datos_proveedor["cuit"],
            datos_proveedor["incidencias"],
            datos_proveedor["dias_vencido"],
            datos_proveedor["cumplimiento_documental"],
            PONDERACIONES,
        )
        print(
            f"- {resultado['nombre']:<25} "
            f"CUIT válido: {str(resultado['cuit_valido']):<5} "
            f"puntaje: {resultado['puntaje']:>5} "
            f"estado: {resultado['estado']}"
        )


def parte_2_textos_y_observaciones():
    seccion("2) PROCESAMIENTO DE TEXTO")

    texto_expediente = "Expediente: EXP-2024-00123 - Estado: en revisión"
    codigo = extraer_codigo_expediente(texto_expediente)
    print(f"Código de expediente extraído: {codigo}")

    texto_observacion = "el proveedor fue sancionado por incumplimiento de plazos"
    encontradas = detectar_palabras_clave(texto_observacion, PALABRAS_CLAVE_LEGALES)
    mensaje = preparar_observacion("Proveedor Sur S.A.", encontradas)
    print(mensaje)


def parte_3_fuentes_web():
    seccion("3) FUENTES WEB PÚBLICAS")
    for fuente in listar_fuentes_con_ip():
        ip = fuente["ip"] if fuente["ip"] else "no resuelta (sin conexión en este entorno)"
        print(f"- {fuente['nombre']}: {fuente['url']} -> IP: {ip}")


def parte_4_scraping():
    seccion("4) SCRAPING DE LA PÁGINA DE PROVEEDORES")
    print("(Página HTML de ejemplo, ver README para el paso a un sitio real.)\n")

    soup = obtener_soup(HTML_EJEMPLO)

    filas = buscar_filas_proveedores(soup)
    print(f"Filas de proveedores encontradas: {len(filas)}")

    for fila in filas:
        datos = extraer_datos_proveedor(fila)
        print(f"  - {datos}")

    filas_riesgo = buscar_filas_de_riesgo(soup)
    print(f"\nFilas en estado de riesgo (suspendido/observado): {len(filas_riesgo)}")
    for fila in filas_riesgo:
        datos = extraer_datos_proveedor(fila)
        print(f"  ⚠ {datos['nombre']} (estado: {datos['estado_web']})")


def parte_5_api_publica():
    seccion("5) API PÚBLICA - TIPO DE CAMBIO")
    dolar = obtener_dolar_actual()
    if dolar is not None:
        print(f"Cotización dólar oficial (venta): ${dolar}")
    else:
        print("No se pudo consultar la API en este momento (revisar conexión).")


if __name__ == "__main__":
    parte_1_evaluacion_proveedores()
    parte_2_textos_y_observaciones()
    parte_3_fuentes_web()
    parte_4_scraping()
    parte_5_api_publica()
    print("\nListo.\n")
