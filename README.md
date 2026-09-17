# Plataforma de evaluación y seguimiento de proveedores

**Solicitud de proyecto 3** — Programación 2, UADE.

Área de compras de una empresa privada, pública o ministerio. Objetivo:
unificar datos de proveedores, documentos publicados, APIs externas y
evaluaciones internas para priorizar seguimiento, alertas y reportes
ejecutivos.

## Alcance de esta entrega

Este avance cubre las necesidades funcionales **N01 a N13** del "alcance
funcional mínimo solicitado" (documento `proyecto`, Solicitud 3 de 6).
Quedan pendientes N14 a N25 (JSON/XML y métodos HTTP a fondo, ETL con
Pandas, visualización y automatización de correos), correspondientes a
etapas posteriores del cronograma de 4 meses.

## Cómo correrlo

```bash
pip install -r requirements.txt
python main.py
```

Para correr las pruebas:

```bash
python tests/test_scoring.py
```

> Nota sobre conexión a internet: `main.py` incluye dos pasos que
> requieren salir a internet de verdad (resolver IPs en `web_info` y
> consultar la API de tipo de cambio en `apis`). Si se ejecuta sin
> conexión, esas partes muestran un aviso en vez de romper el programa
> — el resto del flujo (evaluación de proveedores y scraping) funciona
> igual, porque usa datos y una página HTML de ejemplo incluidos en el
> proyecto.

## Estructura del proyecto

```
seguimiento_proveedores/
├── main.py                    → conecta todo el flujo de punta a punta
├── requirements.txt
├── proveedores/
│   ├── datos.py                → base de proveedores, ponderaciones
│   ├── validaciones.py         → limpiar razón social, validar CUIT
│   ├── textos.py                → expedientes y observaciones
│   └── scoring.py               → puntaje de riesgo y clasificación
├── web_info/
│   └── fuentes.py               → sitio, URL, DNS, IP
├── scraping/
│   ├── descargar.py             → requests: descarga HTML real
│   ├── parsear.py                → BeautifulSoup: arma el árbol HTML
│   ├── extractor.py              → texto y atributos de un elemento
│   ├── buscador.py               → find_all con filtros
│   └── pagina_ejemplo.py         → HTML de prueba para correr sin depender de un sitio real
├── apis/
│   └── tipo_cambio.py            → API pública de tipo de cambio
├── etl/          → reservado para la etapa de ETL/Pandas
├── reportes/     → reservado para reportes y gráficos
├── correo/       → reservado para el envío automático de correos
└── tests/
    └── test_scoring.py           → pruebas de las funciones principales
```

## Mapa de necesidades funcionales cubiertas

| # | Necesidad | Dónde está |
|---|---|---|
| N01 | Entorno y módulos | Esta misma estructura de carpetas |
| N02 | Operadores | `proveedores/scoring.py` → `calcular_puntaje_riesgo` |
| N03 | Estructuras de control | `proveedores/scoring.py` → `clasificar_proveedor` |
| N04 | Funciones | `proveedores/validaciones.py`, `proveedores/scoring.py` → `evaluar_proveedor` |
| N05 | Listas | `proveedores/datos.py` → `PROVEEDORES` |
| N06 | Diccionarios | `proveedores/datos.py` → `PONDERACIONES`, `ESTADOS_DOCUMENTALES` |
| N07 | Cadenas de caracteres | `proveedores/textos.py` |
| N08 | Web, DNS, IP | `web_info/fuentes.py` |
| N09 | Inspección de HTML | Ver sección "Pendiente de inspección real" abajo |
| N10 | Módulo de scraping | `scraping/descargar.py`, `scraping/parsear.py` |
| N11 | Texto y atributos | `scraping/extractor.py` |
| N12 | find_all con filtros | `scraping/buscador.py` |
| N13 | API pública | `apis/tipo_cambio.py` |

## Pendiente de inspección real (N09)

El scraping de este avance corre sobre `scraping/pagina_ejemplo.py`, una
página HTML de prueba armada a propósito con la misma estructura que se
espera de un sitio real (filas `<tr class="fila-proveedor">` con un
`<a data-estado="...">` adentro).

