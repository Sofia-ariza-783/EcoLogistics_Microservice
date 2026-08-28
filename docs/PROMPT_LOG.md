# Bitácora de Prompts — Carbon Tracker Service

Registro de los prompts principales utilizados durante el desarrollo asistido
por LLM del microservicio, junto con las respuestas clave que evidencian la
evolución del código desde el análisis inicial hasta la versión final
revisada. Los prompts se resumen fielmente al contenido original; el código
completo generado en cada fase vive en el repositorio (`app/`, `tests/`).

---

## Fase 1 — Definición del Contexto

**Prompt principal (resumen):**
> "Eres un Desarrollador Senior y Arquitecto de Software especializado en
> microservicios y soluciones sostenibles para logística. Desarrolla el
> Microservicio de Cálculo de Huella de Carbono para EcoLogistics usando
> Python 3.12, FastAPI, Pydantic y Pytest, siguiendo Clean Code, SOLID,
> separación de responsabilidades y programación defensiva. No ejecutes
> ninguna acción todavía, esto es solo contexto."

**Respuesta clave del LLM:**
Confirmó el rol, el stack tecnológico y los principios de diseño como
estándar del proyecto, y se abstuvo deliberadamente de generar código o
estructura de carpetas, a la espera de instrucciones concretas.

**Evidencia de evolución:** ninguna todavía — fase de encuadre. Este contrato
de principios (Clean Code/SOLID/SRP/defensivo) es el criterio contra el que
se evalúa todo el código en las fases 3 a 6.

---

## Fase 2 — Chain-of-Thought (Análisis y Modelo Matemático)

**Prompt principal (resumen):**
> "El microservicio debe calcular las emisiones de CO₂ considerando tipo de
> vehículo (Eléctrico, Diésel, Híbrido), peso de la carga, distancia, factor
> de eficiencia y factor de emisión. Antes de generar código, aplica Chain-of-
> Thought: identifica variables, restricciones de negocio, validaciones,
> casos límite y supuestos; define el modelo matemático explicando unidades y
> fórmula, justificando cada decisión, antes de escribir una sola línea de
> código."

**Respuesta clave del LLM:**
- Tabla de variables de entrada/salida con unidades explícitas.
- Reglas de negocio (fórmula única para los 3 tipos de vehículo, solo cambian
  los factores).
- Validaciones defensivas propuestas (positivos estrictos, no negativos,
  finitud, enum cerrado).
- Casos límite (`distancia = 0`, `factor_emision = 0`, tipo no soportado).
- 5 supuestos explícitos (A1–A5), incluyendo unidades de los factores y
  tratamiento del Híbrido.
- Ante la ambigüedad real entre dos modelos matemáticos plausibles
  (tonelada-km vs. distancia pura con ajuste), el LLM **no asumió
  unilateralmente**: usó `AskUserQuestion` para que el usuario decidiera,
  presentando ambas fórmulas con ejemplo numérico.

**Decisión validada por el usuario:**
```
Emisiones_CO2 (kg) = factor_eficiencia × peso_carga(t) × distancia(km) × factor_emision
```
Híbrido con factores efectivos únicos (sin mezcla ponderada eléctrico/diésel).

**Evidencia de evolución:** esta fórmula, validada aquí *antes* de escribir
código, es exactamente la que se implementa después en
`app/domain/emissions_calculator.py::calculate_co2_emissions`. No hubo
retrabajo posterior de la fórmula — la inversión en CoT previo evitó una
implementación incorrecta o una discusión tardía sobre semántica de negocio.

---

## Fase 3 — Desarrollo del Microservicio (Iterative Refinement)

**Prompt principal (resumen):**
> "Implementa en Python y FastAPI la función principal de cálculo, generando
> los modelos Pydantic y la lógica de negocio. Código documentado, tipado
> estático, apto para producción. Luego aplica Iterative Refinement: mejora
> sucesivamente el manejo de errores y la validación (negativos, nulos, tipos
> no soportados) hasta obtener una versión robusta."

**Respuesta clave del LLM — 3 iteraciones reales sobre el mismo archivo**
(`app/domain/emissions_calculator.py`):

| Iteración | Cambio principal | Qué resolvía |
|---|---|---|
| v1 | `@dataclass` mutable, solo la fórmula, cero validación | Correctitud funcional del cálculo |
| v2 | `InvalidEmissionInputError` / `InvalidVehicleTypeError`; validación de finitud, positividad estricta y no-negatividad | Rechazo explícito de negativos, NaN/inf, tipos no soportados |
| v3 | `frozen=True, slots=True` (inmutabilidad), redondeo controlado, logging estructurado, docstrings Args/Returns/Raises completos | Robustez de producción: invariante protegido de por vida, trazabilidad, sin ruido de punto flotante |

También se generaron `app/domain/vehicle_type.py` (Enum con normalización de
acentos/mayúsculas), `app/domain/exceptions.py`, `app/schemas/emissions.py`
(DTOs Pydantic con validación de forma/rango), `app/api/routes/emissions.py`
y `app/main.py` (exception handlers globales 422/500).

**Evidencia de evolución:** de una función de 6 líneas sin defensas a un
value object inmutable con invariantes garantizados en construcción — visible
directamente en el historial de ediciones de
`app/domain/emissions_calculator.py`.

---

## Fase 4 — Modularización (Arquitectura en Capas)

**Prompt principal (resumen):**
> "Diseña la arquitectura separando lógica de negocio de los controladores
> REST: componentes, modelos de datos, responsabilidades por capa, estructura
> de carpetas y un diagrama textual de interacción entre capas."

**Respuesta clave del LLM:**
- 3 capas: Presentación (controladores), Contratos (DTOs Pydantic), Dominio
  (lógica de negocio) — con regla de dependencia unidireccional.
- Tabla de responsabilidades por componente.
- Diagrama ASCII del flujo request → DTO → dominio → DTO → response,
  incluyendo el camino de error (`EmissionsDomainError` → 422, excepción no
  prevista → 500).
- Distinción explícita entre `EmissionCalculationRequest` (DTO) y
  `EmissionCalculationInput` (modelo de dominio) como frontera deliberada
  (capa anticorrupción), no duplicación accidental.

**Evidencia de evolución:** esta fase **no generó cambios de código** — confirmó
que la estructura de carpetas ya creada en la Fase 3 (`app/api/`,
`app/schemas/`, `app/domain/`) ya satisfacía el diseño en capas propuesto. La
arquitectura fue diseñada implícitamente desde el principio, no como refactor
posterior.

---

## Fase 5 — Generación de Pruebas

**Prompt principal (resumen):**
> "Genera con Pytest una suite de pruebas unitarias para la función principal
> y los endpoints, incluyendo ejemplos de uso. Cubre casos de borde: distancia
> = 0, carga negativa, tipos de vehículo no soportados, verificando que las
> validaciones respondan correctamente."

**Respuesta clave del LLM:**
En lugar de reescribir la suite desde cero, **enriqueció** la ya existente
(evitando duplicación):
- `TestHappyPath` con docstrings narrativos como ejemplos de uso reales
  (camión Diésel, furgón Eléctrico, camión Híbrido).
- `TestRequiredEdgeCases` en dominio (`test_emissions_calculator.py`) y en API
  (`test_emissions_api.py`), verificando **tipo de excepción y contenido del
  mensaje** (no solo "algo falló").
- `test_edge_case_never_returns_500_for_invalid_business_input`: confirma que
  ningún caso de borde de negocio degrada a un error interno.

**Evidencia de evolución:** de 77 a 84 tests, con trazabilidad 1:1 entre cada
caso de borde nombrado en el prompt y un test explícitamente identificable
por su nombre.

---

## Fase 6 — Revisión de Código (Seguridad y Rendimiento)

**Prompt principal (resumen):**
> "En una nueva sesión, actuando de nuevo como Desarrollador Senior, pega el
> código completo y solicita una revisión crítica enfocada en seguridad y
> rendimiento, evaluando Clean Code, SOLID, separación de responsabilidades y
> programación defensiva. Cierra con recomendaciones futuras (nuevos tipos de
> vehículo, fuentes externas de factores, análisis ambiental avanzado)."

**Respuesta clave del LLM:**
Revisión independiente con hallazgos concretos, no genéricos:

- **S1 (Alta):** `efficiency_factor`/`emission_factor` sin cota superior →
  overflow a `float('inf')` → `"emissions_kg": Infinity` en la respuesta
  (JSON inválido según RFC 8259). Asimetría defensiva respecto a
  `cargo_weight_tonnes`/`distance_km`, que sí tienen techo.
- **S2–S5:** sin límite de longitud en el string de `vehicle_type` antes de
  normalizar, sin límite de tamaño de body a nivel ASGI, dependencias sin
  lockfile con hashes, sin auth/rate-limiting documentado como decisión.
- **P1–P4 (rendimiento):** ruta síncrona sin I/O real forzando despacho a
  threadpool (mejor como `async def`), logging por request no acotado,
  `logging.basicConfig()` no configurable por entorno, ausencia de caché
  correctamente justificada como acierto (no como falta).
- Evaluación honesta por principio SOLID: OCP cumplido para el caso previsto,
  con advertencia explícita de que se rompería si un futuro vehículo
  necesitara una fórmula distinta (no solo distintos factores) — recomienda
  Strategy pattern antes de que ocurra, no después.
- Roadmap: Strategy pattern para fórmulas heterogéneas, `Protocol
  EmissionFactorProvider` + adaptador en `app/infrastructure/` para fuentes
  externas (DIP), agregación de flota, alineación con ISO 14083, migración a
  `Decimal` si los números alimentan reportes de cumplimiento.

**Evidencia de evolución:** los hallazgos quedaron priorizados en un backlog
(ver tabla más abajo). Los que representaban un defecto real de robustez o
una mejora de rendimiento de bajo riesgo se cerraron de inmediato como
continuación directa de esta misma revisión (ver siguiente apartado); los que
eran decisiones de infraestructura/despliegue (S3, S5) o de tooling de
dependencias (S4) quedaron fuera de alcance del código del microservicio en
sí y se mantienen documentados como trabajo futuro.

### Fase 6 (continuación) — Refinamiento Post-Revisión

**Prompt principal (resumen):**
> "Realiza el proceso de refinamiento y documéntalo como si se hubiera
> realizado en el paso adecuado, si es que es necesario. Los demás puntos
> ignóralos por ahora."

**Criterio de priorización aplicado:** de los 9 hallazgos (S1–S5, P1–P4), se
corrigieron los que eran defectos reales del código del microservicio y de
bajo riesgo de implementar; se dejaron fuera los que eran decisiones de
despliegue/infraestructura (S3, S5), de tooling externo al código (S4) o de
prioridad menor (P3, P4 ya justificado como acierto).

**Respuesta clave del LLM — cambios aplicados:**

| ID | Corrección aplicada | Archivo(s) |
|---|---|---|
| S1 | Nueva excepción `EmissionsOverflowError`; `calculate_co2_emissions` verifica `math.isfinite()` sobre el resultado antes de redondear, sin importar qué combinación de factores lo produjo. Complementado con cotas superiores (`le=10.0` / `le=50.0`) en `efficiency_factor`/`emission_factor` del schema, simétricas a las ya existentes en `cargo_weight_tonnes`/`distance_km`. | `app/domain/exceptions.py`, `app/domain/emissions_calculator.py`, `app/schemas/emissions.py` |
| S2 | `VehicleType.from_input` rechaza strings de más de 50 caracteres antes de ejecutar la normalización Unicode. | `app/domain/vehicle_type.py` |
| P1 | El endpoint `POST /emissions/calculate` pasó de `def` a `async def`: al no haber I/O bloqueante, esto evita el despacho innecesario al threadpool acotado de Starlette. | `app/api/routes/emissions.py` |

**Pruebas agregadas para evidenciar cada corrección:**
- `TestOverflowGuard` (dominio): valores astronómicos disparan
  `EmissionsOverflowError`; un envío grande pero realista (150 t, 15 000 km)
  sigue calculando con normalidad (evita sobre-corregir).
- `test_rejects_out_of_range_numeric_fields` (schema): casos parametrizados
  para las nuevas cotas superiores.
- `test_rejects_vehicle_type_string_exceeding_max_length` (schema).
- `test_calculate_emissions_rejects_efficiency_factor_above_ceiling` (API):
  confirma 422 y que la respuesta nunca contiene el literal `Infinity`.

**Resultado:** de 84 a **90 tests, todos en verde**.

**Explícitamente fuera de alcance en este refinamiento** (a petición
explícita, no por descuido): S3 (límite de body a nivel ASGI), S4 (lockfile
de dependencias con hashes), S5 (auth/rate-limiting) y P3 (logging
configurable por entorno). Se mantienen documentados como backlog abierto.

---

## Backlog de hallazgos

| ID | Hallazgo | Estado |
|---|---|---|
| S1 | Sin cota superior en `efficiency_factor`/`emission_factor` (riesgo de `Infinity` en la respuesta) | ✅ Corregido (Fase 6, continuación) |
| S2 | Sin `max_length` en el string crudo de `vehicle_type` antes de normalizar | ✅ Corregido (Fase 6, continuación) |
| P1 | Endpoint síncrono sin I/O real (candidato a `async def`) | ✅ Corregido (Fase 6, continuación) |
| S3 | Sin límite de tamaño de body a nivel de aplicación/ASGI | Pendiente (decisión de despliegue, fuera de alcance) |
| S4 | `requirements.txt` sin lockfile con hashes | Pendiente (fuera de alcance) |
| S5 | Sin auth/rate-limiting documentado como decisión explícita | Pendiente (decisión de despliegue, fuera de alcance) |
| P3 | `logging.basicConfig()` no configurable por entorno | Pendiente (fuera de alcance) |
