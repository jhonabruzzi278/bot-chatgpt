Guía Rápida de Comandos NSSM
Para Iniciar el Bot
Se usa cuando el bot está detenido (ej. después de un reinicio manual).

PowerShell

& $nssm start MiBotTelegram
Para Detener el Bot
Necesario antes de actualizar el código.

PowerShell

& $nssm stop MiBotTelegram
Para Reiniciar el Bot (El más común)
Se usa después de actualizar tu código (después de un git pull). Esto detiene y vuelve a iniciar el bot en un solo paso.

PowerShell

& $nssm restart MiBotTelegram
Para Comprobar el Estado del Bot
Te dice si el bot está SERVICE_RUNNING (corriendo) o SERVICE_STOPPED (detenido).

PowerShell

& $nssm status MiBotTelegram
Para Eliminar el Servicio
Si algún día ya no quieres el bot, así es como lo eliminas permanentemente (primero debes detenerlo).

PowerShell

& $nssm stop MiBotTelegram
& $nssm remove MiBotTelegram