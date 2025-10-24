# 🔧 Configuración de Webhooks para Telegram Bot

> **Nota**: Los webhooks son opcionales pero recomendados para producción ya que son más eficientes que polling.

## ¿Qué son los Webhooks?

En lugar de que tu bot "pregunte" constantemente a Telegram si hay mensajes nuevos (polling), los webhooks permiten que Telegram "envíe" los mensajes directamente a tu servidor cuando llegan.

**Ventajas:**
- ⚡ Más rápido (respuesta inmediata)
- 💰 Menos uso de recursos
- 🔒 Más seguro con HTTPS

## 📋 Requisitos

1. **Dominio propio** (ej: `mibot.ejemplo.com`)
2. **Certificado SSL/HTTPS** (Let's Encrypt gratis)
3. **Puerto abierto** (usualmente 80 y 443)

## 🛠️ Configuración paso a paso

### 1. Configurar Nginx como proxy reverso

```bash
# Instalar Nginx
sudo apt install nginx

# Crear configuración del sitio
sudo nano /etc/nginx/sites-available/foto-bot

# Contenido:
server {
    listen 80;
    server_name tu-dominio.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Activar sitio
sudo ln -s /etc/nginx/sites-available/foto-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. Configurar SSL con Let's Encrypt

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com

# Verificar renovación automática
sudo crontab -e
# Agregar:
0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Modificar el bot para webhooks

Crear archivo `webhook_bot.py`:

```python
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask, request
import asyncio
from threading import Thread

# Tu código del bot existente aquí...
from bot import handle_message, handle_button_click, start

# Configurar Flask
app = Flask(__name__)

# Variable global para la aplicación de Telegram
telegram_app = None

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recibir actualizaciones de Telegram"""
    try:
        if telegram_app:
            update = Update.de_json(request.get_json(force=True), telegram_app.bot)
            asyncio.run_coroutine_threadsafe(
                telegram_app.process_update(update),
                telegram_app.loop
            )
        return "OK"
    except Exception as e:
        logging.error(f"Error en webhook: {e}")
        return "ERROR", 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud"""
    return "Bot funcionando correctamente"

def setup_webhook():
    """Configurar webhook de Telegram"""
    webhook_url = f"https://{os.getenv('WEBHOOK_DOMAIN')}/webhook"
    
    try:
        # Configurar webhook
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        app_telegram = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
        
        loop.run_until_complete(
            app_telegram.bot.set_webhook(
                url=webhook_url,
                max_connections=100,
                drop_pending_updates=True
            )
        )
        
        logging.info(f"Webhook configurado en: {webhook_url}")
        return True
        
    except Exception as e:
        logging.error(f"Error configurando webhook: {e}")
        return False

async def main():
    """Función principal del bot"""
    global telegram_app
    
    # Crear aplicación de Telegram
    telegram_app = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    
    # Agregar handlers (copiado de tu bot.py)
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # ... otros handlers
    
    # Inicializar aplicación
    await telegram_app.initialize()
    await telegram_app.start()
    
    # Mantener el loop corriendo
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Verificar variables de entorno
    required_vars = ['TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY', 'WEBHOOK_DOMAIN']
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Variable de entorno {var} no configurada")
    
    # Configurar webhook
    if setup_webhook():
        # Iniciar bot en thread separado
        bot_thread = Thread(target=lambda: asyncio.run(main()))
        bot_thread.daemon = True
        bot_thread.start()
        
        # Iniciar servidor Flask
        app.run(host='127.0.0.1', port=8000, debug=False)
    else:
        logging.error("No se pudo configurar el webhook")
```

### 4. Actualizar variables de entorno

```bash
# Editar .env
nano /home/botuser/foto-bot/.env

# Agregar:
WEBHOOK_DOMAIN=tu-dominio.com
WEBHOOK_MODE=true
```

### 5. Actualizar servicio systemd

```bash
# Editar servicio
sudo nano /etc/systemd/system/foto-bot.service

# Cambiar ExecStart por:
ExecStart=/home/botuser/foto-bot/.venv/bin/python /home/botuser/foto-bot/webhook_bot.py

# Recargar y reiniciar
sudo systemctl daemon-reload
sudo systemctl restart foto-bot.service
```

## 🧪 Probar Webhooks

### Verificar configuración

```bash
# Verificar que el webhook esté configurado
curl -X GET "https://api.telegram.org/bot<TU_TOKEN>/getWebhookInfo"

# Debería mostrar algo como:
{
    "ok": true,
    "result": {
        "url": "https://tu-dominio.com/webhook",
        "has_custom_certificate": false,
        "pending_update_count": 0
    }
}
```

### Test de conectividad

```bash
# Test del endpoint de salud
curl https://tu-dominio.com/health

# Ver logs del bot
sudo journalctl -u foto-bot.service -f
```

## 🚨 Solución de Problemas

### Error de certificado SSL
```bash
# Verificar certificado
sudo certbot certificates

# Renovar si es necesario
sudo certbot renew
```

### Bot no recibe mensajes
```bash
# Verificar webhook
curl -X GET "https://api.telegram.org/bot<TU_TOKEN>/getWebhookInfo"

# Eliminar webhook (volver a polling temporalmente)
curl -X POST "https://api.telegram.org/bot<TU_TOKEN>/deleteWebhook"

# Reconfigurar webhook
curl -X POST "https://api.telegram.org/bot<TU_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://tu-dominio.com/webhook"}'
```

### Logs de Nginx
```bash
# Ver logs de acceso
sudo tail -f /var/log/nginx/access.log

# Ver logs de error
sudo tail -f /var/log/nginx/error.log
```

## 📝 Notas Importantes

1. **Los webhooks requieren HTTPS** - No funcionan con HTTP
2. **Un bot solo puede tener un webhook activo** - Si cambias de servidor, elimina el webhook anterior
3. **Telegram valida certificados SSL** - Deben ser válidos y confiables
4. **Puerto 443 recomendado** - Aunque 80, 88, 8443 también funcionan

## 🔄 Volver a Polling

Si tienes problemas con webhooks, puedes volver al modo polling:

```bash
# Eliminar webhook
curl -X POST "https://api.telegram.org/bot<TU_TOKEN>/deleteWebhook"

# Usar el bot.py original
sudo nano /etc/systemd/system/foto-bot.service
# Cambiar ExecStart de nuevo a bot.py

sudo systemctl daemon-reload
sudo systemctl restart foto-bot.service
```

¡Los webhooks son más avanzados pero ofrecen mejor rendimiento para bots en producción!