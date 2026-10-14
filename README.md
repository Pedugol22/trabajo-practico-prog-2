# Plataforma de evaluación y seguimiento de proveedores

Trabajo práctico – Programación 2 (UADE) – Solicitud de proyecto 3.

El sistema usa **datos reales**:

1. **Web scraping real** (requests + BeautifulSoup) de la tercera sección del
   [Boletín Oficial](https://www.boletinoficial.gob.ar): se leen las *adjudicaciones* del Estado y se
   obtienen razón social, CUIT, monto, organismo y expediente de cada empresa adjudicada.
2. **API propia con autenticación** (FastAPI, header `X-API-Key`). Dado el CUIT de un proveedor, nuestra API
   llama a la **API pública del Banco Central (Central de Deudores)** y devuelve su situación crediticia
   y una evaluación de riesgo con evidencias.

```
Boletín Oficial ──scraping──▶ CUIT + razón social ──▶ nuestra API (X-API-Key) ──▶ API del BCRA
                                                              │
                                                              └─▶ puntaje, estado y evidencias
```

## Estructura

| Carpeta | Contenido |
|---|---|
| `config/` | Configuración leída de variables de entorno (`.env`) |
| `scraping/` | robots.txt, descarga, parseo con BeautifulSoup, filtros, Boletín Oficial |
| `apis/` | Cliente del BCRA, cliente de nuestra API, API de tipo de cambio (práctica) |
| `api_propia/` | Servidor FastAPI: autenticación, modelos Pydantic, endpoints |
| `proveedores/` | Validación de CUIT, procesamiento de textos, scoring de riesgo, servicio |
| `web_info/` | Fuentes web usadas, dominio e IP |
| `tests/` | 42 pruebas con `unittest` (fixtures sintéticos y BCRA simulado) |
| `docs/` | Evidencia de la inspección del HTML |
| `etl/`, `reportes/`, `correo/` | Reservadas para las etapas siguientes (Pandas, reportes, correo) |

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # Linux/Mac: cp .env.example .env
```

Editar `.env` y poner una clave inventada por vos (se repite en las dos variables):

```
API_KEYS=mi-clave-secreta
PROVEEDORES_API_KEY=mi-clave-secreta
```

El archivo `.env` está en `.gitignore`: **nunca se sube a GitHub**.

## Uso

```bash
python main.py servidor                # terminal 1: levanta la API en http://127.0.0.1:8000
python main.py fuentes                 # fuentes web usadas y su IP
python main.py scrapear --limite 5     # scraping real del Boletín Oficial
python main.py consultar 30711111111   # terminal 2: evalúa un CUIT (nuestra API → BCRA)
python main.py ranking --limite 5      # TODO JUNTO en un comando: scrapea, levanta la API sola y ordena por riesgo
python -m unittest discover -s tests -t .
```

Documentación interactiva de la API (Swagger): <http://127.0.0.1:8000/docs>
(botón *Authorize* → ingresar la clave).

### Usar la API con curl

```bash
curl http://127.0.0.1:8000/salud
curl -H "X-API-Key: mi-clave-secreta" http://127.0.0.1:8000/proveedores/30711111111/bcra
curl -X POST http://127.0.0.1:8000/proveedores/evaluar \
     -H "X-API-Key: mi-clave-secreta" -H "Content-Type: application/json" \
     -d '{"cuit": "30711111111", "incidencias_internas": 0, "cumplimiento_documental": 1.0}'
```

| Endpoint | Método | Auth | Respuestas |
|---|---|---|---|
| `/salud` | GET | no | 200 |
| `/proveedores/{cuit}/bcra` | GET | sí | 200, 401, 404 (sin datos en BCRA), 422 (CUIT inválido), 502 (BCRA caído) |
| `/proveedores/evaluar` | POST | sí | 200, 401, 422, 502 |

## Cómo se evalúa un proveedor

`proveedores/scoring.py` suma puntos de riesgo según lo que informa el BCRA (situación 1–5, días de atraso,
cheques rechazados, multas impagas, proceso judicial, situación jurídica, irrecuperable por disposición
técnica, en revisión, refinanciaciones) y datos internos (incidencias, cumplimiento documental).
La respuesta incluye la lista de **evidencias** (qué factor sumó cuántos puntos), así que cada estado es explicable:

`habilitado` → `observado` → `requiere revisión` → `suspendido`

Los pesos y umbrales están en los diccionarios `PONDERACIONES` y `UMBRALES`.

## Decisiones importantes

- **API pública vs. privada.** La API del BCRA es pública: no pide autenticación, sólo limita tráfico por IP.
  La autenticación está en **nuestra** API (API key en el header `X-API-Key`, guardada en variables de
  entorno, comparada con `secrets.compare_digest`).
- **Métodos HTTP.** Se usa GET para consultar y POST para enviar datos a evaluar. PUT/PATCH/DELETE no se
  usan porque la API no guarda datos; serían los métodos para reemplazar, modificar parcialmente o borrar un proveedor.
- **Privacidad.** Sólo se evalúan **personas jurídicas** (CUIT que empieza con 30, 33 o 34). Los CUIT de
  personas humanas (20, 23, 24, 27) se rechazan, para no cruzar datos crediticios de personas físicas.
- **Buenas prácticas de scraping.** Se lee `robots.txt`, se usa un User-Agent que identifica el proyecto,
  timeout, manejo de errores y pausa de 2 segundos entre pedidos.
- **CUIT.** Se valida largo y dígito verificador (módulo 11) antes de consultar.

## Qué se probó y qué no

- Los tests usan HTML sintético (con la estructura real del Boletín) y respuestas simuladas del BCRA, por lo
  que no dependen de internet.
- Los selectores del Boletín se verificaron inspeccionando el sitio real el 13 y 14/10/2026
  (ver `docs/inspeccion_html_boletin_oficial.md`).
- Si el BCRA da error de certificado SSL, actualizar `certifi` (`pip install --upgrade certifi`) o apuntar
  `BCRA_CA_BUNDLE` a un bundle de certificados. No se debe desactivar la verificación.
- El Boletín puede cambiar su HTML con el tiempo; en ese caso hay que ajustar `scraping/parsear.py`.
