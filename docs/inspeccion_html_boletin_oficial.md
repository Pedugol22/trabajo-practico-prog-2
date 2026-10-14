# Inspección del HTML del Boletín Oficial (tercera sección)

Evidencia de la inspección hecha en el navegador (herramientas de desarrollador) los días
**13 y 14 de octubre de 2026**, antes de escribir el scraper.

## robots.txt
`https://www.boletinoficial.gob.ar/robots.txt` sólo restringe la **segunda sección**.
La tercera sección (contrataciones del Estado) no está restringida, por lo que se puede
descargar. Igualmente el programa lee el robots.txt antes de cada descarga
(`scraping/robots.py`) y deja una pausa de 2 segundos entre pedidos.

## URLs
| Qué | URL |
|---|---|
| Listado de la edición vigente | `/seccion/tercera` |
| Listado de un día | `/seccion/tercera/AAAAMMDD` |
| Detalle de un aviso | `/detalleAviso/tercera/<ID>/<AAAAMMDD>` |

## Estructura del listado
```
div#avisosSeccionDiv
  h5.seccion-rubro                       "ADJUDICACIONES - ADJUDICACIONES"
  a[href="/detalleAviso/tercera/<ID>/<AAAAMMDD>"]
    div.linea-aviso
      p.item                             organismo
      p.item-detalle > small             proceso (ej. Licitación Pública Nº ...)
```
El rubro aplica a todos los `a` que le siguen hasta el próximo `h5`.

## Estructura del detalle
- `#tituloDetalleAviso`: título del aviso.
- `#cuerpoDetalleAviso`: texto en párrafos (no hay tablas).

Patrón del texto de una adjudicación:
```
Expediente N°: EX-... Objeto: ... Texto del Aviso: Adjudicar a la Firma NOMBRE
CUIT NRO <11 dígitos sin guiones>, el renglón Nro: ...; por un total de PESOS ... ($ 999.999,99)
```
De ahí se extraen expediente, objeto, razón social, CUIT y monto (`proveedores/textos.py`).

## Limitaciones
- El sitio puede cambiar su HTML; si el scraper deja de encontrar avisos, hay que volver a inspeccionar.
- Los fixtures de `tests/fixtures/` son **sintéticos** (estructura real, datos inventados) y
  existen sólo para probar el parseo sin depender de internet.
