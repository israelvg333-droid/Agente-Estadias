# Subagente de seriedad de llamadas

MVP local en Python para estimar de forma probabilistica la seriedad de una llamada a partir de audio y/o transcripcion. El foco actual es audio-first: la transcripcion se usa como apoyo, no como eje principal. El sistema combina:

- Transcripcion local con Whisper, si esta instalado.
- Extraccion acustica con `librosa` y `numpy` (energia, F0, silencios, pausas, MFCCs, centroide espectral, SNR y mas).
- Indicadores paralinguisticos explicables para llamadas de emergencia: stress vocal, urgencia, nerviosismo, desesperacion, calma, agresividad acustica, inestabilidad vocal y confiabilidad del audio.
- Analisis semantico por reglas (palabras clave, completitud, deteccion de intencion).
- Analisis de coherencia (evasivas, contradicciones, cambios de tema).
- Politica de decision conservadora.

El resultado es una ayuda operativa. No debe usarse para cerrar llamadas automaticamente ni para afirmar que una llamada es falsa.

---

## Instalacion

Desde Windows PowerShell:

```powershell
cd "C:\ruta\al\proyecto\subagente_seriedad"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Whisper local es opcional, pero necesario para transcribir audio automaticamente:

```powershell
pip install openai-whisper
```

Para `.mp3` y `.m4a`, `librosa` puede requerir que FFmpeg este disponible en el sistema.

---

## Uso

### Con audio (requiere Whisper instalado)

```powershell
python main.py --audio data\audios\ejemplo.wav
python main.py --audio data\audios\ejemplo.mp3 --model base
```

Modelos de Whisper disponibles:

| Modelo | Velocidad | Precision |
|--------|-----------|-----------|
| `tiny` | Alta      | Basica    |
| `base` | Media     | Buena     |
| `small`| Baja      | Alta      |

### Con transcripcion manual (sin Whisper)

```powershell
python main.py --transcript data\audios\ejemplo.txt
```

En modo transcript-only, `acoustic_features` se genera con valores `null` pero incluye `word_count_from_transcript`.

---

## Resultados

Los resultados se guardan en:

```text
data/outputs/resultado_<fecha>.json
```

### Estructura del JSON

```json
{
  "generated_at": "2026-06-29T12:00:00",
  "input": {},
  "transcription": {},
  "acoustic_features": {
    "duration_seconds": null,
    "mfcc_mean": null,
    "mfcc_std": null,
    "spectral_centroid_hz": null,
    "word_count_from_transcript": 24,
    "acoustic_anomaly_flags": []
  },
  "semantic_analysis": {},
  "intent_analysis": {},
  "coherence_analysis": {},
  "score": {
    "seriousness_score": 0.0,
    "improcedence_score": 0.0,
    "confidence": 0.0,
    "recommendation": "continuar | pedir_mas_informacion | escalar_humano | posible_improcedente",
    "evidence": [],
    "audio_priority": {},
    "safety_note": "..."
  },
  "recommendation": "...",
  "evidence": []
}
```

### Recomendaciones posibles

| Recomendacion           | Cuando se aplica                                         |
|-------------------------|----------------------------------------------------------|
| `escalar_humano`        | Terminos de alto riesgo detectados                       |
| `continuar`             | Incidente + ubicacion + coherencia suficiente            |
| `pedir_mas_informacion` | Informacion incompleta o confianza baja                  |
| `posible_improcedente`  | Broma detectada o anomalias multiples sin riesgo critico |

### Reglas de seguridad

- Nunca recomienda colgar.
- Si la confianza es baja, recomienda `pedir_mas_informacion`.
- Si hay terminos criticos (arma, disparo, incendio, etc.), recomienda `escalar_humano`.

---

## Pruebas

```powershell
pip install pytest
python -m pytest tests/ -v
```

Los tests cubren:

- `test_text_analyzer.py`: normalizacion, palabras clave, completitud
- `test_coherence_analyzer.py`: evasivas, contradicciones, cambios de tema
- `test_decision_policy.py`: todas las rutas de la politica de decision
- `test_scoring.py`: calculo de scores, confianza, recomendaciones
- `test_vad.py`: deteccion de silencios y pausas
- `test_acoustic_features.py`: features acusticas, clipping, SNR, MFCCs
- `test_preprocessing.py`: validacion de rutas y normalizacion de audio

---

## Features acusticas extraidas

Cuando hay audio disponible se extraen:

| Feature                   | Descripcion                                          |
|---------------------------|------------------------------------------------------|
| `duration_seconds`        | Duracion del audio                                   |
| `rms_energy`              | Energia RMS global                                   |
| `mean_energy`             | Energia promedio por trama                           |
| `max_energy`              | Energia maxima por trama                             |
| `energy_std`              | Desviacion de energia                                |
| `zero_crossing_rate`      | Tasa de cruces por cero                              |
| `estimated_f0_hz`         | Frecuencia fundamental media (rango voz: 70-600 Hz) |
| `mfcc_mean`               | Media de cada uno de los 13 primeros MFCCs           |
| `mfcc_std`                | Desviacion de cada MFCC                              |
| `spectral_centroid_hz`    | Centroide espectral medio (brillo tonal)             |
| `silence_ratio`           | Proporcion de silencio                               |
| `pause_count`             | Numero de pausas detectadas                          |
| `estimated_snr_db`        | SNR aproximado en dB                                 |
| `audio_quality`           | Calidad estimada del audio                           |
| `clipping_ratio`          | Proporcion de muestras con clipping                  |
| `acoustic_anomaly_flags`  | Lista de anomalias detectadas                        |
| `approx_speech_rate`      | Velocidad de habla aproximada (palabras/minuto)      |
| `word_count_from_transcript` | Palabras contadas desde la transcripcion          |

### Indicadores acusticos de emergencia

`acoustic_features.emergency_audio_indicators` agrega una capa de inferencia explicable basada en prosodia, energia, pausas, F0, ritmo y calidad del audio:

| Indicador | Uso |
|-----------|-----|
| `stress_vocal_score` | Variabilidad de energia, F0 y pitch asociada a activacion vocal |
| `urgency_score` | Ritmo de habla, intensidad y baja proporcion de silencio |
| `nervousness_score` | F0 variable, pausas, ZCR e inestabilidad temporal |
| `desperation_score` | Combinacion de stress, urgencia y rango de F0 |
| `calm_score` | Evidencia acustica de baja activacion |
| `aggression_score` | Energia alta, centroide espectral y ZCR elevados |
| `voice_instability_score` | Variacion de F0 y energia |
| `audio_reliability` | Confiabilidad de los indicadores segun calidad, SNR, clipping y silencio |
| `seriousness_audio_score` | Estimacion acustica primaria para alimentar el score final |

---

## Estructura del proyecto

```text
subagente_seriedad/
├── main.py
├── requirements.txt
├── README.md
├── data/
│   ├── audios/
│   └── outputs/
├── docs/
│   ├── METODOLOGIA_BASE.md
│   ├── IMPLEMENTACION_INICIAL.md
│   ├── CAMBIOS_MULTIMODAL.md
│   └── Implementacion_20260629.md
├── tests/
│   ├── conftest.py
│   ├── test_text_analyzer.py
│   ├── test_coherence_analyzer.py
│   ├── test_decision_policy.py
│   ├── test_scoring.py
│   ├── test_vad.py
│   ├── test_acoustic_features.py
│   └── test_preprocessing.py
└── src/
    ├── audio/
    │   ├── preprocessing.py
    │   ├── acoustic_features.py
    │   └── vad.py
    ├── asr/
    │   └── transcriber.py
    ├── semantic/
    │   ├── text_analyzer.py
    │   ├── intent_analyzer.py
    │   └── coherence_analyzer.py
    ├── scoring/
    │   ├── seriousness_scorer.py
    │   └── decision_policy.py
    ├── report/
    │   └── implementation_report.py
    └── utils/
        ├── config.py
        └── logger.py
```

---

## Limitaciones actuales

- No hay telefonia real, SIP, Twilio, WebRTC ni streaming.
- No se cierran llamadas automaticamente.
- No hay entrenamiento de CNN-LSTM ni modelo supervisado.
- Los indicadores acusticos nuevos son heuristicas auditables, no un modelo SER calibrado.
- Whisper en CPU puede ser lento, especialmente con `base` y `small`.
- Las probabilidades son heuristicas, no estan calibradas estadisticamente.
- La deteccion de F0, tempo, SNR y silencios puede fallar con ruido, musica, multiples voces o mala codificacion.
- Las reglas semanticas requieren validacion con datos reales anonimizados.
- Para `.mp3` y `.m4a`, la carga depende del soporte local de decodificacion (FFmpeg).

---

## Proximos pasos recomendados

1. Construir un dataset etiquetado con llamadas simuladas y anonimizadas.
2. Validar umbrales acusticos con audios reales.
3. Agregar evaluacion con precision, recall, F1 y matriz de confusion.
4. Probar `faster-whisper` como alternativa de ASR local mas eficiente.
5. Evaluar openSMILE/eGeMAPS y ComParE como extractor estandarizado de SER.
6. Entrenar modelos baseline clasicos (logistic regression, random forest) antes de considerar CNN-LSTM.
7. Evaluar embeddings wav2vec 2.0, HuBERT, WavLM o SpeechBrain cuando exista dataset etiquetado.
8. Agregar interfaz de visualizacion con Streamlit.
