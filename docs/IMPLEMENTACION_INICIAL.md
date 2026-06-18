# Implementación inicial del subagente de seriedad de llamadas

## 1. Resumen de implementación

Se implementó un MVP offline/local en Python que recibe una transcripción manual o un archivo de audio, genera análisis acústico cuando las dependencias están disponibles, analiza el texto con reglas semánticas y produce un score probabilístico con recomendación operativa.

El sistema conserva la regla de seguridad principal: no cierra llamadas ni afirma que una llamada sea falsa; solo estima seriedad e improcedencia bajo incertidumbre.

## 2. Componentes implementados

- CLI en `main.py` con soporte para `--audio` y `--transcript`.
- Validación de archivos de audio `.wav`, `.mp3` y `.m4a`.
- Fallback de transcripción manual desde `.txt`.
- Integración opcional con Whisper local si está instalado.
- Extracción acústica básica: duración, energía RMS, variación de energía, amplitud pico, zero crossing rate, silencio, pausas aproximadas, F0 estimado y calidad aproximada.
- Análisis semántico por reglas: palabras de emergencia, palabras de broma, ubicación, personas afectadas, tipo de incidente y completitud informativa.
- Análisis de intención básico.
- Análisis de coherencia con evasivas, contradicciones simples y cambios de tema.
- Score probabilístico de seriedad, improcedencia y confianza.
- Política de decisión conservadora con recomendaciones: `continuar`, `pedir_mas_informacion`, `escalar_humano` y `posible_improcedente`.
- Exportación JSON en `data/outputs/resultado_<fecha>.json`.

## 3. Componentes parcialmente implementados

- ASR: se soporta Whisper local si está instalado, pero no se empaqueta como dependencia obligatoria.
- F0: se estima con `librosa.pyin` cuando es viable; si falla, queda como `null`.
- Ritmo de habla: se aproxima con palabras por minuto cuando existe audio y transcripción.
- VAD: se implementó una estimación simple por energía, no un detector neuronal.
- Coherencia: se implementaron reglas simples, no un modelo conversacional avanzado.
- Calidad de audio: se estima con reglas sobre energía, silencio, saturación y duración.

## 4. Componentes no implementados todavía

- Telefonía real, Twilio, SIP, WebRTC o streaming en tiempo real.
- Cierre automático de llamadas.
- Entrenamiento supervisado con dataset etiquetado.
- Modelo CNN-LSTM-MLP.
- Dashboard en Streamlit o Gradio.
- Evaluación formal con métricas.
- Anonimización automática de datos sensibles.
- Integración con un agente principal externo.

## 5. Estructura final del proyecto

```text
subagente_seriedad/
├── README.md
├── requirements.txt
├── .env.example
├── main.py
├── data/
│   ├── audios/
│   │   └── ejemplo.txt
│   └── outputs/
├── src/
│   ├── audio/
│   │   ├── preprocessing.py
│   │   ├── acoustic_features.py
│   │   └── vad.py
│   ├── asr/
│   │   └── transcriber.py
│   ├── semantic/
│   │   ├── text_analyzer.py
│   │   ├── intent_analyzer.py
│   │   └── coherence_analyzer.py
│   ├── scoring/
│   │   ├── seriousness_scorer.py
│   │   └── decision_policy.py
│   ├── utils/
│   │   ├── config.py
│   │   └── logger.py
│   └── report/
│       └── implementation_report.py
└── docs/
    ├── METODOLOGIA_BASE.md
    └── IMPLEMENTACION_INICIAL.md
```

## 6. Dependencias utilizadas

Dependencias base:

- `numpy`
- `scipy`
- `soundfile`
- `librosa`

Dependencia opcional:

- `openai-whisper`

El modo `--transcript` puede ejecutarse sin Whisper y sin GPU.

## 7. Modo de ejecución

Desde la carpeta del proyecto:

```bash
python main.py --transcript data/audios/ejemplo.txt
```

Con audio:

```bash
python main.py --audio data/audios/ejemplo.wav
```

Si Whisper no está instalado y se usa `--audio`, el sistema intentará extraer features acústicas y registrará que la transcripción requiere fallback manual.

## 8. Ejemplo de entrada y salida

Entrada de texto:

```text
Necesito ayuda urgente. Hay un choque en la avenida Reforma numero 120, cerca de la escuela. Una persona esta herida y necesitamos una ambulancia.
```

Salida resumida esperada:

```json
{
  "seriousness_score": 1.0,
  "improcedence_score": 0.0,
  "confidence": 0.75,
  "recommendation": "escalar_humano",
  "evidence": [
    "Se detectaron terminos de alto riesgo; se prioriza seguridad."
  ]
}
```

Los valores exactos pueden cambiar si se agregan audio, pausas o nuevas reglas.

## 9. Limitaciones actuales

- Es un sistema basado en heurísticas, no un clasificador entrenado.
- Puede producir falsos positivos o falsos negativos.
- Las reglas de ubicación, incidente y personas afectadas son simples.
- La detección de contradicciones es limitada.
- El análisis acústico depende de la calidad del archivo y de dependencias locales.
- No existe calibración estadística de probabilidades.
- No debe utilizarse como mecanismo único para descartar llamadas.

## 10. Próximos pasos recomendados

- Definir taxonomía formal de etiquetas: seria, dudosa, improcedente.
- Crear dataset inicial con audios anonimizados y transcripciones revisadas.
- Medir recall para llamadas serias como métrica prioritaria.
- Agregar pruebas unitarias para reglas semánticas y política de decisión.
- Implementar modelos baseline con scikit-learn.
- Evaluar `faster-whisper` para ASR local eficiente.
- Agregar reporte de auditoría por llamada y versionado de reglas.
- Construir una interfaz local con Streamlit cuando el flujo CLI esté validado.

## 11. Relación con la metodología original

La implementación cubre las fases iniciales de la metodología: alcance conservador, procesamiento offline, rama acústica básica, rama semántica por reglas, fusión heurística, score probabilístico y política de decisión.

Quedan fuera las fases avanzadas: telefonía en tiempo real, modelos entrenados, evaluación formal, dashboard, integración con agente principal y arquitectura CNN-LSTM-MLP. Estas partes requieren dataset, validación ética, métricas y pruebas operativas antes de pasar a producción.
