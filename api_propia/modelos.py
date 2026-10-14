"""Modelos Pydantic: definen el contrato de entrada y salida de nuestra API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from proveedores.validaciones import limpiar_cuit, validar_cuit, es_persona_juridica


def normalizar_cuit(valor):
    """Valida un CUIT y devuelve solo sus 11 dígitos; lanza ValueError si no corresponde."""
    digitos = limpiar_cuit(valor)
    if not validar_cuit(digitos):
        raise ValueError("CUIT inválido: debe tener 11 dígitos y dígito verificador correcto.")
    if not es_persona_juridica(digitos):
        raise ValueError(
            "Solo se consultan personas jurídicas (CUIT que empiezan con 30, 33 o 34)."
        )
    return digitos


class ProveedorEntrada(BaseModel):
    cuit: str = Field(..., description="CUIT del proveedor, con o sin guiones.", examples=["30-50001091-2"])
    incidencias_internas: int = Field(0, ge=0, description="Incidencias registradas por la empresa.")
    cumplimiento_documental: float = Field(
        1.0, ge=0, le=1, description="Proporción de documentación entregada (0 a 1)."
    )

    @field_validator("cuit")
    @classmethod
    def validar_cuit_campo(cls, valor):
        return normalizar_cuit(valor)


class Evidencia(BaseModel):
    factor: str
    detalle: str
    puntos: float


class EvaluacionSalida(BaseModel):
    cuit: str
    denominacion: Optional[str] = None
    estado: str
    puntaje: float
    evidencias: List[Evidencia]
    encontrado_en_bcra: bool
    datos_bcra: Dict[str, Any]
    datos_cheques: Dict[str, Any]


class ConsultaBcraSalida(BaseModel):
    cuit: str
    deudas: Dict[str, Any]
    cheques: Dict[str, Any]
