"""
Autenticación de nuestra API mediante API key en el header X-API-Key (N17).

Las claves válidas se leen de la variable de entorno API_KEYS (ver .env.example),
así que no están escritas en el código fuente ni se suben a GitHub.
"""

import secrets
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from config import ajustes

# Declara el esquema de seguridad: Swagger (/docs) muestra el botón "Authorize" con un candado.
encabezado_api_key = APIKeyHeader(name="X-API-Key", auto_error=False)


def verificar_api_key(x_api_key: Optional[str] = Security(encabezado_api_key)):
    """Dependencia de FastAPI: corta el pedido con 401 si la clave falta o es inválida."""
    claves_validas = ajustes.API_KEYS_VALIDAS

    if not claves_validas:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servidor no tiene API keys configuradas (variable de entorno API_KEYS).",
        )

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el header X-API-Key.",
        )

    # compare_digest compara en tiempo constante, para no filtrar información por tiempos de respuesta
    if not any(secrets.compare_digest(x_api_key.encode(), clave.encode()) for clave in claves_validas):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida.",
        )
    return True
