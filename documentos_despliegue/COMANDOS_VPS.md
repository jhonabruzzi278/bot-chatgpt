# Comandos útiles para administrar el bot en VPS

## 🔧 Comandos del Servicio

### Ver estado del bot
```bash
sudo systemctl status foto-bot.service
```

### Iniciar el bot
```bash
sudo systemctl start foto-bot.service
```

### Detener el bot
```bash
sudo systemctl stop foto-bot.service
```

### Reiniciar el bot
```bash
sudo systemctl restart foto-bot.service
```

### Deshabilitar inicio automático
```bash
sudo systemctl disable foto-bot.service
```

## 📋 Monitoreo de Logs

### Ver logs en tiempo real
```bash
sudo journalctl -u foto-bot.service -f
```

### Ver últimas 50 líneas de log
```bash
sudo journalctl -u foto-bot.service -n 50
```

### Ver logs por fecha
```bash
sudo journalctl -u foto-bot.service --since "2024-01-01 00:00:00"
```

## 🔄 Actualizar el Bot

### 1. Detener el servicio
```bash
sudo systemctl stop foto-bot.service
```

### 2. Cambiar al directorio del bot
```bash
cd /home/botuser/foto-bot
```

### 3. Activar entorno virtual
```bash
source .venv/bin/activate
```

### 4. Hacer backup de config
```bash
cp .env .env.backup
```

### 5. Actualizar código (si usas git)
```bash
git pull origin main
```

### 6. Actualizar dependencias
```bash
pip install -r requirements.txt --upgrade
```

### 7. Reiniciar servicio
```bash
sudo systemctl start foto-bot.service
```

## 🛠️ Solución de Problemas

### Bot no inicia
```bash
# Ver errores detallados
sudo journalctl -u foto-bot.service -n 100

# Verificar archivo de configuración
sudo nano /home/botuser/foto-bot/.env

# Verificar permisos
sudo chown -R botuser:botuser /home/botuser/foto-bot
```

### Alta CPU o memoria
```bash
# Ver procesos
htop

# Ver uso específico del bot
ps aux | grep python

# Reiniciar si es necesario
sudo systemctl restart foto-bot.service
```

## 📊 Monitoreo del Sistema

### Uso de recursos
```bash
# CPU y memoria general
htop

# Espacio en disco
df -h

# Temperatura (si está disponible)
sensors
```

### Conectividad
```bash
# Test de internet
ping -c 3 google.com

# Test APIs
curl -I https://api.openai.com
curl -I https://api.telegram.org
```

## 🔐 Seguridad

### Actualizar sistema regularmente
```bash
sudo apt update && sudo apt upgrade -y
```

### Configurar firewall básico
```bash
# Instalar ufw
sudo apt install ufw

# Configurar reglas básicas
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh

# Activar firewall
sudo ufw enable
```

### Backup automático
```bash
# Crear script de backup
nano /home/botuser/backup_bot.sh

# Contenido del script:
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "/home/botuser/backups/foto-bot_$DATE.tar.gz" \
  /home/botuser/foto-bot/.env \
  /home/botuser/foto-bot/bot_data.sqlite \
  /home/botuser/foto-bot/logs/

# Hacer ejecutable
chmod +x /home/botuser/backup_bot.sh

# Agregar a crontab para backup diario
crontab -e
# Agregar línea:
0 2 * * * /home/botuser/backup_bot.sh
```

## 🚨 Alertas por Email (Opcional)

### Instalar mailutils
```bash
sudo apt install mailutils
```

### Script para alertas
```bash
# Crear script de monitoreo
nano /home/botuser/check_bot.sh

#!/bin/bash
if ! systemctl is-active --quiet foto-bot.service; then
    echo "🚨 ALERTA: El bot foto-bot no está funcionando" | mail -s "Bot Caído" tu-email@ejemplo.com
    sudo systemctl start foto-bot.service
fi

# Agregar a crontab cada 5 minutos
*/5 * * * * /home/botuser/check_bot.sh
```

## ⚡ Optimización

### Para VPS de pocos recursos
```bash
# Límitar memoria en systemd
sudo nano /etc/systemd/system/foto-bot.service

# Agregar en [Service]:
MemoryLimit=256M
CPUQuota=50%

sudo systemctl daemon-reload
sudo systemctl restart foto-bot.service
```

### Limpiar logs antiguos
```bash
# Configurar rotación de logs
sudo nano /etc/systemd/journald.conf

# Configurar:
SystemMaxUse=100M
MaxFileSec=7day
```