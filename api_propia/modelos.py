"""Modelos Pydantic: definen el contrato de entrada y salida de nuestra API."""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from config.ajustes import ESTADOS_DOCUMENTALES
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


class DocumentoEntrada(BaseModel):
    nombre: str = Field(..., description="Nombre del documento (ej. constancia de inscripción).")
    estado: str = Field("vigente", description=f"Uno de: {', '.join(ESTADOS_DOCUMENTALES)}.")
    vence: Optional[date] = Field(None, description="Fecha de vencimiento (AAAA-MM-DD), si tiene.")

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, valor):
        if valor not in ESTADOS_DOCUMENTALES:
            raise ValueError(f"Estado inválido. Opciones: {', '.join(ESTADOS_DOCUMENTALES)}")
        return valor


class ProveedorEntrada(BaseModel):
    cuit: str = Field(..., description="CUIT del proveedor, con o sin guiones.", examples=["30-50001091-2"])
    incidencias_internas: int = Field(0, ge=0, description="Incidencias registradas por la empresa.")
    cumplimiento_documental: float = Field(
        1.0, ge=0, le=1, description="Proporción de documentación entregada (0 a 1)."
    )
    documentos: Optional[List[DocumentoEntrada]] = Field(
        None,
        description="Documentos del proveedor. Si se envían, el cumplimiento y los vencimientos "
                    "se calculan a partir de ellos y reemplazan a cumplimiento_documental.",
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
    es_critico: bool = False
    documentos: Optional[Dict[str, Any]] = None
    datos_bcra: Dict[str, Any]
    datos_cheques: Dict[str, Any]


class ConsultaBcraSalida(BaseModel):
    cuit: str
    deudas: Dict[str, Any]
    cheques: Dict[str, Any]
