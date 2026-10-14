"""
Punto de entrada del proyecto.

  python main.py servidor                      levanta la API propia (FastAPI)
  python main.py scrapear [--fecha F] [--limite N]
                                               scraping real del Boletín Oficial (adjudicaciones)
  python main.py consultar <cuit>              evalúa un CUIT llamando a nuestra API (que llama al BCRA);
                                               levanta la API sola si hace falta
  python main.py ranking [--fecha F] [--limite N]
                                               TODO JUNTO: scrapea adjudicatarios, levanta la API sola si
                                               hace falta y los evalúa, ordenados por riesgo
  python main.py inspeccionar [--fecha F]      prueba las búsquedas de BeautifulSoup (find_all) en el listado real
  python main.py fuentes                       muestra las fuentes web usadas y su IP
"""

import argparse
import sys
import threading
import time
from urllib.parse import urlparse

import requests

from apis import cliente_api
from config import ajustes
from proveedores.validaciones import formatear_cuit
from scraping.boletin_oficial import listar_expedientes, obtener_adjudicatarios, url_listado
from scraping.busquedas import resumen_busquedas
from scraping.descargar import ErrorScraping, descargar_html
from web_info.fuentes import describir_fuentes


def comando_servidor(_args):
    import uvicorn
    uvicorn.run("api_propia.servidor:app", host="127.0.0.1", port=8000)


def comando_scrapear(args):
    adjudicatarios = obtener_adjudicatarios(args.fecha, args.limite)
    if not adjudicatarios:
        print("No se encontraron adjudicatarios (puede que no haya edición ese día).")
        return
    for adj in adjudicatarios:
        monto = f"${adj['monto']:,.2f}" if adj["monto"] is not None else "s/d"
        print(f"{formatear_cuit(adj['cuit'])}  {adj['razon_social']}  {monto}")
        print(f"    {adj['organismo']} | Exp. {adj['expediente']}")
        print(f"    {adj['fuente']}")
    print(f"\nExpedientes distintos: {listar_expedientes(adjudicatarios)}")


def comando_inspeccionar(args):
    """Aplica las distintas técnicas de find_all al listado real y cuenta los resultados."""
    html = descargar_html(url_listado(args.fecha))
    for tecnica, cantidad in resumen_busquedas(html).items():
        print(f"{tecnica:<42}{cantidad}")


def comando_consultar(args):
    servidor = _levantar_api_local()
    try:
        _hacer_consulta(args)
    finally:
        if servidor is not None:
            servidor.should_exit = True


def _hacer_consulta(args):
    resultado = cliente_api.evaluar_proveedor(args.cuit)
    print(f"{resultado['denominacion'] or 'Sin denominación'} ({resultado['cuit']})")
    print(f"Estado: {resultado['estado']}  |  Puntaje de riesgo: {resultado['puntaje']}")
    for evidencia in resultado["evidencias"]:
        print(f"  - {evidencia['factor']}: {evidencia['detalle']} (+{evidencia['puntos']})")


def _api_responde():
    try:
        return requests.get(f"{ajustes.API_URL}/salud", timeout=2).status_code == 200
    except requests.RequestException:
        return False


def _levantar_api_local():
    """
    Si la API propia no está corriendo, la levanta en un hilo de este mismo programa
    (sólo si la URL configurada es local). Devuelve el servidor para apagarlo después,
    o None si ya había una API corriendo.
    """
    if _api_responde():
        return None

    anfitrion = urlparse(ajustes.API_URL).hostname
    if anfitrion not in ("127.0.0.1", "localhost"):
        raise cliente_api.ErrorApiPropia(f"No hay una API respondiendo en {ajustes.API_URL}.")

    # Si no hay claves de servidor definidas, se usa la del cliente (misma clave en las dos puntas).
    if not ajustes.API_KEYS_VALIDAS and ajustes.API_KEY_CLIENTE:
        ajustes.API_KEYS_VALIDAS = [ajustes.API_KEY_CLIENTE]

    import uvicorn
    puerto = urlparse(ajustes.API_URL).port or 8000
    servidor = uvicorn.Server(uvicorn.Config(
        "api_propia.servidor:app", host="127.0.0.1", port=puerto, log_level="warning"))
    threading.Thread(target=servidor.run, daemon=True).start()

    for _ in range(50):
        if _api_responde():
            return servidor
        time.sleep(0.1)
    raise cliente_api.ErrorApiPropia("No se pudo levantar la API local.")


def comando_ranking(args):
    servidor = _levantar_api_local()
    try:
        _hacer_ranking(args)
    finally:
        if servidor is not None:
            servidor.should_exit = True


def _hacer_ranking(args):
    adjudicatarios = obtener_adjudicatarios(args.fecha, args.limite)
    unicos = {adj["cuit"]: adj for adj in adjudicatarios}
    if not unicos:
        print("No hay adjudicatarios para evaluar.")
        return

    evaluados = []
    for cuit, adj in unicos.items():
        try:
            evaluacion = cliente_api.evaluar_proveedor(cuit)
        except cliente_api.ErrorApiPropia as error:
            print(f"{formatear_cuit(cuit)}: no se pudo evaluar ({error})")
            continue
        evaluados.append((evaluacion, adj))

    evaluados.sort(key=lambda par: par[0]["puntaje"], reverse=True)
    print(f"{'CUIT':<15}{'Estado':<20}{'Puntaje':>8}  Razón social")
    for evaluacion, adj in evaluados:
        print(f"{formatear_cuit(evaluacion['cuit']):<15}{evaluacion['estado']:<20}"
              f"{evaluacion['puntaje']:>8}  {adj['razon_social']}")


def comando_fuentes(_args):
    for fuente in describir_fuentes():
        print(f"{fuente['nombre']}: {fuente['url']}  ({fuente['dominio']} -> {fuente['ip']})")


def construir_parser():
    parser = argparse.ArgumentParser(description="Seguimiento de proveedores")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("servidor").set_defaults(funcion=comando_servidor)
    sub.add_parser("fuentes").set_defaults(funcion=comando_fuentes)

    p = sub.add_parser("inspeccionar")
    p.add_argument("--fecha", help="AAAAMMDD (por defecto, la edición vigente)")
    p.set_defaults(funcion=comando_inspeccionar)

    for nombre, funcion in (("scrapear", comando_scrapear), ("ranking", comando_ranking)):
        p = sub.add_parser(nombre)
        p.add_argument("--fecha", help="AAAAMMDD (por defecto, la edición vigente)")
        p.add_argument("--limite", type=int, default=10, help="máximo de avisos a leer")
        p.set_defaults(funcion=funcion)

    p = sub.add_parser("consultar")
    p.add_argument("cuit")
    p.set_defaults(funcion=comando_consultar)
    return parser


def main():
    args = construir_parser().parse_args()
    try:
        args.funcion(args)
    except (ErrorScraping, cliente_api.ErrorApiPropia) as error:
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
