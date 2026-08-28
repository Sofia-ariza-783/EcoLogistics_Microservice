# EcoLogistics — Carbon Tracker Service

Microservicio para el cálculo de emisiones de CO₂ generadas por el transporte de
mercancías, construido con **Python 3.12, FastAPI, Pydantic y Pytest**, siguiendo
Clean Code, SOLID, separación de responsabilidades y programación defensiva.

## Índice

1. [Modelo de cálculo](#modelo-de-cálculo)
2. [Estructura del proyecto](#estructura-del-proyecto)
3. [Instalación y ejecución](#instalación-y-ejecución)
4. [Ejemplo de uso](#ejemplo-de-uso)
5. [Estado de la revisión de código](#estado-de-la-revisión-de-código)
6. [Bitácora de Prompts](#bitácora-de-prompts)
7. [Reflexión Crítica](#reflexión-crítica)

---

## Modelo de cálculo

```
emisiones_kg = factor_eficiencia × peso_carga(t) × distancia(km) × factor_emision
```

Modelo de consumo tonelada-kilómetro (alineado con GLEC Framework / ISO 14083).
Justificación completa, unidades y supuestos en la
[Fase 2 de la Bitácora](#fase-2--chain-of-thought-análisis-y-modelo-matemático).

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
    ├── BITACORA_PROMPTS.md          # Fuente completa de la bitácora (ver abajo)
    └── REFLEXION_CRITICA.md         # Fuente completa de la reflexión (ver abajo)
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

La revisión crítica de seguridad y rendimiento (Fase 6 de la bitácora)
detectó 7 hallazgos. Los que eran defectos reales del microservicio o
mejoras de bajo riesgo se corrigieron como refinamiento post-revisión
(90 tests en verde); los que eran decisiones de infraestructura/despliegue o
de tooling de dependencias quedaron fuera de alcance a petición explícita.
Detalle completo en
[Fase 6 — Refinamiento Post-Revisión](#fase-6--revisión-de-código-seguridad-y-rendimiento).

| ID | Hallazgo | Estado |
|---|---|---|
| S1 | Sin cota superior en `efficiency_factor`/`emission_factor` (riesgo de `Infinity` en la respuesta) | ✅ Corregido |
| S2 | Sin `max_length` en el string crudo de `vehicle_type` antes de normalizar | ✅ Corregido |
| P1 | Endpoint síncrono sin I/O real (candidato a `async def`) | ✅ Corregido |
| S3 | Sin límite de tamaño de body a nivel de aplicación/ASGI | Pendiente (decisión de despliegue, fuera de alcance) |
| S4 | `requirements.txt` sin lockfile con hashes | Pendiente (fuera de alcance) |
| S5 | Sin auth/rate-limiting documentado como decisión explícita | Pendiente (decisión de despliegue, fuera de alcance) |
| P3 | `logging.basicConfig()` no configurable por entorno | Pendiente (fuera de alcance) |

---

## Bitácora de Prompts

Registro de los prompts principales utilizados durante el desarrollo, junto
con las respuestas clave que evidencian la evolución del código desde el
análisis inicial hasta la versión final revisada. Fuente completa también en
[`docs/BITACORA_PROMPTS.md`](docs/PROMPT_LOG.md).

<details>
<summary><strong>Fase 1 — Definición del Contexto</strong></summary>

**Prompt principal (resumen):**
> "Eres un Desarrollador Senior y Arquitecto de Software especializado en
> microservicios y soluciones sostenibles para logística. Desarrolla el
> Microservicio de Cálculo de Huella de Carbono para EcoLogistics usando
> Python 3.12, FastAPI, Pydantic y Pytest, siguiendo Clean Code, SOLID,
> separación de responsabilidades y programación defensiva. No ejecutes
> ninguna acción todavía, esto es solo contexto."

**Respuesta clave del LLM:** confirmó rol, stack y principios de diseño como
estándar del proyecto, y se abstuvo deliberadamente de generar código,
a la espera de instrucciones concretas.

**Evolución:** ninguna todavía — fase de encuadre. Este contrato de
principios es el criterio contra el que se evalúa todo el código posterior.

</details>

<details>
<summary><strong>Fase 2 — Chain-of-Thought (Análisis y Modelo Matemático)</strong></summary>

**Prompt principal (resumen):**
> "El microservicio debe calcular las emisiones de CO₂ considerando tipo de
> vehículo, peso de la carga, distancia, factor de eficiencia y factor de
> emisión. Antes de generar código, aplica Chain-of-Thought: identifica
> variables, restricciones, validaciones, casos límite y supuestos; define el
> modelo matemático explicando unidades y fórmula, justificando cada
> decisión, antes de escribir una sola línea de código."

**Respuesta clave del LLM:**
- Variables de entrada/salida con unidades explícitas.
- Reglas de negocio, validaciones defensivas, casos límite y 5 supuestos
  explícitos (A1–A5).
- Ante una ambigüedad real entre dos modelos matemáticos plausibles, el LLM
  **no asumió unilateralmente**: usó una pregunta estructurada al usuario
  para decidir, presentando ambas fórmulas con ejemplo numérico.

**Decisión validada:**
```
Emisiones_CO2 (kg) = factor_eficiencia × peso_carga(t) × distancia(km) × factor_emision
```
Híbrido con factores efectivos únicos (sin mezcla ponderada).

**Evolución:** esta fórmula, validada antes de codificar, es exactamente la
implementada después en `calculate_co2_emissions`. No hubo retrabajo
posterior sobre la semántica de negocio.

</details>

<details>
<summary><strong>Fase 3 — Desarrollo del Microservicio (Iterative Refinement)</strong></summary>

**Prompt principal (resumen):**
> "Implementa la función principal de cálculo, generando los modelos
> Pydantic y la lógica de negocio. Código documentado, tipado estático, apto
> para producción. Luego aplica Iterative Refinement: mejora sucesivamente el
> manejo de errores y la validación hasta obtener una versión robusta."

**Respuesta clave del LLM — 3 iteraciones reales sobre
`app/domain/emissions_calculator.py`:**

| Iteración | Cambio principal |
|---|---|
| v1 | `@dataclass` mutable, solo la fórmula, cero validación |
| v2 | Excepciones de dominio; validación de finitud, positividad estricta y no-negatividad |
| v3 | Inmutabilidad (`frozen=True, slots=True`), redondeo controlado, logging estructurado, docstrings completos |

También se generaron `vehicle_type.py`, `exceptions.py`, `schemas/emissions.py`,
`api/routes/emissions.py` y `app/main.py` (exception handlers globales).

**Evolución:** de una función de 6 líneas sin defensas a un value object
inmutable con invariantes garantizados en construcción.

</details>

<details>
<summary><strong>Fase 4 — Modularización (Arquitectura en Capas)</strong></summary>

**Prompt principal (resumen):**
> "Diseña la arquitectura separando lógica de negocio de los controladores
> REST: componentes, modelos de datos, responsabilidades por capa, estructura
> de carpetas y un diagrama textual de interacción entre capas."

**Respuesta clave del LLM:** 3 capas (Presentación, Contratos/DTOs, Dominio)
con regla de dependencia unidireccional, diagrama ASCII del flujo
request→dominio→response (incluyendo camino de error), y distinción explícita
entre `EmissionCalculationRequest` (DTO) y `EmissionCalculationInput`
(dominio) como frontera deliberada.

**Evolución:** esta fase no generó cambios de código — confirmó que la
estructura ya creada en la Fase 3 satisfacía el diseño propuesto.

</details>

<details>
<summary><strong>Fase 5 — Generación de Pruebas</strong></summary>

**Prompt principal (resumen):**
> "Genera con Pytest una suite de pruebas unitarias para la función principal
> y los endpoints, incluyendo ejemplos de uso. Cubre casos de borde:
> distancia = 0, carga negativa, tipos de vehículo no soportados."

**Respuesta clave del LLM:** enriqueció la suite existente (sin duplicar):
`TestHappyPath` con docstrings narrativos como ejemplos de uso, y
`TestRequiredEdgeCases` (dominio y API) verificando tipo de excepción y
contenido del mensaje, más una prueba de que ningún caso de borde degrada a
un error 500.

**Evolución:** de 77 a 84 tests, con trazabilidad 1:1 entre cada caso de
borde nombrado y un test identificable por su nombre.

</details>

<details>
<summary><strong>Fase 6 — Revisión de Código (Seguridad y Rendimiento)</strong></summary>

**Prompt principal (resumen):**
> "En una nueva sesión, pega el código completo y solicita una revisión
> crítica enfocada en seguridad y rendimiento, evaluando Clean Code, SOLID,
> separación de responsabilidades y programación defensiva. Cierra con
> recomendaciones futuras."

**Respuesta clave del LLM:**
- **S1 (Alta):** sin cota superior en los factores → overflow a
  `float('inf')` → JSON inválido en la respuesta.
- **S2–S5:** sin límite de longitud en `vehicle_type` crudo, sin límite de
  body a nivel ASGI, dependencias sin lockfile, sin auth/rate-limiting
  documentado.
- **P1–P4:** ruta síncrona sin I/O real (candidata a `async def`), logging
  por request no acotado, `basicConfig` no configurable por entorno, ausencia
  de caché correctamente justificada como acierto.
- Evaluación honesta por principio SOLID (OCP cumplido hoy, con advertencia
  explícita de riesgo futuro si un vehículo requiriera fórmula distinta).
- Roadmap: Strategy pattern, `Protocol EmissionFactorProvider` + adaptador
  (DIP) para fuentes externas, agregación de flota, ISO 14083, `Decimal`
  para reportes de cumplimiento.

**Evolución:** hallazgos priorizados en el backlog de
["Estado de la revisión de código"](#estado-de-la-revisión-de-código).

**Refinamiento post-revisión (misma fase, continuación directa):** se
corrigieron los hallazgos que eran defectos reales de bajo riesgo —
**S1** (`EmissionsOverflowError` + `math.isfinite()` sobre el resultado en
`calculate_co2_emissions`, más cotas superiores simétricas en el schema),
**S2** (límite de 50 caracteres en el string crudo de `vehicle_type` antes de
normalizar) y **P1** (`async def` en el endpoint, ya que no hay I/O
bloqueante). Se agregaron pruebas específicas para cada corrección
(`TestOverflowGuard`, cotas del schema, verificación de que la respuesta
nunca contiene el literal `Infinity`): la suite pasó de 84 a **90 tests**.
S3, S4, S5 y P3 quedaron fuera de este refinamiento por ser decisiones de
despliegue o de tooling ajenas al código del microservicio.

</details>

---

## Reflexión Crítica

Mirando el proceso completo con algo de distancia, lo que más me queda dando
vueltas es lo rápido que uno puede confiar en una fórmula que "suena bien".
El LLM propuso un modelo matemático razonable y hasta alineado con
estándares del sector, pero eso solo salió bien porque en algún momento se
frenó a preguntar en lugar de asumir — si no hubiera surgido esa pausa, el
error habría quedado enterrado en cada número reportado, sin que nadie lo
notara hasta mucho después. Algo parecido pasa con el código: en el papel
cumple SOLID, tiene sus capas bien separadas y su dosis de programación
defensiva, y sin embargo bastó una revisión con otros ojos para encontrar
algo tan básico como un campo sin límite superior que podía romper la
respuesta con un `Infinity`. Tres rondas de "refinamiento" y 84 pruebas
pasando, y ese hueco seguía ahí — lo cual dice bastante: las pruebas que uno
mismo genera tienden a cubrir justo lo que uno ya tenía en mente, no lo que
se le escapó, así que la cobertura real termina siendo un espejo de la
imaginación de quien pidió las pruebas, no del universo completo de cosas
que pueden salir mal. Y ahí es donde el Code Review deja de ser un trámite
y se vuelve el paso que realmente importa: fue la única instancia que no
estaba "enamorada" del diseño porque no lo había construido, y por eso pudo
ver lo que el resto no veía. Si algo me llevo de todo esto es que un LLM es
un compañero de trabajo rapidísimo y bastante competente, pero no es
alguien en quien uno deba confiar a ciegas en ninguna de sus tres promesas
—que el modelo de negocio esté bien pensado, que el código sea robusto, que
las pruebas alcancen—; conviene tratarlo como a un desarrollador junior muy
talentoso: se le puede delegar mucho, pero la revisión final sigue siendo
cosa de humanos (o de otro proceso igual de exigente).
