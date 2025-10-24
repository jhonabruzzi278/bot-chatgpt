#!/bin/bash
# Script de instalación automática para VPS Ubuntu/Debian

set -e  # Salir si hay algún error

echo "🚀 Instalando Foto Bot en servidor..."

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
echo "🔧 Instalando dependencias..."
sudo apt install -y python3 python3-pip python3-venv git curl wget screen htop nano

# Crear usuario para el bot (opcional, más seguro)
if ! id "botuser" &>/dev/null; then
    echo "👤 Creando usuario para el bot..."
    sudo useradd -m -s /bin/bash botuser
fi

# Cambiar al directorio home del usuario
cd /home/botuser

# Clonar repositorio (cambiar por tu URL)
echo "📁 Clonando proyecto..."
if [ ! -d "foto-bot" ]; then
    git clone https://github.com/tu-usuario/foto-bot.git
fi

cd foto-bot

# Crear entorno virtual
echo "🐍 Creando entorno virtual..."
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias Python
echo "📦 Instalando paquetes Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variables de entorno
echo "⚙️ Configurando variables de entorno..."
if [ ! -f ".env" ]; then
    echo "Creando archivo .env..."
    echo "TELEGRAM_BOT_TOKEN=TU_TOKEN_AQUI" > .env
    echo "OPENAI_API_KEY=TU_API_KEY_AQUI" >> .env
    echo "LOG_LEVEL=INFO" >> .env
    echo ""
    echo "⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales:"
    echo "nano /home/botuser/foto-bot/.env"
fi

# Configurar permisos
echo "🔒 Configurando permisos..."
sudo chown -R botuser:botuser /home/botuser/foto-bot
chmod +x /home/botuser/foto-bot/bot.py

# Instalar servicio systemd
echo "⚙️ Instalando servicio systemd..."
sudo cp foto-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable foto-bot.service

echo ""
echo "✅ Instalación completada!"
echo ""
echo "📝 Próximos pasos:"
echo "1. Edita el archivo de configuración:"
echo "   sudo nano /home/botuser/foto-bot/.env"
echo ""
echo "2. Inicia el servicio:"
echo "   sudo systemctl start foto-bot.service"
echo ""
echo "3. Verifica el estado:"
echo "   sudo systemctl status foto-bot.service"
echo ""
echo "4. Ver logs en tiempo real:"
echo "   sudo journalctl -u foto-bot.service -f"
echo ""
echo "🎉 ¡Tu bot estará funcionando 24/7!"