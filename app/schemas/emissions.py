"""Pydantic request/response schemas for the emissions calculation API.

These schemas validate the *shape* of transport-level (JSON) input: types,
required fields, and sane numeric ranges. They are intentionally kept
separate from the domain layer's own invariant checks
(``app.domain.emissions_calculator``): the API may reject a request before
it ever reaches the domain, but the domain layer must remain safe even if
invoked from a non-HTTP caller that bypasses these schemas entirely.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.vehicle_type import VehicleType

# Generous, configurable sanity ceilings to catch obvious data-entry errors
# (e.g. a stray extra digit) without encoding a specific business policy.
_MAX_CARGO_WEIGHT_TONNES: float = 200.0
_MAX_DISTANCE_KM: float = 20_000.0
# efficiency_factor and emission_factor originally had no upper bound, which
# let astronomically large values overflow the calculation to `inf` (see
# EmissionsOverflowError). These ceilings are deliberately generous relative
# to any real-world value (e.g. diesel ~2.68 kgCO2/L, grid electricity well
# under 1.5 kgCO2/kWh) so they only ever catch orders-of-magnitude mistakes.
_MAX_EFFICIENCY_FACTOR: float = 10.0
_MAX_EMISSION_FACTOR: float = 50.0


class EmissionCalculationRequest(BaseModel):
    """Input payload for a single CO2 emissions calculation request."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    vehicle_type: VehicleType = Field(
        ...,
        description="Tipo de vehículo utilizado en el trayecto: Eléctrico, Diésel o Híbrido.",
    )
    cargo_weight_tonnes: float = Field(
        ...,
        gt=0,
        le=_MAX_CARGO_WEIGHT_TONNES,
        description="Peso de la carga transportada, en toneladas (t).",
    )
    distance_km: float = Field(
        ...,
        gt=0,
        le=_MAX_DISTANCE_KM,
        description="Distancia recorrida, en kilómetros (km).",
    )
    efficiency_factor: float = Field(
        ...,
        gt=0,
        le=_MAX_EFFICIENCY_FACTOR,
        description=(
            "Factor de eficiencia energética o de combustible del vehículo, "
            "en unidades de energía/combustible por tonelada-kilómetro "
            "(ej. L/(t·km) o kWh/(t·km))."
        ),
    )
    emission_factor: float = Field(
        ...,
        ge=0,
        le=_MAX_EMISSION_FACTOR,
        description=(
            "Factor de emisión asociado al tipo de vehículo, en kg de CO2 "
            "por unidad de energía/combustible consumida (ej. kgCO2/L, kgCO2/kWh)."
        ),
    )

    @field_validator("vehicle_type", mode="before")
    @classmethod
    def _normalize_vehicle_type(cls, value: object) -> VehicleType:
        """Accept minor casing/accent variations before strict enum validation."""
        try:
            return VehicleType.from_input(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator(
        "cargo_weight_tonnes",
        "distance_km",
        "efficiency_factor",
        "emission_factor",
        mode="before",
    )
    @classmethod
    def _reject_non_finite(cls, value: object) -> object:
        """Explicitly reject NaN/Infinity, which pass Pydantic's float type check."""
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("el valor debe ser numérico finito (no NaN ni infinito)")
        return value


class EmissionCalculationResponse(BaseModel):
    """Output payload with the calculated CO2 emissions for a trip."""

    vehicle_type: VehicleType = Field(..., description="Tipo de vehículo evaluado.")
    emissions_kg: float = Field(..., description="Emisiones totales de CO2, en kilogramos.")
    emissions_tonnes: float = Field(
        ..., description="Emisiones totales de CO2, en toneladas."
    )
