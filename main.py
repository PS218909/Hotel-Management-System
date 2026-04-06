from app import create_app
from app.config import Config
from app.util.helper import push_notification, get_config, DEFAULT_CONFIG
import threading, time, os, json


def run_flask(app):
    try:
        app.run(host='0.0.0.0', port=80, debug=False)
    except Exception as e:
        print(f"Flask crashed: {e}")


def run_worker():
    try:
        push_notification()
    except Exception as e:
        print(f"Worker crashed: {e}")


def run_discord_bot():
    from bots.discord.bot import bot
    config = get_config()
    token = config.get('DISCORD_BOT_TOKEN')

    if not token:
        print("No Discord token provided")
        return

    try:
        print("Starting Discord bot...")
        bot.run(token)  # blocking
    except Exception as e:
        print(f"Discord bot crashed: {e}")

def main():
    app = create_app(Config)
    app.run(debug=True)
    # Ensure config file exists
    os.makedirs('instance', exist_ok=True)
    config_path = os.path.join('instance', 'config.json')

    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            json.dump(DEFAULT_CONFIG, f)

    # Start threads
    # threading.Thread(target=run_flask, args=(app,), daemon=True).start()
    threading.Thread(target=run_worker, daemon=True).start()
    threading.Thread(target=run_discord_bot, daemon=True).start()

    run_flask(app)

if __name__ == '__main__':
    main()