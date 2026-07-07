# MEJORAS_PROYECTO.md

Historial técnico del subagente de seriedad de llamadas. Cada sesión de trabajo agrega una entrada con fecha. Las secciones **Roadmap Técnico** y **Deuda Técnica** al final del documento son las versiones vivas y se actualizan en cada sesión.

---

# Sesión 2026-07-06 — Revisión técnica completa

---

## 1. Resumen Ejecutivo

### Estado general

El proyecto es un MVP Python funcional para estimar la seriedad de llamadas de emergencia. Combina análisis acústico (librosa), ASR opcional (Whisper local), análisis semántico por reglas y una política de decisión conservadora. El pipeline es lineal y comprensible, el código está razonablemente organizado por capas, y existe una suite de 114 tests unitarios que pasan al 100%.

### Nivel de calidad del código

**Bueno para un MVP académico.** El código es legible, tiene manejo de errores defensivo en los puntos críticos, utiliza dataclasses para la configuración, evita dependencias externas de pago y respeta la restricción ética principal (nunca recomendar colgar llamadas).

### Fortalezas

- Arquitectura clara separada en capas: audio, ASR, semántica, scoring, reporte, utils.
- Pipeline de ejecución lineal y fácil de seguir en `main.py`.
- Configuración centralizada con `AudioAnalysisConfig` y `AppConfig`.
- 114 tests unitarios cubriendo todos los módulos críticos.
- Manejo de modos: con audio, solo transcripción, y fallback si librosa/Whisper fallan.
- Política de decisión conservadora que prioriza la seguridad sobre la eficiencia.
- Documentación metodológica detallada en `docs/`.

### Debilidades

- Funciones privadas duplicadas entre módulos (`_clamp`, `_optional_float`).
- Campos de configuración definidos pero nunca utilizados (`f0_min_hz`, `f0_max_hz`).
- La ventana de análisis acústico se calcula cuatro veces por llamada en lugar de una.
- Cobertura de tests muy baja para `emergency_indicators.py` (solo 3 tests para el módulo heurístico más complejo).
- No existen tests de integración end-to-end.
- `2do avance.md` en la raíz es un documento obsoleto que duplica contenido del README.

---

## 2. Mejoras implementadas

### Mejora 1 — Configuración del logger al nivel de módulo

**Archivos modificados:**
- `src/utils/logger.py`

**Problema detectado:**
`logging.basicConfig(...)` se llamaba dentro de `get_logger()`, es decir, en cada invocación de esa función. Aunque `basicConfig` es idempotente (no-op después de la primera llamada), la llamada repetida es innecesaria, dificulta la lectura de la intención del código y puede enmascarar problemas si alguien intentara personalizar la configuración de logging antes de llamar a `get_logger`.

**Solución implementada:**
Se movió la llamada a `basicConfig` al nivel de módulo, fuera de la función. `get_logger` ahora solo devuelve el logger por nombre.

**Beneficios:**
- La configuración del logger ocurre exactamente una vez al importar el módulo.
- La función `get_logger` tiene una única responsabilidad clara.
- Facilita sobreescribir la configuración de logging desde el exterior antes de importar el módulo.

---

### Mejora 2 — Eliminación de import `Tuple` obsoleto en preprocessing

**Archivos modificados:**
- `src/audio/preprocessing.py`

**Problema detectado:**
El módulo importaba `Tuple` del módulo `typing` (`from typing import Any, Tuple`) pero el proyecto ya utiliza `from __future__ import annotations`, que permite usar la sintaxis de anotaciones nativa de Python 3.9+ sin activarla en runtime. El tipo `Tuple[Any, int]` del módulo `typing` es el equivalente legado de `tuple[Any, int]`.

**Solución implementada:**
- Se eliminó `Tuple` del import de `typing`.
- Se actualizó la firma de `load_audio` de `Tuple[Any, int]` a `tuple[Any, int]`.

**Beneficios:**
- Elimina un import sin uso.
- Consistencia con el estilo moderno de Python 3.9+ que usa el resto del proyecto.
- Reduce la dependencia innecesaria en `typing` para tipos básicos.

---

### Mejora 3 — Renombrado de `_weighted_mean` a `_mean_valid` en emergency_indicators

**Archivos modificados:**
- `src/audio/emergency_indicators.py`

**Problema detectado:**
La función `_weighted_mean` computaba una media aritmética simple de los valores no-None de un tuple, sin ningún peso diferencial. El nombre "weighted mean" (media ponderada) es incorrecto y engañoso: implicaría que cada valor tiene un peso asignado, lo cual no ocurre. Un desarrollador que lea el nombre esperaría una lógica de ponderación que no existe.

**Solución implementada:**
Se renombró la función a `_mean_valid` (media de los valores válidos), que describe con precisión su comportamiento: calcula la media aritmética de los elementos no-None del tuple de entrada, retorna 0.0 si no hay valores válidos, y aplica `_clamp` al resultado.

**Beneficios:**
- El nombre refleja exactamente lo que hace la función.
- Elimina la confusión con algoritmos de media ponderada (weighted average).
- Todos los usos internos del módulo fueron actualizados correctamente.
- Los 114 tests siguen pasando sin cambios.

---

### Mejora 4 — Fixture `acoustic_with_anomalies` sin clave `emergency_audio_indicators`

**Archivos modificados:**
- `tests/conftest.py`

**Problema detectado:**
La fixture `acoustic_with_anomalies` definía un diccionario de features acústicas con anomalías simuladas, pero omitía la clave `emergency_audio_indicators`. Esta clave es accedida por `score_call` en `seriousness_scorer.py` mediante `acoustic.get("emergency_audio_indicators")`. La ausencia de la clave no causaba un error (`.get()` retorna `None` y el código lo maneja), pero producía un comportamiento inconsistente: al usar esta fixture, los indicadores de emergencia nunca serían evaluados aunque el fixture represente un audio con características.

**Solución implementada:**
Se agregó la clave `emergency_audio_indicators` a la fixture, usando los valores que devuelve `empty_emergency_audio_indicators` con todos los scores en `None` y `audio_reliability: 0.0`. Esto representa correctamente un audio cuyos indicadores de emergencia no pudieron derivarse (coherente con las anomalías acústicas severas que simula el fixture).

**Beneficios:**
- La fixture es más representativa de la estructura real del diccionario de features.
- Cualquier test futuro que use `acoustic_with_anomalies` accederá a la clave sin sorpresas.
- Mantiene la semántica original: audio con anomalías pero sin indicadores acústicos de emergencia derivados.

---

## 3. Problemas encontrados sin modificar

### Problema 1 — `_clamp` duplicado en `seriousness_scorer.py` y `emergency_indicators.py`

Ambos módulos definen de forma idéntica:
```python
def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
```

**Razón para no modificar:** Extraer esta función a `src/utils/helpers.py` requeriría actualizar imports en múltiples archivos y podría generar problemas de importaciones circulares si no se hace con cuidado. El riesgo de romper algo supera el beneficio para un MVP. Se recomienda como mejora futura junto con `_optional_float`.

---

### Problema 2 — `_optional_float` duplicado en `seriousness_scorer.py` y `decision_policy.py`

Mismo patrón que el Problema 1. Ambas definiciones son idénticas:
```python
def _optional_float(value: Any) -> float | None:
    return float(value) if value is not None else None
```

**Razón para no modificar:** Misma razón que el Problema 1. Ver recomendaciones futuras (Prioridad Media).

---

### Problema 3 — `AudioAnalysisConfig.f0_min_hz` y `f0_max_hz` son campos muertos

`AudioAnalysisConfig` define `f0_min_hz: float = 70.0` y `f0_max_hz: float = 600.0`, pero ningún módulo del pipeline los usa. El filtro de rango de F0 en `_estimate_f0_stats` usa las constantes de módulo `_SPEECH_F0_MIN_HZ = 70.0` y `_SPEECH_F0_MAX_HZ = 600.0` hardcodeadas directamente.

**Razón para no modificar:** Conectar el config a la función privada requiere cambiar la firma de `_estimate_f0_stats`, lo cual tiene bajo riesgo pero medio esfuerzo. Los valores son iguales en ambos lugares, por lo que no hay divergencia de comportamiento actual.

---

### Problema 4 — `_analysis_window` se invoca 4 veces por llamada

En `extract_acoustic_features`, las funciones `_estimate_tempo`, `_estimate_f0_stats`, `_extract_mfcc_stats` y `_extract_spectral_centroid` llaman cada una a `_analysis_window` internamente. Esto produce hasta 4 truncaciones del mismo audio de hasta 20 segundos.

**Razón para no modificar:** El impacto de rendimiento es bajo (para audios menores a 20 segundos, `_analysis_window` retorna el array original sin copia). Resolver esto requiere cambiar las firmas de las cuatro funciones privadas para aceptar audio pre-truncado, lo cual es una refactorización más extensa. Se recomienda como mejora futura (Prioridad Baja).

---

### Problema 5 — `_analysis_window` ignora `AudioAnalysisConfig.analysis_window_seconds`

`AudioAnalysisConfig` define `analysis_window_seconds: float = 20.0`, pero `_analysis_window` usa el valor hardcodeado `max_seconds=20.0` en sus defaults. Si alguien cambiara el config, el pipeline no lo respetaría.

**Razón para no modificar:** Está relacionado con el Problema 4. Resolver ambos juntos como parte de una refactorización del pipeline de extracción es más seguro que hacerlo de forma parcial.

---

### Problema 6 — Claves redundantes en el JSON de salida

`build_result_payload` en `implementation_report.py` incluye `recommendation` y `evidence` tanto dentro de `score` (como `score.recommendation`, `score.evidence`) como en el nivel raíz del JSON. Esto es redundancia estructural.

**Razón para no modificar:** Cambiar el esquema del JSON rompería la compatibilidad con cualquier consumidor existente (scripts, hojas de cálculo, visualizaciones) que dependan de las claves del nivel raíz. Además, los resultados en `data/outputs/` ya existentes seguirían teniendo el esquema antiguo. Si se desea corregir esto, debe hacerse con una versión del esquema explícita (campo `schema_version`).

---

### Problema 7 — `2do avance.md` en la raíz está desactualizado

El archivo `2do avance.md` en la raíz del proyecto es una versión anterior del README que no menciona MFCCs, indicadores de emergencia acústicos, `emergency_audio_indicators`, ni la suite de tests. El README actual (`README.md`) lo reemplaza completamente.

**Razón para no modificar:** Eliminar archivos de documentación requiere confirmar con el autor que no tiene valor de referencia histórica. Se recomienda eliminarlo o moverlo a `docs/archivo/`.

---

### Problema 8 — Cobertura delgada de `test_emergency_indicators.py`

El módulo `emergency_indicators.py` contiene la heurística más compleja del sistema (8 indicadores compuestos, 9 funciones de scoring, pesos implícitos) y solo tiene 3 tests. Los tests actuales verifican el signo general del score (stress alto → seriousness alta, calma → seriousness baja), pero no cubren:
- Indicadores individuales (`nervousness_score`, `urgency_score`, `aggression_score`, etc.)
- `indicator_flags` de cada indicador
- `_audio_reliability` en distintas condiciones
- El efecto de `audio_reliability < 0.45` sobre `seriousness_audio_score`

**Razón para no modificar:** Agregar tests es trabajo de escritura, no de refactoring. No rompe nada pero es deuda de calidad prioritaria.

---

## 4. Recomendaciones futuras

### Prioridad Alta

**4.1 Ampliar tests de `emergency_indicators.py`**
El módulo es el más complejo y heurístico del sistema. Necesita al menos 15-20 tests adicionales que cubran cada indicador compuesto (urgency, nervousness, aggression, desperation, calm, voice_instability), los umbrales de `indicator_flags`, y el comportamiento de `audio_reliability` en baja calidad. Sin estos tests, los cambios en umbrales no pueden validarse de forma segura.

**4.2 Agregar tests de integración end-to-end**
Actualmente no existe ningún test que ejecute `run_pipeline` completo con un archivo `.wav` sintético generado en memoria (por ejemplo, con `soundfile.write`). Estos tests detectarían regresiones en la integración entre módulos que los tests unitarios no pueden capturar.

**4.3 Extraer `_clamp` y `_optional_float` a `src/utils/helpers.py`**
Eliminar la duplicación de estas funciones privadas en tres módulos distintos. Una vez extraídas, pueden mejorarse con type hints más precisos y documentación centralizada. La implementación requiere:
1. Crear `src/utils/helpers.py` con ambas funciones.
2. Actualizar imports en `seriousness_scorer.py`, `decision_policy.py` y `emergency_indicators.py`.
3. Verificar que no existan ciclos de importación.

**4.4 Conectar `AudioAnalysisConfig.f0_min_hz`/`f0_max_hz` al pipeline**
Los campos existen en el config pero `_estimate_f0_stats` usa constantes hardcodeadas. Conectar el config permite ajustar el rango de F0 sin tocar el código. La solución más limpia es precomputar la ventana de análisis una sola vez en `extract_acoustic_features` y pasarla como parámetro a las cuatro funciones privadas, lo que también resuelve el Problema 4 (llamadas redundantes a `_analysis_window`).

---

### Prioridad Media

**4.5 Versionar el esquema JSON de salida**
Agregar un campo `schema_version: "1.0"` al JSON de salida. Una vez versionado, se puede eliminar la duplicación de `recommendation`/`evidence` en el nivel raíz (Problema 6) de forma controlada pasando a `schema_version: "2.0"`.

**4.6 Eliminar o archivar `2do avance.md`**
Mover el archivo a `docs/archivo/2do_avance_historico.md` para preservar el historial sin contaminar la raíz del proyecto.

**4.7 Configurar `flake8` o `ruff` como linter en CI**
El código es limpio pero sin un linter configurado es fácil introducir imports sin uso, espacios inconsistentes o nombres que no siguen la convención. Ruff es especialmente rápido y reemplaza flake8 + isort + pyupgrade.

---

### Prioridad Baja

**4.8 Agregar `pyproject.toml` con configuración del proyecto**
Centraliza la configuración de herramientas (pytest, ruff, mypy) y facilita futuras integraciones con CI/CD.

**4.9 Agregar type checking estático con `mypy` o `pyright`**
El proyecto usa anotaciones de tipo consistentemente. Agregar un paso de `mypy --strict` detectaría errores de tipo en tiempo de desarrollo.

**4.10 Marcar `2do avance.md` como obsoleto**
Hasta que se pueda eliminar, agregar una nota al inicio del archivo: `> NOTA: Este documento está desactualizado. Ver README.md para la versión actual.`

---

## 5. Posibles nuevas funcionalidades

### 5.1 Interfaz Streamlit para visualización interactiva

**Justificación:** El sistema genera un JSON rico con scores, evidencias, features acústicas e indicadores. Una interfaz en Streamlit permitiría cargar un audio, ver la transcripción, ver los valores acústicos como gráficos (F0 a lo largo del tiempo, energía por tramas, ratio de silencios) y el resultado final con justificación visual. Sería útil para validar el sistema con usuarios operativos antes de integrarlo en producción.

**Herramienta:** `streamlit` (gratuito, local).

---

### 5.2 faster-whisper como motor de ASR

**Justificación:** `faster-whisper` (basado en CTranslate2) es entre 2x y 4x más rápido que `openai-whisper` en CPU con la misma precisión, y consume menos memoria. El módulo `transcriber.py` puede adaptarse con un bloque `try/except` que intente `faster_whisper` primero y caiga al `openai-whisper` como fallback. Esto no requiere cambiar la interfaz pública del módulo ASR.

**Herramienta:** `pip install faster-whisper`.

---

### 5.3 Jitter y shimmer como features de estabilidad vocal

**Justificación:** La metodología base (`METODOLOGIA_BASE.md`, Fase 3) los menciona explícitamente. Jitter mide la variabilidad ciclo-a-ciclo de F0 y shimmer mide la variabilidad de amplitud. Ambos son indicadores clásicos de estrés vocal y nerviosismo. Pueden calcularse sobre el audio con `parselmouth` (interfaz Python de Praat) sin dependencias de pago. Son especialmente útiles como features para los modelos supervisados de la siguiente fase.

**Herramienta:** `pip install praat-parselmouth`.

---

### 5.4 Evaluación automática con métricas (F1, AUROC, Brier Score)

**Justificación:** El sistema actualmente no tiene métricas de evaluación. Una vez que exista un dataset etiquetado (aunque sea pequeño, de 30-50 llamadas simuladas), un script `scripts/evaluate.py` podría ejecutar el pipeline sobre cada audio, comparar la recomendación con la etiqueta real y calcular recall para llamadas serias, precision para improcedentes, F1 y AUROC. El recall alto en llamadas serias es la métrica prioritaria.

---

### 5.5 Exportación de vector de features para entrenamiento de modelos baseline

**Justificación:** Actualmente todas las features se calculan pero no se persisten en formato tabular. Un script `scripts/extract_features.py` que genere un CSV con una fila por llamada y columnas para cada feature acústica y semántica permitiría entrenar modelos clásicos (regresión logística, random forest, SVM) sin modificar el pipeline principal. Esto es el prerequisito de la Fase 6 de la metodología.

---

### 5.6 Detección de múltiples hablantes

**Justificación:** El sistema asume un solo hablante. En llamadas reales puede haber operador + ciudadano, o interferencias. La diarización básica con `pyannote.audio` (gratuita para uso no comercial) permitiría segmentar el audio por hablante y analizar únicamente la voz del ciudadano, mejorando la calidad de los features acústicos.

---

### 5.7 Modo de análisis de segmentos (chunking)

**Justificación:** Para llamadas largas (> 20 segundos), el pipeline actual analiza solo los primeros 20 segundos para los features espectrales. Un modo de análisis por segmentos procesaría el audio en ventanas de 10-20 segundos y agregaría los resultados (percentiles, evolución temporal). Esto es especialmente útil para detectar cambios de comportamiento a lo largo de la llamada (por ejemplo, inicio tranquilo que se vuelve urgente).

---

## 6. Deuda técnica

| # | Componente | Descripción | Impacto |
|---|---|---|---|
| DT-1 | `emergency_indicators.py` | Solo 3 tests para la heurística más compleja del sistema | Alto |
| DT-2 | Helpers duplicados | `_clamp` y `_optional_float` en 3 módulos distintos | Medio |
| DT-3 | Config fields muertos | `f0_min_hz`, `f0_max_hz` en `AudioAnalysisConfig` nunca se usan | Medio |
| DT-4 | `_analysis_window` × 4 | La ventana de análisis se recalcula 4 veces por llamada | Bajo |
| DT-5 | Config no controla ventana | `analysis_window_seconds` definido en config pero ignorado | Bajo |
| DT-6 | JSON redundante | `recommendation` y `evidence` duplicados en nivel raíz | Bajo |
| DT-7 | Sin versión de esquema | No hay campo `schema_version` en el JSON de salida | Bajo |
| DT-8 | `2do avance.md` obsoleto | Documento en raíz desactualizado respecto al README | Bajo |
| DT-9 | Sin tests de integración | Ningún test ejecuta el pipeline completo con audio real o sintético | Alto |
| DT-10 | Sin linter configurado | No hay `ruff`/`flake8` ni `mypy` en el proyecto | Medio |

---

## 7. Riesgos

### R1 — Calibración de umbrales heurísticos sin datos etiquetados (Riesgo Alto)

Los umbrales de energía, silencio, F0, SNR y los pesos de los indicadores acústicos de emergencia son completamente heurísticos. Sin un dataset etiquetado con llamadas reales (seria, dudosa, improcedente) no es posible saber si los umbrales actuales producen recall alto para llamadas serias o generan muchos falsos positivos. Este es el riesgo más importante antes de cualquier uso operativo.

### R2 — Errores de transcripción con modelo tiny de Whisper (Riesgo Alto)

El modelo `tiny` de Whisper es rápido pero comete errores frecuentes con acentos regionales, múltiples voces, bajo SNR o vocabulario especializado. Un error de transcripción puede hacer que `analyze_text` no detecte palabras clave críticas (por ejemplo, "disparo" transcrito como "desparo" o "chispero"), reduciendo el seriousness score de una llamada grave.

### R3 — Sesgo por variante regional del español (Riesgo Medio)

Los vocabularios de palabras clave en `text_analyzer.py` usan términos del español latinoamericano (colonia, delegación, baldazo). Pueden fallar con variantes regionales de México, España, Argentina u otros países según el contexto de despliegue.

### R4 — Dependencia de FFmpeg para audio comprimido (Riesgo Medio)

Para `.mp3` y `.m4a`, `librosa` delega la decodificación a FFmpeg. Si FFmpeg no está instalado o el PATH no lo incluye, la carga de audio fallará con un error descriptivo pero el pipeline continuará en modo solo-texto, degradando silenciosamente la calidad del análisis acústico.

### R5 — Ausencia de anonimización de datos (Riesgo Alto para producción)

El pipeline guarda el JSON de salida con el path completo del archivo de audio como metadato (`input.audio`). Si los audios contienen datos personales o sensibles y los JSONs se almacenan en un sistema compartido, puede haber riesgos de privacidad. El sistema no anonimiza ni cifra los datos de salida.

### R6 — Sobreconfianza operativa (Riesgo Alto)

El score y la recomendación pueden interpretarse erróneamente como definitivos. La nota de seguridad en el JSON (`"safety_note": "Estimacion probabilistica..."`) es el único mecanismo actual de advertencia. Sin una interfaz de usuario que enfatice el carácter probabilístico del resultado, existe riesgo de que operadores usen el score como criterio de cierre.

---

## 8. Próximos pasos recomendados

### Corto plazo (1-2 semanas)

1. **Ampliar tests de `emergency_indicators.py`**: Agregar mínimo 15 tests para cada indicador y para los `indicator_flags`. Prioridad: esta es la heurística más importante y la menos cubierta.

2. **Agregar tests de integración**: Crear `tests/test_integration.py` con un test que genere un `.wav` sintético en memoria con `soundfile`, lo guarde en un directorio temporal y ejecute `run_pipeline` completo, verificando que el JSON de salida tiene la estructura esperada.

3. **Configurar `ruff` como linter**: Agregar `pyproject.toml` con configuración mínima de `ruff` (o `flake8`). Ejecutar una vez para limpiar imports sin uso residuales o inconsistencias de estilo.

4. **Archivar `2do avance.md`**: Mover a `docs/archivo/` y actualizar `.gitignore` si es necesario.

### Mediano plazo (2-6 semanas)

5. **Dataset etiquetado de llamadas simuladas**: Crear al menos 30-50 llamadas simuladas (.txt o .wav) con etiquetas manuales (seria/dudosa/improcedente). Incluso un dataset pequeño permite validar si los umbrales actuales tienen recall aceptable.

6. **Script de evaluación con métricas**: Implementar `scripts/evaluate.py` que ejecute el pipeline sobre el dataset etiquetado y calcule recall, precision, F1 y AUROC.

7. **Conectar `AudioAnalysisConfig` al pipeline de features**: Precomputar la ventana de análisis una sola vez en `extract_acoustic_features` usando `cfg.analysis_window_seconds`, y pasarla a `_estimate_tempo`, `_estimate_f0_stats`, `_extract_mfcc_stats` y `_extract_spectral_centroid`. Esto también conecta `f0_min_hz`/`f0_max_hz` del config al filtro de `_estimate_f0_stats`.

8. **Evaluar faster-whisper**: Medir velocidad y precisión de `faster-whisper` vs `openai-whisper tiny` en el conjunto de audios de prueba. Si el resultado es superior, actualizar `transcriber.py` con soporte para ambos.

### Largo plazo (6+ semanas)

9. **Modelos baseline supervisados**: Con dataset etiquetado disponible, exportar el vector de features acústicas + semánticas a CSV y entrenar regresión logística, random forest y SVM. Comparar métricas contra el sistema heurístico actual. El objetivo es superar el recall del sistema de reglas en llamadas serias.

10. **Interfaz Streamlit**: Implementar una demo visual que permita subir un audio o texto, ver la transcripción, visualizar los features acústicos (energía, F0, silencios como gráfico temporal) y el resultado con justificación. Útil para demostraciones y validación con usuarios operativos.

11. **Versionar esquema JSON y limpiar redundancias**: Agregar `schema_version: "2.0"` y eliminar las claves duplicadas `recommendation`/`evidence` del nivel raíz. Documentar la migración para consumidores existentes.

12. **Jitter y shimmer con parselmouth**: Agregar features de estabilidad vocal como preparación para la fase CNN-LSTM una vez que exista dataset etiquetado suficiente.

---

# Sesión 2026-07-07 — Adopción del modo de mantenimiento evolutivo y resolución de DT-2

## Fecha

2026-07-07

## Objetivo de la sesión

Establecer el modo de trabajo permanente de mantenimiento evolutivo, verificar el estado actual del proyecto, reestructurar este documento como historial técnico con secciones vivas de Roadmap y Deuda Técnica, y resolver la deuda técnica DT-2 (helpers duplicados).

## Archivos modificados

- `src/utils/helpers.py` (nuevo)
- `src/scoring/seriousness_scorer.py`
- `src/scoring/decision_policy.py`
- `src/audio/emergency_indicators.py`
- `tests/test_scoring.py`
- `MEJORAS_PROYECTO.md`

## Cambios implementados

1. **Creación de `src/utils/helpers.py`** con dos funciones compartidas: `clamp01(value)` (restringe al rango [0, 1]) y `optional_float(value)` (convierte a float preservando None).
2. **Eliminación de las copias duplicadas**: `_clamp` y `_optional_float` en `seriousness_scorer.py`, `_optional_float` en `decision_policy.py`, y `_clamp` y `_value` en `emergency_indicators.py` (esta última era una tercera copia de `optional_float` con otro nombre, no detectada en la auditoría anterior).
3. **Actualización de todos los usos** en los tres módulos a los nombres públicos `clamp01` y `optional_float`.
4. **Actualización de `tests/test_scoring.py`** para importar los helpers desde `src.utils.helpers` en lugar de los nombres privados de `seriousness_scorer`.
5. **Reestructuración de este documento** al formato de historial: entradas por sesión con fecha, más las secciones vivas Roadmap Técnico y Deuda Técnica al final.

## Justificación técnica

La auditoría del 2026-07-06 identificó la duplicación como recomendación 4.3 (Prioridad Alta). Existían cinco definiciones para dos funciones en tres módulos, lo que obligaba a mantener sincronizadas copias idénticas y ocultaba que `_value` en `emergency_indicators.py` era la misma función con otro nombre. `src/utils` no importa nada de `scoring` ni `audio`, por lo que la extracción no introduce ciclos de importación.

## Beneficios obtenidos

- Una única fuente de verdad para el clamping y la conversión opcional a float.
- Nombres públicos y descriptivos (`clamp01` deja explícito el rango) en lugar de tres nombres privados distintos para la misma lógica.
- Se elimina la deuda DT-2 del inventario.

## Riesgos detectados

- Riesgo bajo: el cambio es un refactor mecánico sin cambio de comportamiento. Los `replace_all` fueron verificados con grep para descartar corrupción de identificadores similares.

## Validaciones realizadas

- Suite completa: **114 tests pasando** antes y después del cambio.
- Verificación de imports: `import main` y uso directo de `clamp01`/`optional_float` sin errores.
- Smoke test end-to-end: `python main.py --transcript <archivo>` ejecuta el pipeline completo y genera el JSON con la estructura esperada (`escalar_humano` para un guion con términos de alto riesgo).
- `git status` limpio antes de la sesión; directorios temporales de pytest ya cubiertos por `.gitignore`.

## Recomendaciones futuras

- La siguiente prioridad del roadmap es ampliar los tests de `emergency_indicators.py` (DT-1) y agregar tests de integración end-to-end (DT-9), ambas de impacto Alto.
- Al conectar `AudioAnalysisConfig` al pipeline de features (recomendación 4.4 de la sesión anterior), aprovechar para mover el filtro de F0 a los campos del config.

---

## Roadmap Técnico

> Sección viva. Actualizada por última vez: 2026-07-07.

### Corto plazo

- [x] Extraer `_clamp` y `_optional_float` a `src/utils/helpers.py` — **completado 2026-07-07**
- [ ] Ampliar tests de `emergency_indicators.py` (mínimo 15 tests: indicadores individuales, `indicator_flags`, `audio_reliability`) — **siguiente prioridad**
- [ ] Agregar tests de integración end-to-end (`run_pipeline` con `.wav` sintético generado con `soundfile`)
- [ ] Configurar `ruff` como linter con `pyproject.toml`
- [ ] Archivar `2do avance.md` en `docs/archivo/` (requiere confirmación del autor)

### Mediano plazo

- [ ] Dataset etiquetado de 30-50 llamadas simuladas (seria/dudosa/improcedente)
- [ ] Script `scripts/evaluate.py` con recall, precision, F1 y AUROC
- [ ] Conectar `AudioAnalysisConfig` al pipeline de features (ventana de análisis precomputada + `f0_min_hz`/`f0_max_hz`)
- [ ] Evaluar `faster-whisper` como motor ASR alternativo

### Largo plazo

- [ ] Modelos baseline supervisados (regresión logística, random forest, SVM) sobre CSV de features
- [ ] Interfaz Streamlit para visualización interactiva
- [ ] Versionar esquema JSON (`schema_version: "2.0"`) y eliminar claves duplicadas del nivel raíz
- [ ] Jitter y shimmer con `parselmouth`
- [ ] Diarización de hablantes y análisis por segmentos (chunking)

---

## Deuda Técnica

> Sección viva. Actualizada por última vez: 2026-07-07.

### Alta

| ID | Componente | Descripción |
|---|---|---|
| DT-1 | `emergency_indicators.py` | Solo 3 tests para la heurística más compleja del sistema |
| DT-9 | Tests | Ningún test ejecuta el pipeline completo con audio real o sintético |

### Media

| ID | Componente | Descripción |
|---|---|---|
| DT-3 | `AudioAnalysisConfig` | `f0_min_hz`, `f0_max_hz` definidos pero nunca usados |
| DT-10 | Tooling | Sin linter (`ruff`/`flake8`) ni type checker (`mypy`) configurados |

### Baja

| ID | Componente | Descripción |
|---|---|---|
| DT-4 | `acoustic_features.py` | `_analysis_window` se recalcula 4 veces por llamada |
| DT-5 | `AudioAnalysisConfig` | `analysis_window_seconds` definido en config pero ignorado |
| DT-6 | JSON de salida | `recommendation` y `evidence` duplicados en nivel raíz |
| DT-7 | JSON de salida | Sin campo `schema_version` |
| DT-8 | Documentación | `2do avance.md` obsoleto en la raíz |

### Resueltas

| ID | Descripción | Resuelta en |
|---|---|---|
| DT-2 | `_clamp` y `_optional_float` duplicados en 3 módulos (5 definiciones) | 2026-07-07 |
