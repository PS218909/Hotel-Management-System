from src.app import app
from src.config import DISCORD_BOT_TOKEN
from src.discord_bot import client
from threading import Thread

def run_flask_app():
    app.run(port=80, debug=True)

def run_discord_bot():
    client.run(DISCORD_BOT_TOKEN)

Thread(None, run_flask_app, '').start()
run_discord_bot()