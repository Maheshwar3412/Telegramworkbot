import os
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Fetch Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") # Provided automatically by Render

if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("Missing BOT_TOKEN or HF_TOKEN in environment variables.")

# 2. Initialize Telegram Bot & OpenAI Client
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# 3. Handle /start and /help commands
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am a DeepSeek-R1 AI bot. Send me any message and I will reply!")

# 4. Handle incoming text messages
@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # Show 'typing...' status in Telegram
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Call the Hugging Face / OpenAI API
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=[
                {"role": "user", "content": message.text}
            ]
        )
        
        # Extract response and send back to Telegram user
        reply_text = chat_completion.choices[0].message.content
        bot.reply_to(message, reply_text)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Sorry, I ran into an error processing your request.")


# 5. Flask Webhook Routes
@app.route('/' + BOT_TOKEN, methods=['POST'])
def receive_update():
    """Receives POST requests from Telegram"""
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def index():
    """Health check route for Render"""
    return "Bot is running!", 200

# 6. Set up the Webhook
def setup_webhook():
    bot.remove_webhook()
    if RENDER_EXTERNAL_URL:
        # Construct the webhook URL using Render's automatic external URL
        webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
        bot.set_webhook(url=webhook_url)
        print(f"Webhook set to: {webhook_url}")
    else:
        print("RENDER_EXTERNAL_URL not found. Webhook was not set.")

setup_webhook()

if __name__ == "__main__":
    # If running locally (not strictly needed for gunicorn on Render, but good for testing)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
