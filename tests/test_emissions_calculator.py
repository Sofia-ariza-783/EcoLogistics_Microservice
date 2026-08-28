"""Tests for the core emissions calculation domain logic.

Cubre:
  - Ejemplos de uso (happy path) para cada tipo de vehículo.
  - Casos de borde de negocio: distancia = 0, peso de carga negativo,
    tipo de vehículo no soportado, valores no finitos (NaN/inf).
  - Que las excepciones lanzadas sean del tipo correcto y con un mensaje
    explicativo (no solo "algo falló").
"""

import math

import pytest

from app.domain.emissions_calculator import EmissionCalculationInput, calculate_co2_emissions
from app.domain.exceptions import InvalidEmissionInputError, InvalidVehicleTypeError
from app.domain.vehicle_type import VehicleType


def _build_input(**overrides: object) -> EmissionCalculationInput:
    defaults: dict[str, object] = {
        "vehicle_type": VehicleType.DIESEL,
        "cargo_weight_tonnes": 5.0,
        "distance_km": 300.0,
        "efficiency_factor": 0.02,
        "emission_factor": 2.68,
    }
    defaults.update(overrides)
    return EmissionCalculationInput(**defaults)  # type: ignore[arg-type]


class TestHappyPath:
    """Ejemplos de uso: cómo construir un cálculo válido y obtener el resultado."""

    def test_calculates_expected_emissions_for_diesel(self) -> None:
        """Ejemplo de uso — camión Diésel.

        Un camión Diésel transporta 5 toneladas de mercancía a lo largo de
        300 km. Su consumo específico es 0.02 L por tonelada-km y el diésel
        emite 2.68 kg de CO2 por litro quemado.
        """
        calculation_input = EmissionCalculationInput(
            vehicle_type=VehicleType.DIESEL,
            cargo_weight_tonnes=5.0,
            distance_km=300.0,
            efficiency_factor=0.02,
            emission_factor=2.68,
        )

        emissions_kg = calculate_co2_emissions(calculation_input)

        # 0.02 * 5 * 300 * 2.68 = 80.4
        assert emissions_kg == pytest.approx(80.4)

    def test_calculates_expected_emissions_for_electrico(self) -> None:
        """Ejemplo de uso — furgón Eléctrico.

        Mismo trayecto (5 t, 300 km) pero con un vehículo eléctrico: el
        factor de eficiencia se expresa en kWh/(t·km) y el factor de
        emisión en kgCO2/kWh (según la matriz energética de la red).
        """
        calculation_input = _build_input(
            vehicle_type=VehicleType.ELECTRICO,
            efficiency_factor=0.15,
            emission_factor=0.35,
        )

        emissions_kg = calculate_co2_emissions(calculation_input)

        # 0.15 * 5 * 300 * 0.35 = 78.75
        assert emissions_kg == pytest.approx(78.75)

    def test_calculates_expected_emissions_for_hibrido(self) -> None:
        """Ejemplo de uso — camión Híbrido.

        El Híbrido usa la misma fórmula que los demás tipos; sus factores
        ya representan el comportamiento combinado del vehículo.
        """
        calculation_input = _build_input(
            vehicle_type=VehicleType.HIBRIDO,
            efficiency_factor=0.012,
            emission_factor=1.4,
        )

        emissions_kg = calculate_co2_emissions(calculation_input)

        # 0.012 * 5 * 300 * 1.4 = 25.2
        assert emissions_kg == pytest.approx(25.2)

    def test_zero_emission_factor_yields_zero_emissions(self) -> None:
        calculation_input = _build_input(emission_factor=0.0)
        assert calculate_co2_emissions(calculation_input) == 0.0

    def test_result_is_rounded_to_fixed_precision(self) -> None:
        calculation_input = _build_input(
            cargo_weight_tonnes=1.0,
            distance_km=1.0,
            efficiency_factor=1.0 / 3.0,
            emission_factor=1.0,
        )
        result = calculate_co2_emissions(calculation_input)
        assert result == round(1.0 / 3.0, 4)


class TestVehicleTypeValidation:
    def test_rejects_non_vehicle_type_value(self) -> None:
        with pytest.raises(InvalidVehicleTypeError):
            _build_input(vehicle_type="Diésel")  # raw str, not the enum member

    def test_rejects_unsupported_vehicle_type_object(self) -> None:
        with pytest.raises(InvalidVehicleTypeError):
            _build_input(vehicle_type=None)


class TestNumericValidation:
    @pytest.mark.parametrize("field", ["cargo_weight_tonnes", "distance_km", "efficiency_factor"])
    @pytest.mark.parametrize("invalid_value", [0, -1, -0.001])
    def test_rejects_non_positive_required_fields(self, field: str, invalid_value: float) -> None:
        with pytest.raises(InvalidEmissionInputError):
            _build_input(**{field: invalid_value})

    def test_rejects_negative_emission_factor(self) -> None:
        with pytest.raises(InvalidEmissionInputError):
            _build_input(emission_factor=-0.5)

    @pytest.mark.parametrize(
        "field", ["cargo_weight_tonnes", "distance_km", "efficiency_factor", "emission_factor"]
    )
    def test_rejects_nan(self, field: str) -> None:
        with pytest.raises(InvalidEmissionInputError):
            _build_input(**{field: math.nan})

    @pytest.mark.parametrize(
        "field", ["cargo_weight_tonnes", "distance_km", "efficiency_factor", "emission_factor"]
    )
    def test_rejects_infinity(self, field: str) -> None:
        with pytest.raises(InvalidEmissionInputError):
            _build_input(**{field: math.inf})

    @pytest.mark.parametrize(
        "field", ["cargo_weight_tonnes", "distance_km", "efficiency_factor", "emission_factor"]
    )
    def test_rejects_non_numeric_type(self, field: str) -> None:
        with pytest.raises(InvalidEmissionInputError):
            _build_input(**{field: "not-a-number"})

    def test_rejects_none_for_required_numeric_field(self) -> None:
        with pytest.raises(InvalidEmissionInputError):
            _build_input(cargo_weight_tonnes=None)

    def test_rejects_boolean_masquerading_as_number(self) -> None:
        # bool is technically an int subclass in Python; must be explicitly rejected.
        with pytest.raises(InvalidEmissionInputError):
            _build_input(cargo_weight_tonnes=True)


class TestRequiredEdgeCases:
    """Casos de borde explícitamente solicitados para el dominio:

    1. Distancia recorrida igual a cero.
    2. Peso de carga negativo.
    3. Tipo de vehículo no soportado.

    Cada test verifica el TIPO de excepción y que el MENSAJE sea
    explicativo, no solo que "algo" haya fallado (programación defensiva
    verificable, no solo silenciosa).
    """

    def test_edge_case_zero_distance_is_rejected(self) -> None:
        with pytest.raises(InvalidEmissionInputError) as exc_info:
            _build_input(distance_km=0)

        assert exc_info.value.field_name == "distance_km"
        assert "mayor que cero" in str(exc_info.value)

    def test_edge_case_negative_cargo_weight_is_rejected(self) -> None:
        with pytest.raises(InvalidEmissionInputError) as exc_info:
            _build_input(cargo_weight_tonnes=-10.0)

        assert exc_info.value.field_name == "cargo_weight_tonnes"
        assert "mayor que cero" in str(exc_info.value)

    def test_edge_case_unsupported_vehicle_type_is_rejected(self) -> None:
        with pytest.raises(InvalidVehicleTypeError) as exc_info:
            _build_input(vehicle_type="Gasolina")

        assert "no soportado" in str(exc_info.value)


class TestImmutability:
    def test_calculation_input_is_frozen(self) -> None:
        calculation_input = _build_input()
        with pytest.raises(Exception):
            calculation_input.cargo_weight_tonnes = 999.0  # type: ignore[misc]
