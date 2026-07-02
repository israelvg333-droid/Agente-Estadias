# Subagente de seriedad de llamadas

MVP local en Python para estimar de forma probabilistica la seriedad de una llamada a partir de audio y/o transcripcion. El sistema combina:

- Transcripcion local con Whisper, si esta instalado.
- Extraccion acustica con `librosa`, `numpy` y `scipy`.
- Analisis semantico por reglas.
- Analisis de coherencia.
- Politica de decision conservadora.

El resultado es una ayuda operativa. No debe usarse para cerrar llamadas automaticamente ni para afirmar que una llamada es falsa.

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

## Ejecutar con audio

```powershell
python main.py --audio data\audios\1757078926.92210.mp3
```

Tambien puede seleccionar el modelo de Whisper:

```powershell
python main.py --audio data\audios\1757078926.92210.mp3 --model tiny
python main.py --audio data\audios\archivo.wav --model base
python main.py --audio data\audios\archivo.m4a --model small
```

Modelos soportados por el CLI:

- `tiny`: mas rapido, menor precision.
- `base`: balance inicial.
- `small`: mejor transcripcion, mas lento en CPU.

## Ejecutar con transcript

Si no desea usar Whisper o no hay audio disponible:

```powershell
python main.py --transcript data\audios\ejemplo.txt
```

En modo transcript-only, la seccion `acoustic_features` se genera con valores `null` y una nota de que no hubo audio.

## JSON de salida

Los resultados se guardan en:

```text
data/outputs/resultado_<fecha>.json
```

Estructura principal:

```json
{
  "generated_at": "2026-06-23T13:49:46",
  "input": {},
  "transcription": {},
  "acoustic_features": {},
  "semantic_analysis": {},
  "intent_analysis": {},
  "coherence_analysis": {},
  "score": {
    "seriousness_score": 0.0,
    "improcedence_score": 0.0,
    "confidence": 0.0,
    "recommendation": "continuar | pedir_mas_informacion | escalar_humano | posible_improcedente",
    "evidence": []
  },
  "recommendation": "...",
  "evidence": []
}
```

La seccion `acoustic_features` incluye, cuando el audio puede cargarse:

- `duration_seconds`
- `rms_energy`, `mean_energy`, `max_energy`, `energy_std`
- `peak_amplitude`
- `zero_crossing_rate`
- `estimated_tempo_bpm`
- `silence_ratio`
- `pause_count`
- `mean_pause_seconds`
- `longest_pause_seconds`
- `estimated_f0_hz`, `estimated_f0_min_hz`, `estimated_f0_max_hz`
- `audio_quality`
- `clipping_ratio`
- `estimated_snr_db`
- `acoustic_anomaly_flags`
- `approx_speech_rate`

## Recomendaciones

El sistema puede devolver:

- `continuar`
- `pedir_mas_informacion`
- `escalar_humano`
- `posible_improcedente`

Reglas de seguridad:

- Nunca recomienda colgar.
- Si la confianza es baja, recomienda `pedir_mas_informacion`.
- Si hay terminos criticos, recomienda `escalar_humano`.
- Si hay baja coherencia, baja completitud y senales acusticas anomalas, puede recomendar `posible_improcedente`.

## Estructura

```text
subagente_seriedad/
|-- main.py
|-- requirements.txt
|-- README.md
|-- data/
|   |-- audios/
|   `-- outputs/
|-- docs/
|   |-- IMPLEMENTACION_INICIAL.md
|   |-- METODOLOGIA_BASE.md
|   `-- CAMBIOS_MULTIMODAL.md
`-- src/
    |-- audio/
    |-- asr/
    |-- semantic/
    |-- scoring/
    |-- report/
    `-- utils/
```

## Limitaciones actuales

- No hay telefonia real, SIP, Twilio, WebRTC ni streaming.
- No se cierran llamadas automaticamente.
- No hay entrenamiento de CNN-LSTM ni modelo supervisado.
- Whisper en CPU puede ser lento, especialmente con `base` y `small`.
- Las probabilidades son heuristicas, no estan calibradas estadisticamente.
- La deteccion de F0, tempo, SNR y silencios puede fallar con ruido, musica, multiples voces o mala codificacion.
- Las reglas semanticas requieren validacion con datos reales anonimizados.
- Para `.mp3` y `.m4a`, la carga depende del soporte local de decodificacion.
