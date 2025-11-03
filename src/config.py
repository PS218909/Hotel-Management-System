import os

DEBUG = True

# Hotel Detail
HOTEL_NAME = "Hotel Name"
HOTEL_ADDRESS = "Hotel Address"

# File's and folder's
DATASET_DIR = "dataset"
ROOMS_DB = os.path.join(DATASET_DIR, "rooms.csv")
CUSTOMERS_DB = os.path.join(DATASET_DIR, "customer.csv")
TRANSACTIONS_DB = os.path.join(DATASET_DIR, "transaction.csv")
REGISTER_DB = os.path.join(DATASET_DIR, "register.csv")
ALERT_DB = os.path.join(DATASET_DIR, 'alert.json')
EVENT_LOG = os.path.join(DATASET_DIR, 'events.csv')

# Room State's
AVAILABLE = 1
OCCUPIED = 2
OUT_OF_ORDER = 3

# Report Configuration
REPORT_PATH = "C:\\Users\\Admin\\Desktop\\Downloaded Report"
REPORT_MONTHLY_FLODER = True

# Discord Webhook
DISCORD_WEBHOOK_URL = "DISCORD WEBHOOK"

# Discord Configuration
TESTING_CHANNEL_ID = 0 
UPDATE_CHANNEL_ID = 0  
DISCORD_BOT_TOKEN = "BOT TOKEN"
