"""Integration tests for the emissions calculation API endpoint.

Cubre:
  - Ejemplo de uso end-to-end del endpoint (request -> response real vía
    FastAPI TestClient, sin mocks del framework).
  - Casos de borde de negocio a nivel HTTP: distancia = 0, carga negativa,
    tipo de vehículo no soportado -> deben responder 422 con un detalle
    explicativo, nunca un 500 ni un fallo silencioso.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "vehicle_type": "Diésel",
    "cargo_weight_tonnes": 5.0,
    "distance_km": 300.0,
    "efficiency_factor": 0.02,
    "emission_factor": 2.68,
}


def test_usage_example_calculate_emissions_end_to_end() -> None:
    """Ejemplo de uso: cliente HTTP solicita el cálculo de un trayecto real.

    Camión Diésel, 5 toneladas de carga, 300 km recorridos.
    Se espera 200 OK con las emisiones en kg y en toneladas.
    """
    response = client.post("/emissions/calculate", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["vehicle_type"] == "Diésel"
    assert body["emissions_kg"] == pytest.approx(80.4)
    assert body["emissions_tonnes"] == pytest.approx(0.0804)


def test_calculate_emissions_normalizes_vehicle_type_input() -> None:
    payload = {**VALID_PAYLOAD, "vehicle_type": "diesel"}
    response = client.post("/emissions/calculate", json=payload)

    assert response.status_code == 200
    assert response.json()["vehicle_type"] == "Diésel"


def test_calculate_emissions_rejects_unsupported_vehicle_type() -> None:
    payload = {**VALID_PAYLOAD, "vehicle_type": "Gasolina"}
    response = client.post("/emissions/calculate", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field,value",
    [
        ("cargo_weight_tonnes", -5.0),
        ("distance_km", 0),
        ("efficiency_factor", -0.01),
        ("emission_factor", -1.0),
    ],
)
def test_calculate_emissions_rejects_invalid_numeric_values(field: str, value: float) -> None:
    payload = {**VALID_PAYLOAD, field: value}
    response = client.post("/emissions/calculate", json=payload)

    assert response.status_code == 422


def test_calculate_emissions_rejects_missing_field() -> None:
    payload = dict(VALID_PAYLOAD)
    del payload["cargo_weight_tonnes"]
    response = client.post("/emissions/calculate", json=payload)

    assert response.status_code == 422


def test_calculate_emissions_rejects_null_field() -> None:
    payload = {**VALID_PAYLOAD, "distance_km": None}
    response = client.post("/emissions/calculate", json=payload)

    assert response.status_code == 422


class TestRequiredEdgeCases:
    """Casos de borde explícitamente solicitados, verificados a nivel HTTP:

    1. Distancia recorrida igual a cero.
    2. Peso de carga negativo.
    3. Tipo de vehículo no soportado.

    Nota de diseño: estos tres valores son rechazados por Pydantic
    (``Field(gt=0)`` / el validador de ``vehicle_type``) antes de llegar al
    dominio, por lo que devuelven 422 con el formato de error estándar de
    FastAPI. La capa de dominio se prueba de forma independiente en
    ``test_emissions_calculator.py`` para garantizar que, aunque algo
    invocara el dominio sin pasar por la API, seguiría estando protegido.
    """

    def test_edge_case_zero_distance_returns_422(self) -> None:
        payload = {**VALID_PAYLOAD, "distance_km": 0}

        response = client.post("/emissions/calculate", json=payload)

        assert response.status_code == 422
        assert "distance_km" in response.text

    def test_edge_case_negative_cargo_weight_returns_422(self) -> None:
        payload = {**VALID_PAYLOAD, "cargo_weight_tonnes": -10.0}

        response = client.post("/emissions/calculate", json=payload)

        assert response.status_code == 422
        assert "cargo_weight_tonnes" in response.text

    def test_edge_case_unsupported_vehicle_type_returns_422(self) -> None:
        payload = {**VALID_PAYLOAD, "vehicle_type": "Gasolina"}

        response = client.post("/emissions/calculate", json=payload)

        assert response.status_code == 422
        assert "no soportado" in response.text

    def test_edge_case_never_returns_500_for_invalid_business_input(self) -> None:
        """Ninguno de los tres casos de borde debe degradar a un 500: son
        errores de validación esperados, no fallos internos inesperados."""
        invalid_payloads = [
            {**VALID_PAYLOAD, "distance_km": 0},
            {**VALID_PAYLOAD, "cargo_weight_tonnes": -10.0},
            {**VALID_PAYLOAD, "vehicle_type": "Gasolina"},
        ]

        for payload in invalid_payloads:
            response = client.post("/emissions/calculate", json=payload)
            assert response.status_code != 500


def test_calculate_emissions_allows_zero_emission_factor() -> None:
    payload = {**VALID_PAYLOAD, "emission_factor": 0.0}
    response = client.post("/emissions/calculate", json=payload)

    assert response.status_code == 200
    assert response.json()["emissions_kg"] == 0.0
