import os
from dotenv import load_dotenv
from PIL import Image
import telebot
from flask import Flask, request
from io import BytesIO

# Load token and webhook URL
load_dotenv()
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_photos = {}

TEMPLATE_PATH = "template.png"
BEFORE_BOX = (100, 400, 670, 1200)
AFTER_BOX = (850, 400, 1420, 1200)

def paste_resized(template, img, box):
    resized = img.resize((box[2] - box[0], box[3] - box[1]))
    template.paste(resized, (box[0], box[1]))
    return template

@bot.message_handler(commands=["start"])
def start(message):
    user_photos[message.chat.id] = []
    bot.reply_to(message, "Send the BEFORE photo")

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded = bot.download_file(file_info.file_path)
    img = Image.open(BytesIO(downloaded)).convert("RGB")
    user_photos.setdefault(chat_id, []).append(img)

    if len(user_photos[chat_id]) == 1:
        bot.reply_to(message, "Now send the AFTER photo.")
    elif len(user_photos[chat_id]) == 2:
        before, after = user_photos[chat_id]
        template = Image.open(TEMPLATE_PATH).convert("RGB")
        paste_resized(template, before, BEFORE_BOX)
        paste_resized(template, after, AFTER_BOX)

        output_path = f"{chat_id}_result.jpg"
        template.save(output_path)
        with open(output_path, "rb") as result:
            bot.send_photo(chat_id, result)
        user_photos[chat_id] = []

@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
