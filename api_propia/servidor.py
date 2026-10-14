"""
API propia del proyecto (FastAPI).

Recibe un CUIT, consulta la API pública del BCRA (Central de Deudores) y devuelve
la situación del proveedor y su evaluación de riesgo. Requiere API key.

Para correrla:   python main.py servidor
Documentación interactiva (Swagger):   http://127.0.0.1:8000/docs
"""

from fastapi import Depends, FastAPI, HTTPException

from apis import bcra
from api_propia.modelos import (
    ConsultaBcraSalida, EvaluacionSalida, ProveedorEntrada, normalizar_cuit,
)
from api_propia.seguridad import verificar_api_key
from proveedores.servicio import evaluar_por_cuit

app = FastAPI(
    title="API de seguimiento de proveedores",
    description="Consulta la Central de Deudores del BCRA por CUIT y evalúa el riesgo del proveedor.",
    version="1.0.0",
)


@app.get("/salud")
def salud():
    """Chequeo de estado. Es público (no requiere API key)."""
    return {"estado": "ok"}


@app.get("/proveedores/{cuit}/bcra", response_model=ConsultaBcraSalida,
         dependencies=[Depends(verificar_api_key)])
def consultar_bcra(cuit: str):
    """Devuelve el resumen de deudas y cheques rechazados del BCRA para un CUIT."""
    try:
        cuit_limpio = normalizar_cuit(cuit)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    try:
        deudas = bcra.resumir_deudas(bcra.consultar_deudas(cuit_limpio))
        cheques = bcra.resumir_cheques(bcra.consultar_cheques_rechazados(cuit_limpio))
    except bcra.BcraNoEncontrado:
        raise HTTPException(status_code=404, detail="El BCRA no tiene datos para ese CUIT.")
    except bcra.BcraNoDisponible as error:
        raise HTTPException(status_code=502, detail=str(error))
    except bcra.BcraError as error:
        raise HTTPException(status_code=502, detail=str(error))

    return {"cuit": cuit_limpio, "deudas": deudas, "cheques": cheques}


@app.post("/proveedores/evaluar", response_model=EvaluacionSalida,
          dependencies=[Depends(verificar_api_key)])
def evaluar(proveedor: ProveedorEntrada):
    """
    Evalúa un proveedor: consulta el BCRA por su CUIT, le suma las evaluaciones
    internas que se envíen en el cuerpo y devuelve puntaje, estado y evidencias.
    """
    try:
        return evaluar_por_cuit(
            proveedor.cuit, proveedor.incidencias_internas, proveedor.cumplimiento_documental
        )
    except bcra.BcraNoDisponible as error:
        raise HTTPException(status_code=502, detail=str(error))
    except bcra.BcraError as error:
        raise HTTPException(status_code=502, detail=str(error))
