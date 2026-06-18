# Subagente de seriedad de llamadas

MVP local en Python para estimar de forma probabilistica la seriedad de una llamada a partir de audio y/o transcripcion. El sistema combina senales acusticas basicas, analisis semantico por reglas y una politica operativa conservadora.

El resultado no es una verdad absoluta ni una decision automatica de cierre. La salida sirve como apoyo para continuar, pedir mas informacion, escalar a humano o marcar posible improcedencia.

## Instalacion

```bash
cd subagente_seriedad
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Whisper local es opcional. Si desea transcripcion automatica desde audio:

```bash
pip install openai-whisper
```

Si Whisper no esta instalado, use el modo con transcripcion manual:

```bash
python main.py --transcript data/audios/ejemplo.txt
```

## Uso

Con audio:

```bash
python main.py --audio data/audios/ejemplo.wav
```

Con transcripcion manual:

```bash
python main.py --transcript data/audios/ejemplo.txt
```

Los resultados se guardan en:

```text
data/outputs/resultado_<fecha>.json
```

## Estructura

```text
subagente_seriedad/
├── README.md
├── requirements.txt
├── .env.example
├── main.py
├── data/
│   ├── audios/
│   └── outputs/
├── src/
│   ├── audio/
│   ├── asr/
│   ├── semantic/
│   ├── scoring/
│   ├── utils/
│   └── report/
└── docs/
    ├── METODOLOGIA_BASE.md
    └── IMPLEMENTACION_INICIAL.md
```

## Salida principal

El campo `score` tiene esta forma:

```json
{
  "seriousness_score": 0.0,
  "improcedence_score": 0.0,
  "confidence": 0.0,
  "recommendation": "continuar | pedir_mas_informacion | escalar_humano | posible_improcedente",
  "evidence": []
}
```

## Limitaciones actuales

- No hay telefonia real, SIP, Twilio ni WebRTC.
- No se cierran llamadas automaticamente.
- No hay entrenamiento de CNN-LSTM ni modelo supervisado.
- El ASR depende de Whisper local si se usa `--audio`; si no esta instalado, use `--transcript`.
- Las reglas semanticas son heuristicas iniciales y deben calibrarse con datos reales.
- Las features acusticas son basicas y pueden fallar con audio de mala calidad.

## Siguientes pasos

- Construir un dataset etiquetado y criterios de anotacion.
- Validar las reglas con llamadas simuladas y reales anonimizadas.
- Agregar evaluacion con precision, recall para llamadas serias, F1 y matriz de confusion.
- Probar `faster-whisper` como alternativa de ASR local.
- Entrenar modelos baseline clasicos antes de considerar deep learning.
