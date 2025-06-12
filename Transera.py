from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)
from deep_translator import GoogleTranslator
from gtts import gTTS
from flask import Flask
from PIL import Image
import easyocr
import threading
import os

ocr_reader = easyocr.Reader(['en'])
user_temp_data = {}

# Start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        " Welcome to Transera Bot!\nJust send me a message or image and I’ll help translate it with audio.\nI'll ask which direction you want to translate each time!"
    )

# Help
def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "How to Use Transera Bot:\n"
        "https://transera-bot.blogspot.com/2025/06/how-to-use-transera-bot-your-pocket.html\n\n"
        "️What it does:\n"
        "• Translates between English and German\n"
        "• Works with both text and images\n"
        "• Sends back translated audio\n\n"
        "Just send a message or upload an image, and Transera will do the magic! \n"
        "Perfect for learners, travellers, and language fans."
    )


# Text handler
def handle_text(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    user_temp_data[user_id] = {'type': 'text', 'content': update.message.text}

    buttons = [
        [InlineKeyboardButton("📤 English ➜ German", callback_data='en2de')],
        [InlineKeyboardButton("📥 German ➜ English", callback_data='de2en')]
    ]
    update.message.reply_text("Choose translation direction:", reply_markup=InlineKeyboardMarkup(buttons))

# Image handler
def handle_photo(update: Update, context: CallbackContext) -> None:
    photo = update.message.photo[-1]
    user_id = update.message.chat_id
    file_path = f"temp_{user_id}.jpg"
    photo.get_file().download(file_path)

    result = ocr_reader.readtext(file_path, detail=0)
    extracted_text = " ".join(result)
    os.remove(file_path)

    if not extracted_text.strip():
        update.message.reply_text(" Couldn't detect any text in the image.")
        return

    user_temp_data[user_id] = {'type': 'text', 'content': extracted_text}

    buttons = [
        [InlineKeyboardButton("📤 English ➜ German", callback_data='en2de')],
        [InlineKeyboardButton("📥 German ➜ English", callback_data='de2en')]
    ]
    update.message.reply_text("Text found! Choose translation direction:", reply_markup=InlineKeyboardMarkup(buttons))

# Callback for translation choice
def handle_translation_choice(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = query.message.chat_id
    direction = query.data  # en2de or de2en

    if user_id not in user_temp_data:
        query.edit_message_text(" No text found to translate.")
        return

    text = user_temp_data[user_id]['content']
    del user_temp_data[user_id]

    src, tgt = ('en', 'de') if direction == 'en2de' else ('de', 'en')

    try:
        translated = GoogleTranslator(source=src, target=tgt).translate(text)
        query.edit_message_text(f"Translated:\n{translated}")

        tts = gTTS(text=translated, lang=tgt)
        audio_file = f"audio_{user_id}.mp3"
        tts.save(audio_file)
        context.bot.send_audio(chat_id=user_id, audio=open(audio_file, 'rb'))
        os.remove(audio_file)

    except Exception as e:
        query.edit_message_text(f"Error during translation: {str(e)}")

# Flask Keep-Alive
app = Flask('')

@app.route('/')
def home():
    return "Transera Bot is live!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

# Main
def main():
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("BOT_TOKEN2")
    print("Loaded Token:", token)

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    dp.add_handler(CallbackQueryHandler(handle_translation_choice))

    keep_alive()
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
