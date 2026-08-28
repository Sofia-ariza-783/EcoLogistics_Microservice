"""API routes for CO2 emissions calculation."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.domain.emissions_calculator import EmissionCalculationInput, calculate_co2_emissions
from app.schemas.emissions import EmissionCalculationRequest, EmissionCalculationResponse

router = APIRouter(prefix="/emissions", tags=["emissions"])

_KG_PER_TONNE: float = 1000.0


@router.post(
    "/calculate",
    response_model=EmissionCalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calcula las emisiones de CO2 de un trayecto de transporte de carga",
)
def calculate_emissions(request: EmissionCalculationRequest) -> EmissionCalculationResponse:
    """Calculate CO2 emissions for a single cargo transport trip.

    Pydantic has already validated the request's shape and ranges. This
    handler only translates the request into a domain value object and
    delegates the calculation; any remaining business-rule violation is
    raised as an ``EmissionsDomainError`` subclass and handled globally
    (see ``app.main``), keeping this route free of error-mapping logic.
    """
    calculation_input = EmissionCalculationInput(
        vehicle_type=request.vehicle_type,
        cargo_weight_tonnes=request.cargo_weight_tonnes,
        distance_km=request.distance_km,
        efficiency_factor=request.efficiency_factor,
        emission_factor=request.emission_factor,
    )
    emissions_kg = calculate_co2_emissions(calculation_input)

    return EmissionCalculationResponse(
        vehicle_type=request.vehicle_type,
        emissions_kg=emissions_kg,
        emissions_tonnes=round(emissions_kg / _KG_PER_TONNE, 6),
    )
