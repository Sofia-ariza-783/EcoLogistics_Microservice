"""Domain-specific exceptions for the Carbon Tracker service.

Kept free of any web-framework dependency (no FastAPI/Pydantic imports)
so the domain layer remains reusable outside an HTTP context (batch
jobs, other services, tests).
"""

from __future__ import annotations


class EmissionsDomainError(Exception):
    """Base class for all business-rule violations in the emissions domain."""


class InvalidVehicleTypeError(EmissionsDomainError):
    """Raised when the provided vehicle type is not a supported VehicleType."""

    def __init__(self, value: object) -> None:
        self.value = value
        super().__init__(f"Tipo de vehículo no soportado: {value!r}")


class InvalidEmissionInputError(EmissionsDomainError):
    """Raised when a numeric emissions input violates a domain business rule."""

    def __init__(self, field_name: str, value: object, reason: str) -> None:
        self.field_name = field_name
        self.value = value
        self.reason = reason
        super().__init__(f"Campo '{field_name}' inválido ({value!r}): {reason}")


class EmissionsOverflowError(EmissionsDomainError):
    """Raised when a (validated, finite) combination of inputs still produces
    a non-finite result (overflow to +/- infinity).

    Each individual field can pass ``InvalidEmissionInputError`` checks (be
    positive and finite) and yet, multiplied together, exceed the range a
    float can represent. This guard protects the domain regardless of the
    caller, independently of any upper bound enforced upstream (e.g. by the
    API schema).
    """

    def __init__(self) -> None:
        super().__init__(
            "El cálculo produjo un resultado no finito (overflow). "
            "Revise la magnitud de los factores de entrada."
        )
