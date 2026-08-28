# EcoLogistics — Carbon Tracker Service

Microservicio para el cálculo de emisiones de CO₂ generadas por el transporte de
mercancías, construido con **Python 3.12, FastAPI, Pydantic y Pytest**, siguiendo
Clean Code, SOLID, separación de responsabilidades y programación defensiva.

## Modelo de cálculo

```
emisiones_kg = factor_eficiencia × peso_carga(t) × distancia(km) × factor_emision
```

Modelo de consumo tonelada-kilómetro (alineado con GLEC Framework / ISO 14083).
Ver justificación completa, unidades y supuestos en
[`docs/BITACORA_PROMPTS.md`](docs/BITACORA_PROMPTS.md#fase-2--chain-of-thought-análisis-y-modelo-matemático).

## Estructura del proyecto

```
EcoLogistics_Microservice/
├── main.py                          # Entrypoint: uvicorn app.main:app
├── requirements.txt
├── app/
│   ├── main.py                      # App factory FastAPI + exception handlers
│   ├── api/routes/emissions.py      # Controlador: POST /emissions/calculate
│   ├── schemas/emissions.py         # DTOs Pydantic (Request/Response)
│   └── domain/
│       ├── vehicle_type.py          # VehicleType (Enum) + normalización
│       ├── exceptions.py            # Excepciones de negocio
│       └── emissions_calculator.py  # Fórmula de negocio (núcleo del servicio)
├── tests/                           # Suite Pytest (84 tests)
└── docs/
    ├── BITACORA_PROMPTS.md          # Historial de prompts y evolución del código
    └── REFLEXION_CRITICA.md         # Reflexión sobre desarrollo asistido por LLM
```

Arquitectura en capas (Presentación → Contratos/DTO → Dominio), con regla de
dependencia unidireccional: el dominio no conoce FastAPI ni Pydantic.

## Instalación y ejecución

```bash
python -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt

# Levantar el servicio
./.venv/Scripts/python main.py
# -> http://localhost:8000/docs (Swagger UI)

# Ejecutar la suite de pruebas
./.venv/Scripts/python -m pytest -v
```

## Ejemplo de uso

```bash
curl -X POST http://localhost:8000/emissions/calculate \
  -H "Content-Type: application/json" \
  -d '{
        "vehicle_type": "Diésel",
        "cargo_weight_tonnes": 5,
        "distance_km": 300,
        "efficiency_factor": 0.02,
        "emission_factor": 2.68
      }'
```

Respuesta esperada:

```json
{"vehicle_type": "Diésel", "emissions_kg": 80.4, "emissions_tonnes": 0.0804}
```

## Estado de la revisión de código

La revisión crítica de seguridad y rendimiento (fase 6, ver bitácora) dejó un
backlog de mejoras **aún no aplicado al código**, encabezado por la falta de
cota superior en `efficiency_factor`/`emission_factor` (riesgo de overflow a
`Infinity`). Ver el detalle completo en
[`docs/BITACORA_PROMPTS.md`](docs/BITACORA_PROMPTS.md#backlog-de-hallazgos-pendientes-de-corrección).

## Documentación del proceso

- [**Bitácora de Prompts**](docs/BITACORA_PROMPTS.md) — prompts principales y
  respuestas clave del LLM por cada fase del desarrollo, con evidencia de la
  evolución del código.
- [**Reflexión Crítica**](docs/REFLEXION_CRITICA.md) — ventajas y riesgos de
  usar LLMs en la construcción de este microservicio.
