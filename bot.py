#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot de chat con OpenAI (solo texto). Proyecto simplificado.
"""

import logging
from typing import Dict, List
import asyncio
from time import sleep

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ChatAction
from telegram.error import NetworkError, RetryAfter, TimedOut, BadRequest

from config.settings import (
    ensure_config, TELEGRAM_BOT_TOKEN, LOG_FORMAT, LOG_LEVEL,
    OPENAI_API_KEY, OPENAI_MODEL, SYSTEM_PROMPT, MAX_TOKENS, 
    TEMPERATURE, MAX_HISTORY_MESSAGES, is_user_authorized
)

from openai import OpenAI
import openai

# Configurar logging
logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger("chat-bot")

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Memoria de conversación en RAM por usuario
conversations: Dict[int, List[dict]] = {}

# Configuración personalizada por usuario
user_configs: Dict[int, Dict] = {}

# Modos de respuesta disponibles
RESPONSE_MODES = {
    "🤖 Formal": "Responde de manera profesional, formal y estructurada.",
    "😊 Casual": "Responde de forma amigable, relajada y conversacional.",
    "🎓 Académico": "Proporciona explicaciones detalladas, precisas y educativas.",
    "⚡ Conciso": "Responde de forma breve, directa y al punto."
}

def get_user_config(user_id: int) -> Dict:
    """Obtiene la configuración personalizada del usuario."""
    if user_id not in user_configs:
        user_configs[user_id] = {
            "mode": "😊 Casual",
            "temperature": TEMPERATURE,
            "model": OPENAI_MODEL,
            "max_tokens": MAX_TOKENS
        }
    return user_configs[user_id]

def get_system_prompt(user_id: int) -> str:
    """Genera el system prompt personalizado según el modo del usuario."""
    config = get_user_config(user_id)
    mode = config["mode"]
    
    base_prompt = SYSTEM_PROMPT
    mode_instruction = RESPONSE_MODES.get(mode, RESPONSE_MODES["😊 Casual"])
    
    return f"{base_prompt} {mode_instruction}"

def get_main_keyboard():
    """Crea el teclado principal con botones de comandos."""
    keyboard = [
        [KeyboardButton("🆘 Ayuda"), KeyboardButton("📊 Estadísticas")],
        [KeyboardButton("🔄 Resetear Chat"), KeyboardButton("💬 Chat Libre")],
        [KeyboardButton("🎭 Cambiar Modo"), KeyboardButton("⚙️ Configuración")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_mode_keyboard():
    """Crea el teclado para seleccionar modo de respuesta."""
    keyboard = [
        [KeyboardButton("🤖 Formal"), KeyboardButton("😊 Casual")],
        [KeyboardButton("🎓 Académico"), KeyboardButton("⚡ Conciso")],
        [KeyboardButton("🔙 Volver")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_config_keyboard():
    """Crea el teclado para configuración."""
    keyboard = [
        [KeyboardButton("🌡️ Temperatura"), KeyboardButton("🧠 Modelo")],
        [KeyboardButton("📏 Tokens"), KeyboardButton("📋 Ver Config")],
        [KeyboardButton("🔙 Volver")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_temperature_keyboard():
    """Crea el teclado para seleccionar temperatura."""
    keyboard = [
        [KeyboardButton("🔥 0.1"), KeyboardButton("🌡️ 0.5"), KeyboardButton("🌡️ 0.7")],
        [KeyboardButton("🌡️ 1.0"), KeyboardButton("🌡️ 1.5"), KeyboardButton("🔥 2.0")],
        [KeyboardButton("🔙 Volver Config")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_model_keyboard():
    """Crea el teclado para seleccionar modelo."""
    keyboard = [
        [KeyboardButton("🧠 gpt-4o"), KeyboardButton("⚡ gpt-4o-mini")],
        [KeyboardButton("🔙 Volver Config")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_tokens_keyboard():
    """Crea el teclado para seleccionar tokens."""
    keyboard = [
        [KeyboardButton("📏 500"), KeyboardButton("📏 1000")],
        [KeyboardButton("📏 2000"), KeyboardButton("📏 4000")],
        [KeyboardButton("🔙 Volver Config")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# ============================================================================
# FUNCIONES DE MANEJO DE ERRORES
# ============================================================================

def validate_user_config(config: dict) -> tuple[bool, str]:
    """Valida la configuración del usuario."""
    try:
        # Validar temperatura
        if not (0.0 <= config.get("temperature", 0.7) <= 2.0):
            return False, "❌ La temperatura debe estar entre 0.0 y 2.0"
        
        # Validar modelo
        valid_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
        if config.get("model") not in valid_models:
            return False, f"❌ Modelo no válido. Usa: {', '.join(valid_models)}"
        
        # Validar tokens
        if not (50 <= config.get("max_tokens", 500) <= 4000):
            return False, "❌ Los tokens deben estar entre 50 y 4000"
        
        # Validar modo
        if config.get("mode") not in RESPONSE_MODES:
            return False, "❌ Modo de respuesta no válido"
        
        return True, "✅ Configuración válida"
    except Exception as e:
        return False, f"❌ Error validando configuración: {str(e)}"

async def handle_openai_error(error: Exception, user_id: int) -> str:
    """Maneja errores específicos de OpenAI y devuelve un mensaje amigable."""
    error_msg = str(error).lower()
    
    # Rate limiting
    if "rate limit" in error_msg or "too many requests" in error_msg:
        logger.warning(f"Rate limit para usuario {user_id}: {error}")
        return "⏳ **Límite de uso alcanzado**\n\nEspera unos segundos antes de enviar otro mensaje.\n\n💡 Tip: Intenta reducir la frecuencia de mensajes."
    
    # Problemas de conexión
    if any(keyword in error_msg for keyword in ["connection", "timeout", "network"]):
        logger.warning(f"Problema de conexión para usuario {user_id}: {error}")
        return "🌐 **Error de conexión**\n\nHay problemas temporales de conexión con la IA.\n\n🔄 Intenta nuevamente en unos momentos."
    
    # Contexto muy largo
    if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
        logger.info(f"Contexto excedido para usuario {user_id}, limpiando historial")
        reset_history(user_id)
        return "📚 **Conversación muy larga**\n\nHe limpiado el historial para continuar.\n\n✨ Puedes repetir tu última pregunta."
    
    # Token inválido o problemas de autenticación
    if any(keyword in error_msg for keyword in ["authentication", "api key", "unauthorized"]):
        logger.error(f"Error de autenticación OpenAI para usuario {user_id}: {error}")
        return "🔐 **Error de configuración**\n\nHay un problema con la configuración del bot.\n\n👨‍💻 Contacta al administrador."
    
    # Contenido bloqueado
    if any(keyword in error_msg for keyword in ["content_filter", "policy", "safety"]):
        logger.warning(f"Contenido bloqueado para usuario {user_id}: {error}")
        return "🛡️ **Contenido no permitido**\n\nTu mensaje no cumple con las políticas de uso.\n\n💭 Intenta reformular tu pregunta de manera diferente."
    
    # Error genérico
    logger.error(f"Error OpenAI no identificado para usuario {user_id}: {error}")
    return "🤖 **Error temporal de IA**\n\nHubo un problema técnico inesperado.\n\n🔄 Intenta nuevamente o usa /reset para empezar de nuevo."

async def safe_send_message(update: Update, message: str, reply_markup=None, max_retries: int = 3):
    """Envía mensajes de forma segura con reintentos automáticos."""
    for attempt in range(max_retries):
        try:
            await update.message.reply_text(
                message, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return True
        except RetryAfter as e:
            if attempt < max_retries - 1:
                logger.warning(f"Rate limit Telegram, esperando {e.retry_after} segundos...")
                await asyncio.sleep(e.retry_after)
            else:
                logger.error(f"Rate limit Telegram agotado después de {max_retries} intentos")
        except BadRequest as e:
            if "can't parse" in str(e).lower():
                # Intenta enviar sin Markdown
                try:
                    await update.message.reply_text(message, reply_markup=reply_markup)
                    return True
                except Exception:
                    pass
            logger.error(f"BadRequest en Telegram: {e}")
        except (NetworkError, TimedOut) as e:
            if attempt < max_retries - 1:
                logger.warning(f"Error de red Telegram, reintentando... ({attempt + 1}/{max_retries})")
                await asyncio.sleep(2 ** attempt)  # Backoff exponencial
            else:
                logger.error(f"Error de red Telegram agotado: {e}")
        except Exception as e:
            logger.error(f"Error inesperado enviando mensaje: {e}")
            break
    
    # Si llegamos aquí, falló todos los intentos
    try:
        # Intento final sin markdown ni teclado
        await update.message.reply_text("❌ Error enviando respuesta. Intenta nuevamente.")
    except Exception:
        logger.error("No se pudo enviar ni el mensaje de error")
    return False

def get_history(user_id: int) -> List[dict]:
    if user_id not in conversations:
        conversations[user_id] = [{"role": "system", "content": get_system_prompt(user_id)}]
    return conversations[user_id]

def reset_history(user_id: int):
    conversations[user_id] = [{"role": "system", "content": get_system_prompt(user_id)}]

def update_system_prompt(user_id: int):
    """Actualiza el system prompt cuando cambia el modo."""
    if user_id in conversations:
        history = conversations[user_id]
        if history and history[0]["role"] == "system":
            history[0]["content"] = get_system_prompt(user_id)

def trim_history(history: List[dict]) -> List[dict]:
    """Mantiene solo los últimos N mensajes para evitar exceder límites de tokens."""
    if len(history) <= MAX_HISTORY_MESSAGES:
        return history
    
    # Mantener el system prompt + últimos mensajes
    system_msg = history[0] if history and history[0]["role"] == "system" else None
    recent_messages = history[-(MAX_HISTORY_MESSAGES-1):] if system_msg else history[-MAX_HISTORY_MESSAGES:]
    
    if system_msg:
        return [system_msg] + recent_messages
    return recent_messages

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Verificar autorización
    if not is_user_authorized(user.id):
        await safe_send_message(
            update,
            f"❌ **No autorizado**\n\nTu ID de usuario es: `{user.id}`\n\n👨‍💻 Contacta al administrador para obtener acceso."
        )
        logger.warning(f"Usuario no autorizado intentó usar el bot: {user.id} (@{user.username})")
        return
    
    try:
        reset_history(user.id)
        await safe_send_message(
            update,
            f"🤖 **¡Hola {user.first_name}!** Soy tu asistente con OpenAI.\n\n"
            "💬 Puedes usar los botones de abajo o escribir directamente.\n"
            "🔄 Usa los botones para acceder rápidamente a las funciones.\n"
            "✨ ¡Empecemos a chatear!",
            get_main_keyboard()
        )
        logger.info(f"Usuario autorizado inició sesión: {user.id} (@{user.username})")
    except Exception as e:
        logger.error(f"Error iniciando sesión para usuario {user.id}: {e}")
        await safe_send_message(
            update,
            "❌ **Error iniciando**\n\nHubo un problema al inicializar tu sesión.\n\n🔄 Intenta usar /start nuevamente."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_user_authorized(user.id):
        return
    
    try:
        config = get_user_config(user.id)
        help_text = (
            "🤖 **Bot de Chat con OpenAI**\n\n"
            "**Botones principales:**\n"
            "• 🆘 Ayuda - Mostrar esta información\n"
            "• 📊 Estadísticas - Ver tu uso del bot\n"
            "• 🔄 Resetear Chat - Borrar conversación\n"
            "• 💬 Chat Libre - Modo chat continuo\n"
            "• 🎭 Cambiar Modo - Estilos de respuesta\n"
            "• ⚙️ Configuración - Ajustes personalizados\n\n"
            "**Modos de respuesta:**\n"
            "• 🤖 Formal - Profesional y estructurado\n"
            "• 😊 Casual - Amigable y conversacional\n"
            "• 🎓 Académico - Detallado y educativo\n"
            "• ⚡ Conciso - Breve y directo\n\n"
            "**Comandos de configuración:**\n"
            "• `/config temperatura 0.8` - Cambiar creatividad\n"
            "• `/config modelo gpt-4o` - Cambiar modelo\n"
            "• `/config tokens 500` - Cambiar límite\n\n"
            f"**Tu configuración actual:**\n"
            f"• Modo: {config['mode']}\n"
            f"• Modelo: {config['model']}\n"
            f"• Temperatura: {config['temperature']}\n"
            f"• Máx. tokens: {config['max_tokens']}\n\n"
            "💡 Usa los botones o escribe directamente."
        )
        await safe_send_message(update, help_text, get_main_keyboard())
    except Exception as e:
        logger.error(f"Error mostrando ayuda a usuario {user.id}: {e}")
        await safe_send_message(
            update,
            "❌ **Error**\n\nNo se pudo cargar la información de ayuda.\n\n🔄 Intenta nuevamente.",
            get_main_keyboard()
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_user_authorized(user.id):
        return
    
    try:
        user_history = get_history(user.id)
        total_users = len(conversations)
        user_messages = len([msg for msg in user_history if msg["role"] == "user"])
        
        stats_text = (
            f"📊 **Estadísticas**\n\n"
            f"👤 **Tu sesión:**\n"
            f"• Mensajes enviados: {user_messages}\n"
            f"• Contexto actual: {len(user_history)} mensajes\n\n"
            f"🌐 **Global:**\n"
            f"• Usuarios activos: {total_users}\n"
            f"• Modelo en uso: {OPENAI_MODEL}"
        )
        await safe_send_message(update, stats_text, get_main_keyboard())
    except Exception as e:
        logger.error(f"Error generando estadísticas para usuario {user.id}: {e}")
        await safe_send_message(
            update,
            "❌ **Error**\n\nNo se pudieron cargar las estadísticas.\n\n🔄 Intenta nuevamente.",
            get_main_keyboard()
        )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_user_authorized(user.id):
        return
    
    try:
        reset_history(user.id)
        await safe_send_message(
            update,
            "🧹 **Chat reiniciado**\n\nContexto borrado exitosamente.\n\n✨ Empecemos de nuevo.",
            get_main_keyboard()
        )
        logger.info(f"Usuario {user.id} reinició su chat")
    except Exception as e:
        logger.error(f"Error reiniciando chat para usuario {user.id}: {e}")
        await safe_send_message(
            update,
            "❌ **Error**\n\nNo se pudo reiniciar el chat.\n\n🔄 Intenta nuevamente.",
            get_main_keyboard()
        )

async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /config para cambiar configuraciones."""
    user = update.effective_user
    if not is_user_authorized(user.id):
        return
    
    try:
        if not context.args or len(context.args) < 2:
            config = get_user_config(user.id)
            config_text = (
                f"⚙️ **Tu configuración actual:**\n\n"
                f"🎭 **Modo:** {config['mode']}\n"
                f"🌡️ **Temperatura:** {config['temperature']}\n"
                f"🧠 **Modelo:** {config['model']}\n"
                f"📏 **Tokens:** {config['max_tokens']}\n\n"
                "**Para cambiar usa:**\n"
                "`/config temperatura 0.8`\n"
                "`/config modelo gpt-4o`\n"
                "`/config tokens 500`\n\n"
                "**Valores permitidos:**\n"
                "• Temperatura: 0.0 - 2.0\n"
                "• Modelo: gpt-4o-mini, gpt-4o\n"
                "• Tokens: 100 - 4000"
            )
            await safe_send_message(update, config_text, get_main_keyboard())
            return
        
        setting = context.args[0].lower()
        value = context.args[1]
        config = get_user_config(user.id)
        
        if setting == "temperatura":
            try:
                temp = float(value)
                if 0.0 <= temp <= 2.0:
                    config["temperature"] = temp
                    user_configs[user.id] = config
                    desc = '🎨 Más creativo' if temp > 1.0 else '🎯 Más preciso' if temp < 0.5 else '⚖️ Equilibrado'
                    await safe_send_message(
                        update,
                        f"✅ **Temperatura actualizada**\n\n🌡️ **Valor:** {temp} ({desc})",
                        get_main_keyboard()
                    )
                else:
                    await safe_send_message(
                        update,
                        "❌ **Temperatura inválida**\n\nDebe estar entre 0.0 y 2.0\n\n💡 Ejemplo: `/config temperatura 0.7`",
                        get_main_keyboard()
                    )
            except ValueError:
                await safe_send_message(
                    update,
                    "❌ **Formato inválido**\n\nLa temperatura debe ser un número.\n\n💡 Ejemplo: `/config temperatura 0.7`",
                    get_main_keyboard()
                )
                    
        elif setting == "modelo":
            valid_models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
            if value in valid_models:
                config["model"] = value
                user_configs[user.id] = config
                desc = "Más inteligente" if value == "gpt-4o" else "Rápido y económico" if value == "gpt-4o-mini" else "Básico"
                await safe_send_message(
                    update,
                    f"✅ **Modelo actualizado**\n\n🧠 **Modelo:** {value}\n📊 **Tipo:** {desc}",
                    get_main_keyboard()
                )
            else:
                await safe_send_message(
                    update,
                    f"❌ **Modelo inválido**\n\nModelos disponibles:\n• {chr(10).join(valid_models)}\n\n💡 Ejemplo: `/config modelo gpt-4o-mini`",
                    get_main_keyboard()
                )
                    
        elif setting == "tokens":
            try:
                tokens = int(value)
                if 100 <= tokens <= 4000:
                    config["max_tokens"] = tokens
                    user_configs[user.id] = config
                    length = "cortas" if tokens <= 500 else "medianas" if tokens <= 1000 else "largas" if tokens <= 2000 else "muy largas"
                    await safe_send_message(
                        update,
                        f"✅ **Tokens actualizados**\n\n📏 **Límite:** {tokens}\n📝 **Respuestas:** {length}",
                        get_main_keyboard()
                    )
                else:
                    await safe_send_message(
                        update,
                        "❌ **Tokens inválidos**\n\nDeben estar entre 100 y 4000\n\n💡 Ejemplo: `/config tokens 500`",
                        get_main_keyboard()
                    )
            except ValueError:
                await safe_send_message(
                    update,
                    "❌ **Formato inválido**\n\nLos tokens deben ser un número entero.\n\n💡 Ejemplo: `/config tokens 500`",
                    get_main_keyboard()
                )
                    
        else:
            await safe_send_message(
                update,
                "❌ **Configuración no válida**\n\nOpciones disponibles:\n• temperatura\n• modelo\n• tokens\n\n💡 Ejemplo: `/config temperatura 0.7`",
                get_main_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Error en config_command para usuario {user.id}: {e}")
        await safe_send_message(
            update,
            "❌ **Error de configuración**\n\nHubo un problema procesando tu comando.\n\n🔄 Intenta nuevamente o usa los botones del menú.",
            get_main_keyboard()
        )

async def mode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el cambio de modo de respuesta."""
    user = update.effective_user
    if not is_user_authorized(user.id):
        return
    
    try:
        text = update.message.text
        config = get_user_config(user.id)
        
        if text in RESPONSE_MODES:
            old_mode = config["mode"]
            config["mode"] = text
            user_configs[user.id] = config
            update_system_prompt(user.id)
            
            mode_description = RESPONSE_MODES[text]
            await safe_send_message(
                update,
                f"✅ **Modo cambiado**\n\n"
                f"🔄 **De:** {old_mode}\n"
                f"➡️ **A:** {text}\n\n"
                f"📝 **Descripción:** {mode_description}\n\n"
                "💡 Los próximos mensajes seguirán este estilo.",
                get_main_keyboard()
            )
            logger.info(f"Usuario {user.id} cambió modo de {old_mode} a {text}")
        else:
            await safe_send_message(
                update,
                "❌ **Modo no válido**\n\nUsa el menú de modos o los botones disponibles.",
                get_mode_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Error en mode_handler para usuario {user.id}: {e}")
        await safe_send_message(
            update,
            "❌ **Error cambiando modo**\n\nHubo un problema procesando el cambio.\n\n🔄 Intenta nuevamente.",
            get_main_keyboard()
        )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los botones del teclado personalizado."""
    user = update.effective_user
    if not is_user_authorized(user.id):
        return
    
    text = update.message.text
    
    # Botones principales
    if text == "🆘 Ayuda":
        await help_command(update, context)
    elif text == "📊 Estadísticas":
        await stats_command(update, context)
    elif text == "🔄 Resetear Chat":
        await reset(update, context)
    elif text == "💬 Chat Libre":
        await update.message.reply_text(
            "💬 **Modo Chat Libre Activado**\n\n"
            "Ahora puedes escribir cualquier mensaje y te responderé.\n"
            "✨ La conversación continuará con contexto.\n"
            "🔄 Usa el botón 'Resetear Chat' para empezar de nuevo.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    elif text == "🎭 Cambiar Modo":
        config = get_user_config(user.id)
        await update.message.reply_text(
            f"🎭 **Selecciona un modo de respuesta:**\n\n"
            f"**Actual:** {config['mode']}\n\n"
            "🤖 **Formal** - Profesional y estructurado\n"
            "😊 **Casual** - Amigable y conversacional\n"
            "🎓 **Académico** - Detallado y educativo\n"
            "⚡ **Conciso** - Breve y directo",
            parse_mode='Markdown',
            reply_markup=get_mode_keyboard()
        )
    elif text == "⚙️ Configuración":
        await update.message.reply_text(
            "⚙️ **Panel de Configuración**\n\n"
            "Selecciona qué quieres ajustar:\n\n"
            "🌡️ **Temperatura** - Creatividad vs Precisión\n"
            "🧠 **Modelo** - Capacidad de OpenAI\n"
            "📏 **Tokens** - Longitud de respuestas\n"
            "📋 **Ver Config** - Configuración actual",
            parse_mode='Markdown',
            reply_markup=get_config_keyboard()
        )
    elif text == "🔙 Volver":
        await update.message.reply_text(
            "🔙 **Menú Principal**\n\nSelecciona una opción:",
            reply_markup=get_main_keyboard()
        )
    
    # Botones de configuración
    elif text == "🌡️ Temperatura":
        config = get_user_config(user.id)
        temp_desc = "🎨 Creativo" if config["temperature"] > 1.0 else "🎯 Preciso" if config["temperature"] < 0.5 else "⚖️ Equilibrado"
        await update.message.reply_text(
            f"🌡️ **Temperatura actual:** {config['temperature']} ({temp_desc})\n\n"
            "**Selecciona un valor:**\n\n"
            "🔥 **0.1** - Muy preciso y determinista\n"
            "🌡️ **0.5** - Equilibrado hacia precisión\n"
            "🌡️ **0.7** - Equilibrado (recomendado)\n"
            "🌡️ **1.0** - Creativo moderado\n"
            "🌡️ **1.5** - Muy creativo\n"
            "� **2.0** - Máxima creatividad",
            parse_mode='Markdown',
            reply_markup=get_temperature_keyboard()
        )
    elif text == "🧠 Modelo":
        config = get_user_config(user.id)
        await update.message.reply_text(
            f"🧠 **Modelo actual:** {config['model']}\n\n"
            "**Selecciona un modelo:**\n\n"
            "🧠 **gpt-4o** - Más inteligente y capaz\n"
            "⚡ **gpt-4o-mini** - Rápido y económico\n\n"
            "💡 gpt-4o es más capaz pero usa más tokens",
            parse_mode='Markdown',
            reply_markup=get_model_keyboard()
        )
    elif text == "📏 Tokens":
        config = get_user_config(user.id)
        await update.message.reply_text(
            f"📏 **Tokens actuales:** {config['max_tokens']}\n\n"
            "**Selecciona la longitud:**\n\n"
            "📏 **500** - Respuestas cortas\n"
            "📏 **1000** - Respuestas medianas\n"
            "📏 **2000** - Respuestas largas\n"
            "📏 **4000** - Respuestas muy largas\n\n"
            "💡 Más tokens = respuestas más detalladas",
            parse_mode='Markdown',
            reply_markup=get_tokens_keyboard()
        )
    elif text == "📋 Ver Config":
        await config_command(update, context)
    elif text == "🔙 Volver Config":
        await update.message.reply_text(
            "⚙️ **Panel de Configuración**\n\n"
            "Selecciona qué quieres ajustar:",
            parse_mode='Markdown',
            reply_markup=get_config_keyboard()
        )
    
    # Opciones de temperatura
    elif text in ["🔥 0.1", "🌡️ 0.5", "🌡️ 0.7", "🌡️ 1.0", "🌡️ 1.5", "🔥 2.0"]:
        temp_value = float(text.split()[-1])
        config = get_user_config(user.id)
        config["temperature"] = temp_value
        user_configs[user.id] = config
        
        temp_desc = "🎨 Creativo" if temp_value > 1.0 else "🎯 Preciso" if temp_value < 0.5 else "⚖️ Equilibrado"
        await update.message.reply_text(
            f"✅ **Temperatura actualizada**\n\n"
            f"🌡️ **Nuevo valor:** {temp_value} ({temp_desc})\n"
            f"📈 Las próximas respuestas tendrán este nivel de creatividad.",
            parse_mode='Markdown',
            reply_markup=get_config_keyboard()
        )
    
    # Opciones de modelo
    elif text in ["🧠 gpt-4o", "⚡ gpt-4o-mini"]:
        model_value = text.split()[-1]
        config = get_user_config(user.id)
        config["model"] = model_value
        user_configs[user.id] = config
        
        model_desc = "Más inteligente y capaz" if model_value == "gpt-4o" else "Rápido y económico"
        await update.message.reply_text(
            f"✅ **Modelo actualizado**\n\n"
            f"🧠 **Nuevo modelo:** {model_value}\n"
            f"📊 **Características:** {model_desc}",
            parse_mode='Markdown',
            reply_markup=get_config_keyboard()
        )
    
    # Opciones de tokens
    elif text in ["📏 500", "📏 1000", "📏 2000", "📏 4000"]:
        tokens_value = int(text.split()[-1])
        config = get_user_config(user.id)
        config["max_tokens"] = tokens_value
        user_configs[user.id] = config
        
        length_desc = "cortas" if tokens_value <= 500 else "medianas" if tokens_value <= 1000 else "largas" if tokens_value <= 2000 else "muy largas"
        await update.message.reply_text(
            f"✅ **Tokens actualizados**\n\n"
            f"📏 **Nuevo límite:** {tokens_value} tokens\n"
            f"📝 **Respuestas:** {length_desc}",
            parse_mode='Markdown',
            reply_markup=get_config_keyboard()
        )
    
    # Modos de respuesta
    elif text in RESPONSE_MODES:
        await mode_handler(update, context)
    
    else:
        # Si no es un botón conocido, tratarlo como mensaje normal
        await chat(update, context)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not update.message or not update.message.text:
        return
    
    # Verificar autorización
    if not is_user_authorized(user.id):
        await safe_send_message(
            update, 
            f"❌ **No autorizado**\n\nTu ID de usuario es: `{user.id}`\n\n👨‍💻 Contacta al administrador."
        )
        return
    
    text = update.message.text.strip()
    if not text:
        return

    # Añadir mensaje del usuario al historial
    try:
        history = get_history(user.id)
        history.append({"role": "user", "content": text})
        
        # Recortar historial si es muy largo
        history = trim_history(history)
        conversations[user.id] = history
    except Exception as e:
        logger.error(f"Error manejando historial para usuario {user.id}: {e}")
        await safe_send_message(
            update, 
            "❌ **Error interno**\n\nHubo un problema guardando tu mensaje.\n\n🔄 Intenta usar /reset"
        )
        return

    # Indicador de escritura con manejo de errores
    try:
        await update.message.chat.send_action(action=ChatAction.TYPING)
    except Exception as e:
        logger.warning(f"No se pudo mostrar indicador de escritura para usuario {user.id}: {e}")
        # No es crítico, continúamos

    # Obtener y validar configuración personalizada del usuario
    try:
        config = get_user_config(user.id)
        is_valid, validation_msg = validate_user_config(config)
        
        if not is_valid:
            logger.warning(f"Configuración inválida para usuario {user.id}: {validation_msg}")
            # Resetear a configuración por defecto
            user_configs[user.id] = {
                "mode": "😊 Casual",
                "temperature": 0.7,
                "model": "gpt-4o-mini",
                "max_tokens": 500
            }
            config = get_user_config(user.id)
            await safe_send_message(
                update,
                f"⚠️ **Configuración corregida**\n\n{validation_msg}\n\n🔧 He aplicado valores por defecto."
            )
    except Exception as e:
        logger.error(f"Error obteniendo configuración para usuario {user.id}: {e}")
        await safe_send_message(
            update, 
            "❌ **Error de configuración**\n\nUsa /reset para restaurar configuración por defecto."
        )
        return

    # Llamada a OpenAI con manejo de errores robusto
    try:
        resp = client.chat.completions.create(
            model=config["model"],
            messages=history,
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            timeout=30  # Timeout de 30 segundos
        )
        
        answer = (resp.choices[0].message.content or "").strip()
        if not answer:
            answer = "🤔 La IA no generó una respuesta. Intenta reformular tu pregunta."
        
        logger.info(f"Respuesta generada para usuario {user.id}: {len(answer)} caracteres | Modo: {config['mode']} | Modelo: {config['model']}")
        
        # Añadir respuesta al historial
        history.append({"role": "assistant", "content": answer})
        conversations[user.id] = history
        
    except openai.RateLimitError as e:
        error_msg = await handle_openai_error(e, user.id)
        await safe_send_message(update, error_msg, get_main_keyboard())
        return
        
    except openai.APIConnectionError as e:
        error_msg = await handle_openai_error(e, user.id)
        await safe_send_message(update, error_msg, get_main_keyboard())
        return
        
    except openai.APITimeoutError as e:
        logger.warning(f"Timeout OpenAI para usuario {user.id}: {e}")
        await safe_send_message(
            update,
            "⏰ **Timeout**\n\nLa IA tardó demasiado en responder.\n\n🔄 Intenta con una pregunta más simple.",
            get_main_keyboard()
        )
        return
        
    except openai.AuthenticationError as e:
        error_msg = await handle_openai_error(e, user.id)
        await safe_send_message(update, error_msg, get_main_keyboard())
        return
        
    except openai.BadRequestError as e:
        error_msg = await handle_openai_error(e, user.id)
        await safe_send_message(update, error_msg, get_main_keyboard())
        return
        
    except Exception as e:
        error_msg = await handle_openai_error(e, user.id)
        await safe_send_message(update, error_msg, get_main_keyboard())
        return

    # Enviar respuesta con manejo de errores
    try:
        success = await safe_send_message(update, answer, get_main_keyboard())
        if not success:
            logger.error(f"No se pudo enviar respuesta a usuario {user.id} después de varios intentos")
    except Exception as e:
        logger.error(f"Error crítico enviando respuesta a usuario {user.id}: {e}")

def main():
    """Función principal con manejo de errores robusto."""
    try:
        # Validar configuración inicial
        logger.info("🔧 Iniciando validación de configuración...")
        ensure_config()
        logger.info("✅ Configuración validada exitosamente")
        
        # Crear aplicación Telegram
        logger.info("📱 Creando aplicación Telegram...")
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        logger.info("✅ Aplicación Telegram creada")

        # Registrar comandos
        logger.info("📋 Registrando comandos...")
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("reset", reset))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("stats", stats_command))
        app.add_handler(CommandHandler("config", config_command))

        # Manejo de botones y chat general
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
        logger.info("✅ Handlers registrados exitosamente")

        logger.info("🤖 Chat Bot con OpenAI iniciado")
        logger.info(f"🔒 Usuarios autorizados: {len([id for id in [1, 2] if is_user_authorized(id)])}")
        logger.info("🚀 Bot ejecutándose... (Ctrl+C para detener)")
        
        # Iniciar bot
        app.run_polling()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Bot detenido por el usuario")
    except Exception as e:
        logger.critical(f"💥 Error crítico al iniciar el bot: {e}")
        logger.critical("🔍 Verifica tu configuración y conexión a internet")
        
        # Información de diagnóstico
        logger.error("❌ Verifica tu configuración:")
        logger.error("  • TOKEN de Telegram en config/settings.py")
        logger.error("  • API Key de OpenAI configurada")
        logger.error("  • Conexión a internet disponible")
            
        raise  # Re-lanzar el error para debugging

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO: {e}")
        print("🔧 Revisa los logs para más detalles")
        print("📖 Consulta la documentación del bot")
        exit(1)
