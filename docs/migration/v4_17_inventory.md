# Inventario de migración `v4.17_pre`

| Campo | Valor |
|---|---|
| Tarea | `P00-T05` |
| Fecha de inspección | `2026-08-24` |
| Repositorio predecesor (solo lectura) | `C:\Users\aalvarezg\Documents\Home Assistant\Scripts Automatizaciones` |
| Baseline operativo | `automation_versions/asesor_ventanas_automatizacion_v4_17_pre.yaml` |
| Política | Mantener `v4.17_pre` inmutable; la integración nueva permanece en recomendación/sombra y no acciona persianas o ventanas |
| Estado | Inventario terminado; A01/A02 se copiaron byte a byte a los fixtures de P00-T09 y el predecesor permanece sin modificaciones |

Este documento es la frontera de importación para `P00-T09`. Todos los caminos
de las tablas son relativos a la raíz del repositorio predecesor indicada arriba.
Los artefactos predecesores siguen siendo evidencia de rollback y no se
reutilizan como archivos de producción.

## Método y límites de la inspección

- Se comprobaron con `Test-Path -LiteralPath` todos los caminos de las tablas y
  se recalculó cada SHA-256 localmente con `Get-FileHash -Algorithm SHA256`.
- No se ejecutaron despliegues, llamadas a Home Assistant, aplicaciones,
  MCP ni servicios externos. La inspección es de archivos y documentación.
- No se copiaron valores de `.env`, estados de entidades, trazas completas,
  copias de seguridad, coordenadas privadas ni adjuntos de ejecución.
- El predecesor no contiene un replay separado en CSV/JSON/Parquet. Las
  simulaciones disponibles son el bucle determinista embebido en
  `tests/test_v4_17_blind_percentage.py` y los resultados resumidos en los dos
  documentos de modelo. Las tareas P01 propietarias deben derivar esos casos
  sin inventar un histórico ni presentar el resumen como una medición nueva.

## Artefactos seleccionados para importación o derivación

La columna `SHA-256` se incluye también para referencias que no se copiarán,
para que cualquier cambio posterior en el predecesor sea detectable. `COPY`
significa preservar los bytes; `DERIVE` significa extraer solo los casos,
constantes o aserciones necesarios y adaptar rutas/contratos del nuevo
repositorio; `REFERENCE` significa que el archivo solo aporta procedencia o
evidencia y no entra en P00-T09.

| ID | Ruta relativa exacta | SHA-256 local | Procedencia y propósito | Disposición P00-T09 |
|---|---|---|---|---|
| A01 | `automation_versions/asesor_ventanas_automatizacion_v4_17_pre.yaml` | `4f3cec8d2ba8ed0ffd037b2cc2ecb510ddc94a6a75007824d52c7c2f13b0b0ea` | Archivo propio de la baseline desplegada; contiene alias `v4.17_pre`, porcentaje recomendado, diagnóstico y política de aviso sin acción `cover.*`. | `COPY` exacto a `tests/fixtures/migration/v4_17_pre/automation.yaml`; verificar el mismo hash. |
| A02 | `automation_versions/asesor_ventanas_automatizacion_v4_16_pre.yaml` | `974c46e340325f00f7d0d7c6b54afe963d99e58a14c7c13681368caf20fd6acc` | Baseline térmica inmediata contra la que la prueba de v4.17 verifica regresión e inmutabilidad. | `COPY` exacto a `tests/fixtures/migration/v4_16_pre/automation.yaml`; verificar el mismo hash. |
| A03 | `tests/test_v4_17_blind_percentage.py` | `59ba6a7c0b4079b191020fdf570960f2db1bfc2c504fbf37d817012f1f9f6f9e` | Caracterización ejecutable del porcentaje 0–100 %, paso 10 %, monotonía, previsión conservadora, extremos físicos, simulación de 30 días y separación entre diagnóstico y aviso. | `REFERENCE`; P01-T01 inventaría los casos y P01-T02/P01-T04/P01-T07 crearán las aserciones junto a sus consumidores. |
| A04 | `tests/test_v4_16_thermal_balance.py` | `fbe1340b6ff05356a0abebedab3c25e86902a6e0cdb61a02e4da47d1b0036840` | Caracterización de área/caudal, balance solar-conducción, fallback sin previsión, histéresis, puertas de calidad Hyperlocal y prioridad meteorológica. | `REFERENCE`; P01-T01 inventaría los casos y P01-T02/P01-T04/P01-T06/P01-T07 crearán las aserciones; no se importan estados de Home Assistant. |
| A05 | `tests/test_wind_exposure.py` | `4cbf57ca42aef5bd81354c2f2057df0b85fcd85d8ca19a0e0408757e276f15b7` | Casos puros de distancia angular, peor dirección entre instantánea/media, exposición continua y protección de lluvia por alero. | `REFERENCE`; P01-T01 conserva la matriz y P01-T06 deriva las pruebas de seguridad/geometry con sus unidades y bordes. |
| A06 | `tests/test_temperate_strategy.py` | `3a742912ee798a8f8599143ffdaf4425dc7cdc2a95778bb7943caef27783a585` | Política histórica del modo templado: previsión completa, historial caliente/frío, umbrales estrictos, datos ausentes y límite de estado compacto. | `REFERENCE`; P01-T01 conserva la matriz y P01-T03 deriva las pruebas de perfiles; no se importa serialización `input_text`. |
| A07 | `tests/test_v4_15_aggregation_policy.py` | `dac8ff352709ae6c5d811fcc1d931ad77d0a20d3c1c18bafce295f29d1ec4714` | Evolución aceptada de cadencia `/30`, una notificación consolidada, disparos de seguridad separados, persistencia selectiva A/O y estados bajo 255 caracteres. | `REFERENCE`; P01-T01 conserva la matriz y P01-T07 deriva las pruebas de estabilidad/estado; no se copian destinatarios. |
| A08 | `tests/test_v4_13_notification_policy.py` | `749a1420d4a8e17b234ee1418a1f7884029c64804725b1bdd6de615a3e22d745` | Comportamiento heredado aceptado: estabilidad de persiana de 15 min, reapertura meteorológica de 30 min, histéresis solar, deduplicación y máximo una notificación. | `REFERENCE`; P01-T01 conserva la matriz y P01-T07 deriva las transiciones; no se copian helpers `input_*` ni destinatarios. |
| A09 | `MODELO_PERSIANAS_v4_17_pre.md` | `f189c6d762d5d5bf96bb534624ba865684b05758581e2a46ca7ec807184ac59a` | Especificación de significado de 0/100 %, mezcla de áreas, residual 0,15 provisional, bandas 1,5/2,0 °C, prioridad de ventilación y política de ruido. | `REFERENCE`; P01-T01 registra supuestos y P01-T02/P01-T04/P01-T07 los prueban sin presentarlos como datos medidos. |
| A10 | `MODELO_TERMICO_v4_16_pre.md` | `23130d55e2015524f3b300da6e3f11e09b66d45ee474a063611bfa58eb9f2c55` | Especificación de fuentes, ecuaciones, signos, fallback, histéresis, simulación de 835 evaluaciones y limitaciones de calibración. | `REFERENCE`; P01-T01 registra los casos y P01-T02/P01-T04/P01-T07 los prueban con incertidumbre explícita. |

## Referencias históricas y de aceptación (no importar)

Estas fuentes ayudan a interpretar regresiones y la procedencia de la política,
pero no son archivos de fixture de `v4.17_pre`. Se mantienen intactas en el
repositorio predecesor.

| Ruta relativa exacta | SHA-256 local | Uso de referencia | Motivo para no copiar |
|---|---|---|---|
| `tests/test_v4_14_temperature_smoothing.py` | `8990505421e4a8f0614875925e106e62df892ccf9a4a6301b4de6f5c8c22440e` | Evidencia de la migración de media exterior de 15 a 30 minutos y de la regresión estructural v4.13→v4.14. | La integración nueva debe traducir fuentes mediante adaptadores/config-entry; no debe importar pruebas que dependan de YAML históricos o de `PLAN.md`. |
| `tests/test_summer_notification_separation.py` | `be4e813be893f28fb8b4dba4be621517a2605c2b0af5957957dc7318555778c1` | Catálogo de separación de avisos de ventana/persiana, agrupación por habitación, histéresis y compactación. | Apunta explícitamente a `asesor_ventanas_automatizacion_v4_sin_exceso_avisos.yaml`, no a la baseline v4.17; solo se pueden derivar casos que el contrato nuevo acepte. |
| `automation_versions/asesor_ventanas_automatizacion_v4_15_pre.yaml` | `a23f6df5ef12210c0abac8d0211a7c6f745b0c6dbb5b476580e4ec43f42d229f` | Antecesor de la cadencia y persistencia selectiva que A07 caracteriza. | No copiar versiones anteriores; A01 es la única automatización de rollback que se importa como fixture. |
| `automation_versions/asesor_ventanas_automatizacion_v4_14_pre.yaml` | `093b816bbd554ed619d72b93866247752feb490d05451344b1fd765b44bdd2de` | Antecesor de la fuente térmica de 30 minutos. | No copiar versiones anteriores. |
| `automation_versions/asesor_ventanas_automatizacion_v4_13_pre.yaml` | `dbb9f69e922827f71d4f42a8125452f038df49b158791da22d4ef8d9b1f8a787` | Antecesor de la máquina de estabilidad y de notificación que A08 caracteriza. | No copiar versiones anteriores. |
| `automation_versions/asesor_ventanas_automatizacion_v4_sin_exceso_avisos.yaml` | `971b0dafdff9012f6442bd0df86abd22abb2db111472a29439874c3aa7f672aa` | Fuente de A08 ampliada en A09 histórico y del test de separación de verano. | No es la baseline v4.17 y no debe convertirse en una segunda fuente de verdad. |
| `PLAN.md` | `5b3a4215807434ae3fd67f4adcd4c21d10eeab871cfad9f56f3cea2a00bdb2cf` | Filas F01-07–F01-09 y registro de modificaciones: hashes, conteos de pruebas, simulaciones y evidencia de despliegue. | Contiene identificadores y trazas de Home Assistant; se citan hechos sanitizados, nunca se copia el documento ni su estado de ejecución. |
| `HANDOFF_asesor_ventanas_home_assistant.md` | `98045527b160c42172d57ab4adfd3c287ed3f7ddc3357f2821e8bcf26a29b4b1` | Matriz de aceptación heredada (escenarios 1–42, líneas 810–880) y arquitectura de migración. | Contiene inventario de entidades y supuestos de una instalación concreta; solo se usa como catálogo de escenarios, sin importar runtime. |
| `CHECKLIST_despliegue_asesor_ventanas.md` | `3c14bddcde010135a2eaee056274effccb9cc3e556084d2df8626bb78b671a3b` | Procedimiento histórico de despliegue y rollback, versión v4.4. | Es antiguo y operativo; no constituye evidencia v4.17 ni fixture de la integración. |
| `INFORME_despliegue_asesor_ventanas_2026-08-06.md` | `f25a6df3028f0e9c9937f965c301e62c4711255f9d3473579ce99dd760d6ca19` | Informe histórico de despliegue previo a v4.17. | Puede contener estado/runtime de una instalación; se conserva como referencia privada y no se copia. |

## Escenarios aceptados y trazabilidad a pruebas

La siguiente matriz separa lo caracterizado de forma ejecutable de lo que solo
está descrito como requisito heredado. Los nombres de métodos son los del
predecesor y sirven de ancla para que P00-T09 derive pruebas sin depender de
`Path(__file__).parents[1]` ni de un `PLAN.md` ajeno.

| ID | Comportamiento aceptado | Evidencia de origen | Cobertura/importación prevista |
|---|---|---|---|
| S01 | La baseline tiene archivo y alias propios; v4.16 permanece inmutable; YAML y todas las plantillas Jinja se pueden analizar. | A03 `test_version_is_independent_and_v416_is_immutable`, `test_yaml_and_all_jinja_templates_parse`; A01/A02. | Copiar A01/A02; derivar validación de parseo y hash en characterization tests. |
| S02 | El porcentaje está acotado, es accionable en pasos de 10 % y nunca supera el 20 % mínimo de cierre cuando la protección solar está activa. | A03 `test_model_constants_and_semantics_are_explicit`, `test_percentage_is_bounded_and_actionable`; A09, secciones «Modelo térmico» y «Prioridades». | Derivar función/tabla de casos; no importar plantillas como lógica de dominio. |
| S03 | Más temperatura interior o más sol no abre más la persiana; la previsión válida usa el peor sol y conducción actual/previstos. | A03 `test_more_heat_or_sun_never_opens_the_blind_further`, `test_forecast_uses_the_worst_solar_and_conduction_case`; A09. | Derivar pruebas de monotonía y selección conservadora. |
| S04 | Lluvia/racha conservan prioridad; si se recomienda `A/O`, la persiana queda al 100 %; `G/V` queda al 100 %, `I` al 0 %; no hay movimiento automático. | A03 `test_airflow_priority_and_winter_extremes`; A01; A09 «Prioridades». | Derivar casos de política; comprobar ausencia de `cover.*` y mantener recomendación-only. |
| S05 | Variaciones de porcentaje no crean avisos; solo se incorpora el porcentaje después de confirmar la acción física de persiana durante 15 min. | A03 `test_thirty_day_simulation_does_not_turn_percentage_drift_into_alerts`, `test_notification_adds_percentage_only_after_physical_confirmation`; A09 «Política de ruido». | Derivar simulación determinista de 30 días y máquina de estabilidad; no convertir cada escalón en transición de estado. |
| S06 | El modelo térmico usa 1,60 × 1,20 m, área 1,92 m², caudal unilateral conservador, SHGC 0,55 y U 1,40; el sol puede invertir el beneficio de abrir. | A04 `test_physical_constants_and_geometry_are_explicit`, `test_airflow_scales_with_free_opening_area`, `test_solar_gain_can_reverse_an_otherwise_useful_opening`; A10 «Ecuaciones». | Derivar módulos puros de geometry/thermal y sus unidades. |
| S07 | El peor balance previsto impide abrir; sin previsión válida el umbral de apertura es más estricto; una apertura ya notificada conserva histéresis de +50 W. | A04 `test_forecast_is_conservative_and_fallback_is_stricter`, `test_power_hysteresis_retains_opening_without_rearming_it`; A10 «Decisión e histéresis». | Derivar casos con dato actual/previsto y calidad explícita, sin fallback favorable. |
| S08 | Fuentes Hyperlocal inválidas se degradan al dato actual y dejan diagnóstico; seguridad, recuperación meteorológica y política de persiana permanecen separadas. | A04 `test_hyperlocal_inputs_have_quality_gates_and_fallback`, `test_safety_notification_and_blind_policies_are_preserved`. | Derivar estados `missing/unavailable/stale`; no copiar entity IDs ni estados reales. |
| S09 | La exposición de viento es continua, usa la peor dirección de instantánea/media y calcula protección de lluvia según alero, hueco y racha. | A05 `test_angular_distance_wraps_around_north`, `test_current_and_average_use_the_worst_direction_per_facade`, `test_lateral_wind_keeps_a_safety_component`, `test_limits_change_continuously_without_quadrants`, `test_desk_roof_protects_more_than_half_meter_overhang`; HANDOFF escenarios 26–35. | Derivar pruebas puras; faltan en el predecesor casos solares completos 1–6, que quedan para la fase de geometría. |
| S10 | En clima templado, previsión completa por debajo de 25 °C selecciona calentar, por encima selecciona refrescar; previsión mixta usa historial estricto; dato ausente mantiene neutralidad. | A06 todos los métodos `TemperateStrategyTests`; HANDOFF escenarios 21–25. | Derivar política estacional sin cachear runtime en `input_text`. |
| S11 | La cadencia ordinaria es `/30`, seguridad meteorológica tiene disparos independientes y cada evaluación agrupa como máximo una notificación; estados compactos quedan bajo 255 caracteres. | A07 `test_ordinary_cadence_is_thirty_minutes`, `test_safety_and_recovery_triggers_remain_independent`, `test_each_evaluation_has_one_consolidated_mobile_action`, `test_persisted_state_stays_below_input_text_limit`. | Derivar contratos de transición/estado y un límite de tamaño; no importar destinatario ni payload. |
| S12 | La estabilidad heredada evita ruido: persiana 15 min, mejora A/O selectiva, reapertura seca 30 min, cierre meteorológico inmediato y no repetir recomendación igual. | A08 `test_blinds_require_fifteen_continuous_minutes`, `test_opposite_blind_action_rearms_after_stability`, `test_radiation_uses_entry_and_exit_hysteresis`, `test_open_to_tilt_is_immediate_but_tilt_to_open_is_stable`, `test_weather_recovery_does_not_clear_physical_memory`; A07; HANDOFF 7–20 y 35. | Derivar solo la máquina de estados necesaria; el contrato nuevo no hereda helpers `input_*`. |
| S13 | Separar cierre de ventana y protección de persiana, agrupar por habitación y evitar duplicados; conservar cuerpos compactos si el contrato de notificación se activa tras sombra. | `tests/test_summer_notification_separation.py` (métodos `test_blind_protection_does_not_consume_window_closure` a `test_duplicate_room_names_are_suppressed_in_summaries`), pero sobre baseline `v4_sin_exceso_avisos`. | `REFERENCE`: derivar únicamente casos que el diseño de integración acepte después de la etapa de shadow; no copiar el YAML ni el test completo. |
| S14 | Resiliencia: sensor interior ausente no se convierte en cero, previsión ausente degrada explícitamente, reinicio no repite categorías y estado compacto no se trunca. | HANDOFF escenarios 36–42; A04 fallback; A07/A08 límites de estado. | No se cubre conductualmente en P00-T09; reinicio, disponibilidad y entidades son trabajo de P00-T03/P01. No inventar fixtures de runtime. |

### Escenarios heredados aún no demostrados por un artefacto ejecutable

El `HANDOFF` lista geometría solar frontal/lateral y sombras de alero en los
escenarios 1–6, pero el predecesor no contiene un test solar equivalente (A05
solo cubre exposición de viento y lluvia). También lista casos de reinicio y
eventos perdidos en 36–42 sin replay de Home Assistant. Se registran aquí como
brechas explícitas para P01; no se rellenan con datos inventados durante
P00-T09. Las pruebas A03–A08 y el resumen de A09/A10 sí son la evidencia
disponible y aceptada para el alcance de esta importación.

## Simulaciones y evidencia de despliegue

### Simulaciones disponibles

1. **Porcentaje v4.17:** A03, método
   `test_thirty_day_simulation_does_not_turn_percentage_drift_into_alerts`,
   recorre 30 días × 48 muestras de 30 minutos. Comprueba 60 transiciones de
   acción física, más transiciones de porcentaje, y que la notificación no se
   dispara por el mero drift porcentual.
2. **Balance v4.16:** A10, sección «Simulación y límites», resume 167 horas ×
   5 huecos = 835 evaluaciones reales; la comparación reportada reduce 70 a 50
   transiciones y no produce ciclos de una sola muestra. No se encontró el
   histórico bruto; el resumen no debe copiarse como dataset.
3. **Conteos documentados:** `PLAN.md`, filas F01-07/F01-08 y registro de
   modificaciones, informa `108 passed`, 6 subpruebas, 145 plantillas Jinja
   válidas y regresión contra el hash de A02. Son evidencia histórica del
   predecesor, no un resultado ejecutado por P00-T05.

### Referencias de despliegue aceptado, sanitizadas

Las referencias son solo documentales; no contienen una exportación de estado
privado en este inventario y no se copian al nuevo repositorio.

| Referencia | Hecho aceptado que se puede reutilizar | Lo que se excluye |
|---|---|---|
| `PLAN.md:54` (fila F01-09) | La baseline v4.17 se actualizó sobre la automatización existente, conservando identidad, una sola coincidencia, configuración cargada y ejecución finalizada sin errores ni aviso redundante. | IDs de traza, payloads, estados de sensores y cualquier dump de Home Assistant. |
| `PLAN.md:98` (registro F01-09) | Se documentó configuración local/remota idéntica, hash canónico de configuración desplegada `9300b99ed0268865` (distinto del SHA-256 del archivo fuente A01), validación global sin errores/avisos y una ejecución con porcentajes calculados. | El identificador de traza y sus acciones detalladas; no se reejecuta ni verifica externamente en esta tarea. |
| `PLAN.md:50-53,94-97` (F01-05–F01-08) | Procedencia de v4.16, modelo físico, pruebas, simulaciones y transición a v4.17. | Entity IDs, valores de una instalación y cualquier secreto. |
| `CHECKLIST_despliegue_asesor_ventanas.md` | Runbook histórico de backup, carga, comprobación y rollback, útil como contexto. | No se considera evidencia v4.17; no importar helpers ni nombres de instalación. |

El despliegue de la integración nueva, su `entity_id`, disponibilidad,
configuración y rollback pertenecen al root manager y a las tareas
`P00-T04`/`P01-T10`. Este executor no realizó ninguna mutación
externa.

## Manifest mínimo de importación para `P00-T09`

Esta tabla conserva la instrucción versionada de importación y distingue los
dos `COPY` ya ejecutados de las derivaciones conductuales que P01-T01
inventariará y sus tareas propietarias implementarán.

| Acción | Fuente | Destino propuesto | Regla de integridad/alcance |
|---|---|---|---|
| `COPY` | A01 | `tests/fixtures/migration/v4_17_pre/automation.yaml` | Copiar bytes sin normalizar YAML; recalcular y exigir SHA-256 A01. Mantenerlo como rollback/characterization fixture, nunca como automatización desplegable. |
| `COPY` | A02 | `tests/fixtures/migration/v4_16_pre/automation.yaml` | Copiar bytes sin normalizar; exigir SHA-256 A02. Solo baseline de regresión, no segunda automatización. |
| `DEFER → P01-T02/T04/T07` | A03 + A09 | Pruebas de los módulos propietarios | Inventariar primero los casos en P01-T01; derivar porcentaje, monotonía, extremos, simulación y estabilidad solo junto al consumidor real. |
| `DEFER → P01-T02/T04/T06/T07` | A04 + A10 | Pruebas de los módulos propietarios | Inventariar primero unidades, ecuaciones, fallback, histéresis y calidad; no simular estados de HA ni crear una implementación de legado. |
| `DEFER → P01-T06` | A05 | `tests/unit/domain/test_policy.py` | Derivar ángulos, exposición y alero junto a la política de seguridad, sin entidades ni llamadas de servicio. |
| `DEFER → P01-T03` | A06 | `tests/unit/domain/test_profiles.py` | Mantener los criterios de decisión y el caso neutral; no importar serialización `input_text`. |
| `DEFER → P01-T07` | A07 + A08 | `tests/unit/domain/test_state_machine.py` | Derivar estabilidad, reapertura, deduplicación y límites de estado; sustituir notificación móvil por salida tipada. |
| `REFERENCE` | `HANDOFF_asesor_ventanas_home_assistant.md:810-880` | No crear archivo todavía | Usar los escenarios 1–42 para completar P01; los casos sin fuente ejecutable quedan marcados como pendientes, no como fixtures inventados. |

### Resultado ejecutable de P00-T09

La importación ejecutada queda deliberadamente limitada a dos fixtures de
integridad y a una prueba estructural:

| Artefacto nuevo | Procedencia | Comprobaciones ejecutables | Alcance excluido |
|---|---|---|---|
| `tests/fixtures/migration/v4_17_pre/automation.yaml` | Copia byte a byte de A01 | SHA-256 `4f3cec8d2ba8ed0ffd037b2cc2ecb510ddc94a6a75007824d52c7c2f13b0b0ea`, YAML válido, alias versionado, plantillas Jinja compilables y ausencia de acciones de servicio `cover.*`. | No es automatización desplegable ni fuente de lógica nueva. |
| `tests/fixtures/migration/v4_16_pre/automation.yaml` | Copia byte a byte de A02 | SHA-256 `974c46e340325f00f7d0d7c6b54afe963d99e58a14c7c13681368caf20fd6acc`, YAML válido, alias versionado, plantillas Jinja compilables y ausencia de acciones de servicio `cover.*`. | No es una segunda baseline operativa ni una implementación de v4.16. |
| `tests/characterization/test_migration_fixtures.py` | Derivación estructural de A01/A02 y de la frontera de importación | Verifica hashes, parseo YAML, compilación de todas las plantillas embebidas, independencia de versiones y política recommendation-only. | No contiene aserciones de porcentaje, térmica, viento, estrategia, histéresis, notificación ni simulación de dominio. |

P01-T01 convertirá S02–S14 y A03–A10 en una matriz versionada de casos y
disposiciones. Las aserciones ejecutables se crearán después en P01-T02–P01-T07
junto al consumidor propietario. Copiar ahora los tests heredados o inventar un
evaluador habría creado una segunda fuente de verdad. P00-T09 demuestra la
integridad y la importabilidad segura de la baseline, no la paridad funcional
del futuro dominio.

### No copiar ni derivar en P00-T09

- `.env`, tokens, URLs con credenciales, coordenadas exactas,
  copias de seguridad, dumps de entidades, trazas, estados de sensores y
  cualquier otro runtime privado.
- `tests/__pycache__/`, `*.pyc`, `.pytest_cache/`, `.codex-remote-attachments/`
  y demás artefactos generados.
- `automation_versions/asesor_ventanas_automatizacion_v4_13_pre.yaml`,
  `v4_14_pre.yaml`, `v4_15_pre.yaml` y
  `v4_sin_exceso_avisos.yaml`: son historia, no baselines adicionales.
- `tests/test_summer_notification_separation.py` completo: apunta a una
  automatización distinta; solo puede aportar casos derivados y aprobados por
  el contrato de sombra.
- `PLAN.md`, `HANDOFF_asesor_ventanas_home_assistant.md`,
  `CHECKLIST_despliegue_asesor_ventanas.md` e
  `INFORME_despliegue_asesor_ventanas_2026-08-06.md`: referencias de
  procedencia/evidencia, no configuración ni fixtures.
- `tarjeta_asesor_ventanas.yaml`: tarjeta Lovelace del predecesor, fuera del
  contrato inicial de la integración.

## Verificaciones de aceptación de este inventario

Resultado de la inspección local:

- Todos los caminos A01–A10 y de referencia existen en la raíz predecesora.
- Los SHA-256 de las tablas se recalcularon localmente; A01 y A02 coinciden
  con los hashes registrados por sus pruebas/documentación.
- No se modificó ningún archivo del predecesor; solo se copiaron A01 y A02 a
  sus destinos versionados, con hashes idénticos a las fuentes.
- `git diff --check` del repositorio destino pasa después de crear este archivo;
  los cambios ajenos de `P00-T02` (`docs/phases/00-bootstrap/PLAN.md` y
  `.python-version`) se conservan sin tocar.
- La ausencia de replay bruto queda documentada como límite de evidencia, no
  se oculta ni se rellena con datos privados o sintéticos no aceptados.
