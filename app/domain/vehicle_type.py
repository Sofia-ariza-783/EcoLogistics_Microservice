"""Vehicle type taxonomy for the Carbon Tracker domain."""

from __future__ import annotations

import unicodedata
from enum import Enum

# The longest real member value ("Eléctrico"/"Híbrido") is under 10 chars;
# 50 is a generous ceiling to reject pathological inputs (e.g. a multi-MB
# string) before spending CPU on Unicode normalization.
_MAX_INPUT_LENGTH: int = 50


class VehicleType(str, Enum):
    """Supported vehicle types for cargo transport emissions calculation.

    Each member shares the same calculation formula; only the numeric
    factors (efficiency, emission) associated with a given trip differ
    per type. Adding a new vehicle type never requires touching the
    calculation logic (Open/Closed Principle).
    """

    ELECTRICO = "Eléctrico"
    DIESEL = "Diésel"
    HIBRIDO = "Híbrido"

    @classmethod
    def from_input(cls, raw_value: object) -> "VehicleType":
        """Resolve a loosely-formatted user input into a canonical VehicleType.

        Tolerates variations in case, surrounding whitespace, and accent
        marks (e.g. "electrico", " ELECTRICO ", "Eléctrico") so that minor
        upstream data-entry inconsistencies do not cause spurious failures.

        Args:
            raw_value: the value received from an external caller (API
                payload, batch import, etc). May already be a VehicleType.

        Returns:
            The matching VehicleType member.

        Raises:
            ValueError: if raw_value cannot be matched to any supported
                vehicle type.
        """
        if isinstance(raw_value, cls):
            return raw_value

        if not isinstance(raw_value, str) or not raw_value.strip():
            raise ValueError(f"Tipo de vehículo inválido: {raw_value!r}")

        if len(raw_value) > _MAX_INPUT_LENGTH:
            raise ValueError(
                f"Tipo de vehículo inválido: excede la longitud máxima de "
                f"{_MAX_INPUT_LENGTH} caracteres."
            )

        normalized = _strip_accents(raw_value).strip().casefold()
        for member in cls:
            if _strip_accents(member.value).casefold() == normalized:
                return member

        supported = ", ".join(member.value for member in cls)
        raise ValueError(
            f"Tipo de vehículo no soportado: {raw_value!r}. "
            f"Valores permitidos: {supported}."
        )


def _strip_accents(value: str) -> str:
    """Remove diacritics (accents) from a string for case/accent-insensitive matching."""
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
