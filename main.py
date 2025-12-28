from src.app import app
from src.util import default_values, push_webhook_alerts
from src.bot import client
from src.config import DEBUG, DISCORD_BOT_TOKEN

import threading

def run_flask_app():
    app.run(port=80)

def run_discord_bot():
    client.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    default_values()
    threading.Thread(target=run_flask_app).start()
    threading.Thread(target=push_webhook_alerts).start()
    run_discord_bot()