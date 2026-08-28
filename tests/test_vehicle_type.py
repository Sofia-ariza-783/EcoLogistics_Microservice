"""Tests for VehicleType parsing and normalization."""

import pytest

from app.domain.vehicle_type import VehicleType


@pytest.mark.parametrize(
    "raw_value",
    ["Eléctrico", "electrico", "ELECTRICO", " Eléctrico ", "eléctrico"],
)
def test_from_input_normalizes_electrico_variants(raw_value: str) -> None:
    assert VehicleType.from_input(raw_value) is VehicleType.ELECTRICO


@pytest.mark.parametrize(
    "raw_value",
    ["Diésel", "diesel", "DIESEL", "Diesel"],
)
def test_from_input_normalizes_diesel_variants(raw_value: str) -> None:
    assert VehicleType.from_input(raw_value) is VehicleType.DIESEL


@pytest.mark.parametrize(
    "raw_value",
    ["Híbrido", "hibrido", "HIBRIDO"],
)
def test_from_input_normalizes_hibrido_variants(raw_value: str) -> None:
    assert VehicleType.from_input(raw_value) is VehicleType.HIBRIDO


def test_from_input_returns_same_instance_if_already_vehicle_type() -> None:
    assert VehicleType.from_input(VehicleType.DIESEL) is VehicleType.DIESEL


@pytest.mark.parametrize("raw_value", ["Gas Natural", "", "   ", None, 123, 3.14])
def test_from_input_rejects_unsupported_values(raw_value: object) -> None:
    with pytest.raises(ValueError):
        VehicleType.from_input(raw_value)
