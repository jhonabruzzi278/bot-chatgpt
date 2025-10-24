# 📁 Documentos de Despliegue - Foto Bot

Esta carpeta contiene todos los archivos y documentación necesarios para desplegar tu bot de Telegram en servidores 24/7, **sin afectar el proyecto principal**.

## 📋 Contenido de la Carpeta

### 🚀 **Archivos de Configuración**
- **`Procfile`** - Configuración para Heroku
- **`runtime.txt`** - Especifica la versión de Python para Heroku
- **`.env.example`** - Plantilla de variables de entorno
- **`foto-bot.service`** - Archivo de servicio systemd para Linux

### 📖 **Documentación**
- **`DESPLIEGUE_24-7.md`** - Guía completa de opciones de hosting
- **`COMANDOS_VPS.md`** - Manual de administración para VPS
- **`WEBHOOKS.md`** - Configuración avanzada de webhooks (opcional)

### 🛠️ **Scripts de Instalación**
- **`install_vps.sh`** - Script automático de instalación para Ubuntu/Debian

---

## 🎯 **Cómo Usar Esta Documentación**

### **1. Para Principiantes (Heroku)**
1. Lee `DESPLIEGUE_24-7.md` sección "HEROKU"
2. Usa los archivos `Procfile`, `runtime.txt` y `.env.example`
3. Costo: **Gratuito** (con limitaciones)

### **2. Para Usuarios Avanzados (VPS)**
1. Lee `DESPLIEGUE_24-7.md` sección "VPS"
2. Usa el script `install_vps.sh` para instalación automática
3. Consulta `COMANDOS_VPS.md` para administración
4. Costo: **$2-5/mes** (control total)

### **3. Para Máximo Rendimiento (Webhooks)**
1. Configura primero el VPS básico
2. Sigue `WEBHOOKS.md` para implementar webhooks
3. Requiere dominio propio y certificado SSL

---

## ⚡ **Instalación Rápida**

### **Opción A: VPS con Script Automático**
```bash
# 1. Copia el script al servidor
scp install_vps.sh usuario@tu-servidor:/home/usuario/

# 2. Ejecuta la instalación
chmod +x install_vps.sh
./install_vps.sh

# 3. Configura tus tokens
nano /home/botuser/foto-bot/.env

# 4. Inicia el bot
sudo systemctl start foto-bot.service
```

### **Opción B: Heroku (Más Fácil)**
```bash
# 1. Copia archivos a tu proyecto
cp Procfile runtime.txt .env.example ../

# 2. Configura Heroku
heroku create tu-bot-nombre
heroku config:set TELEGRAM_BOT_TOKEN=tu_token
heroku config:set OPENAI_API_KEY=tu_api_key

# 3. Despliega
git push heroku main
```

---

## 📊 **Comparación Rápida**

| Método | Dificultad | Costo | Control | Recomendado Para |
|--------|------------|-------|---------|------------------|
| Heroku | ⭐ Fácil | Gratis | Básico | Pruebas/Inicio |
| Railway | ⭐ Fácil | $1-5 | Medio | Producción Simple |
| VPS | ⭐⭐⭐ Medio | $2-5 | Total | Producción Seria |
| Webhooks | ⭐⭐⭐⭐ Avanzado | $2-5 + Dominio | Total | Alto Rendimiento |

---

## 🆘 **Soporte y Troubleshooting**

### **Problemas Comunes**
- Bot no inicia → Ver logs con `sudo journalctl -u foto-bot.service -f`
- Error 409 → Eliminar webhooks con `curl -X POST "https://api.telegram.org/bot<TOKEN>/deleteWebhook"`
- Sin respuesta → Verificar tokens en archivo `.env`

### **Archivos de Log**
- Heroku: `heroku logs --tail`
- VPS: `sudo journalctl -u foto-bot.service -f`
- Local: Archivo `logs/bot.log`

---

## 🔄 **Actualización del Bot**

Cuando actualices tu código principal:

### **Para Heroku:**
```bash
git add .
git commit -m "Actualización"
git push heroku main
```

### **Para VPS:**
```bash
sudo systemctl stop foto-bot.service
cd /home/botuser/foto-bot
git pull origin main
pip install -r requirements.txt --upgrade
sudo systemctl start foto-bot.service
```

---

## ⚠️ **Importante**

- Esta carpeta **NO afecta** tu proyecto principal
- Todos los archivos son **copias independientes**
- Puedes modificar estos archivos sin romper nada
- Tu `bot.py` original sigue funcionando normalmente

---

## 🤝 **¿Necesitas Ayuda?**

1. **Revisa la documentación** correspondiente a tu método elegido
2. **Consulta los logs** para ver errores específicos
3. **Verifica las variables de entorno** están configuradas correctamente
4. **Prueba localmente** antes de desplegar en servidor

¡Tu bot estará funcionando 24/7 sin problemas! 🎉