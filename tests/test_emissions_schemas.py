"""Tests for the Pydantic request/response schemas."""

import math

import pytest
from pydantic import ValidationError

from app.domain.vehicle_type import VehicleType
from app.schemas.emissions import EmissionCalculationRequest

VALID_PAYLOAD = {
    "vehicle_type": "Diésel",
    "cargo_weight_tonnes": 5.0,
    "distance_km": 300.0,
    "efficiency_factor": 0.02,
    "emission_factor": 2.68,
}


def test_accepts_valid_payload() -> None:
    request = EmissionCalculationRequest(**VALID_PAYLOAD)
    assert request.vehicle_type is VehicleType.DIESEL


def test_normalizes_vehicle_type_casing_and_accents() -> None:
    payload = {**VALID_PAYLOAD, "vehicle_type": "diesel"}
    request = EmissionCalculationRequest(**payload)
    assert request.vehicle_type is VehicleType.DIESEL


def test_rejects_unsupported_vehicle_type() -> None:
    payload = {**VALID_PAYLOAD, "vehicle_type": "Gasolina"}
    with pytest.raises(ValidationError):
        EmissionCalculationRequest(**payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("cargo_weight_tonnes", 0),
        ("cargo_weight_tonnes", -1),
        ("distance_km", 0),
        ("distance_km", -1),
        ("efficiency_factor", 0),
        ("efficiency_factor", -0.5),
        ("emission_factor", -0.1),
    ],
)
def test_rejects_out_of_range_numeric_fields(field: str, value: float) -> None:
    payload = {**VALID_PAYLOAD, field: value}
    with pytest.raises(ValidationError):
        EmissionCalculationRequest(**payload)


def test_allows_zero_emission_factor() -> None:
    payload = {**VALID_PAYLOAD, "emission_factor": 0.0}
    request = EmissionCalculationRequest(**payload)
    assert request.emission_factor == 0.0


@pytest.mark.parametrize(
    "field,value", [("cargo_weight_tonnes", math.nan), ("distance_km", math.inf)]
)
def test_rejects_non_finite_numeric_fields(field: str, value: float) -> None:
    payload = {**VALID_PAYLOAD, field: value}
    with pytest.raises(ValidationError):
        EmissionCalculationRequest(**payload)


def test_rejects_missing_required_field() -> None:
    payload = dict(VALID_PAYLOAD)
    del payload["distance_km"]
    with pytest.raises(ValidationError):
        EmissionCalculationRequest(**payload)


def test_rejects_unexpected_extra_field() -> None:
    payload = {**VALID_PAYLOAD, "unexpected_field": "should not be here"}
    with pytest.raises(ValidationError):
        EmissionCalculationRequest(**payload)


def test_rejects_wrong_type_for_numeric_field() -> None:
    payload = {**VALID_PAYLOAD, "distance_km": "trescientos"}
    with pytest.raises(ValidationError):
        EmissionCalculationRequest(**payload)
