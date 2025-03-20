import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging

# Lee el TOKEN desde las variables de entorno
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise Exception("No se encontró la variable BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat.id
    nombre = update.message.chat.first_name
    mensaje = f"👋 ¡Hola, {nombre}! Bienvenido al bot de Diagnóstico por Imágenes. Usa /jugar para comenzar."
    update.message.reply_text(mensaje)

def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    updater.start_polling()
    logger.info("Bot iniciado...")
    updater.idle()

if __name__ == "__main__":
    main()
# Fixing deployment issue