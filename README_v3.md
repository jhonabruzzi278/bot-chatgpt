# 🤖 Chat Bot (OpenAI) - Minimalista

Bot de Telegram simplificado que usa la API de OpenAI para chatear en español. Se eliminaron todas las funciones de procesamiento de fotos, watcher y base de datos; todo se maneja en memoria durante la ejecución.

## ✨ Características

- 💬 Chat directo con OpenAI (modelo configurable)
- 🧠 Contexto por usuario en memoria (se reinicia con `/reset`)
- 🔘 **Menú de botones interactivo** para acceso rápido
- 🧾 Configuración simple vía `.env`

## 🏗️ Estructura

```
foto-bot/
├── bot.py                # Punto de entrada del bot (chat)
├── config/
│   └── settings.py       # Configuración: tokens y modelo
├── requirements.txt      # Dependencias mínimas
└── logs/                 # Logs
```

## 🚀 Instalación y Configuración

### 1. Clonar y preparar el entorno

```powershell
git clone <repo>
cd foto-bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear archivo `.env` en la raíz:

```env
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
OPENAI_API_KEY=tu_api_key_de_openai
# Opcionales
OPENAI_MODEL=gpt-4o-mini
SYSTEM_PROMPT=Eres un asistente útil en español. Responde de forma breve.
AUTHORIZED_USER_IDS=tu_user_id
```

### 3. Ejecutar el bot

```powershell
python .\bot.py
```

## 📋 Comandos

| Comando | Descripción |
|---------|-------------|
| `/start` | Presentación y arranque del contexto |
| `/reset` | Limpia el contexto del chat para el usuario |
| `/help` | Muestra ayuda detallada |
| `/stats` | Estadísticas de uso personal y global |

### 🔘 Botones Interactivos

El bot incluye un **teclado personalizado** con botones para acceso rápido:

- **🆘 Ayuda** - Muestra información completa del bot
- **📊 Estadísticas** - Ver uso personal y estadísticas globales  
- **🔄 Resetear Chat** - Limpia toda la conversación actual
- **💬 Chat Libre** - Activa modo conversación continua

> Los botones aparecen automáticamente al escribir `/start`

## 🔧 Configuración Avanzada

Variables opcionales en `.env`:

```env
# Control de acceso (opcional - IDs separados por coma)
AUTHORIZED_USER_IDS=123456789,987654321

# Configuración del modelo
MAX_TOKENS=300
TEMPERATURE=0.3
MAX_HISTORY_MESSAGES=20
LOG_LEVEL=INFO
```

## 🔧 Notas

- El contexto por usuario se guarda solo en memoria (se pierde al reiniciar).
- Puedes ajustar el `SYSTEM_PROMPT` en `.env` para personalizar el tono del bot.

## 🆘 Soporte

1. Verifica las variables en `.env`.
2. Revisa la consola para mensajes de error.
3. Asegúrate de tener Python 3.10+ y las dependencias instaladas.
