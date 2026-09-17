"""
Pagina HTML de ejemplo para probar el scraper sin depender de un sitio
real todavia no inspeccionado. En la entrega final se reemplaza por el
HTML que devuelva descargar_html() sobre la URL definitiva.
"""

HTML_EJEMPLO = """
<html>
  <head><title>Licitaciones vigentes</title></head>
  <body>
    <h1>Listado de proveedores</h1>
    <table>
      <tr>
        <th>Expediente</th>
        <th>Proveedor</th>
      </tr>
      <tr class="fila-proveedor" data-estado="vigente">
        <td>Expediente: EXP-2024-00123 - Estado: en revision</td>
        <td><a href="/detalle/123" data-estado="vigente">Proveedor Sur S.A.</a></td>
      </tr>
      <tr class="fila-proveedor" data-estado="observado">
        <td>Expediente: EXP-2024-00456 - Estado: observado</td>
        <td><a href="/detalle/456" data-estado="observado">Insumos Norte SRL</a></td>
      </tr>
      <tr class="fila-proveedor" data-estado="suspendido">
        <td>Expediente: EXP-2024-00789 - Estado: suspendido</td>
        <td><a href="/detalle/789" data-estado="suspendido">Logistica del Plata</a></td>
      </tr>
    </table>
  </body>
</html>
"""
