"""
Configuración central del proyecto.

Las credenciales (API keys) NUNCA van escritas en el código: se leen de
variables de entorno o de un archivo .env que no se sube a GitHub
(ver .env.example y .gitignore).
"""

import os
import re
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv es opcional: sin él se usan solo variables de entorno
    pass


def _lista_desde_env(nombre):
    """Lee una variable de entorno con valores separados por coma y devuelve una lista limpia."""
    valor = os.environ.get(nombre, "")
    return [item.strip() for item in valor.split(",") if item.strip()]


# --- Parámetros HTTP (diccionario) ------------------------------------
PARAMETROS_HTTP = {
    "timeout": 15,
    "user_agent": "TP-UADE-Programacion2 (seguimiento de proveedores; uso academico)",
    "pausa_entre_pedidos": 2.0,   # segundos entre pedidos al mismo sitio
}

# --- Fuentes externas -------------------------------------------------
FUENTES = {
    "boletin_oficial": "https://www.boletinoficial.gob.ar",
    "bcra_deudores": "https://api.bcra.gob.ar/CentralDeDeudores/v1.0",
}

# --- Listas de control (N05) --------------------------------------------
# Dominios desde los que el scraper tiene permitido descargar: se derivan de las fuentes reales.
DOMINIOS_PERMITIDOS = sorted({urlparse(url).hostname for url in FUENTES.values()})

# CUIT de proveedores críticos para la organización (se cargan desde el entorno, sin guiones).
# A un proveedor crítico se le aplica un criterio más estricto en la evaluación.
PROVEEDORES_CRITICOS = [re.sub(r"\D", "", cuit) for cuit in _lista_desde_env("PROVEEDORES_CRITICOS")]

# --- Estados documentales (N06) ------------------------------------------
# Cuánto aporta al cumplimiento documental cada estado de un documento (1 = cumple del todo).
ESTADOS_DOCUMENTALES = {
    "vigente": 1.0,
    "por_vencer": 0.5,
    "vencido": 0.0,
    "faltante": 0.0,
}

# --- Scraping: se puede desactivar por configuración -------------------
SCRAPING_HABILITADO = os.environ.get("SCRAPING_HABILITADO", "true").strip().lower() != "false"

# --- Credenciales (siempre desde el entorno) ---------------------------
# Claves que acepta NUESTRA API (se mandan en el header X-API-Key).
API_KEYS_VALIDAS = _lista_desde_env("API_KEYS")

# Clave que usa el cliente (main.py ranking / consultar) para llamar a nuestra API.
API_KEY_CLIENTE = os.environ.get("PROVEEDORES_API_KEY", "")

# Dirección donde corre nuestra API.
API_URL = os.environ.get("PROVEEDORES_API_URL", "http://127.0.0.1:8000")

# Ruta opcional a un certificado CA propio si el BCRA da error de SSL en tu red.
# Si no se define, se usa la verificación normal de certificados.
BCRA_CA_BUNDLE = os.environ.get("BCRA_CA_BUNDLE") or True

# Destinatarios del comité (para la etapa de correo, más adelante).
DESTINATARIOS_COMITE = _lista_desde_env("COMITE_EMAILS")
