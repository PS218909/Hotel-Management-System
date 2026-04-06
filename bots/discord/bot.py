import discord, re
from discord.ext import tasks, commands
from datetime import datetime, timedelta, time

from app import create_app
from app.config import Config

app = create_app(config_class=Config)
app.app_context().push()

from app.services.register import get_active_registers, get_register_by_current_stay, Room
from app.services.room import get_all_rooms
from app.services.transaction import get_all_transaction_api, Transaction
from app.services.migrate import export_data
from app.util.helper import generate_image, get_config

REPEAT_AFTER = 45
DELETE_AFTER = 30 * 60
DISCORD_CHANNEL_ID_TEST = get_config().get('DISCORD_CHANNEL_ID_TEST', 0)
DISCORD_CHANNEL_ID_UPDATES = get_config().get('DISCORD_CHANNEL_ID_UPDATES', 0)
SCHEDULED_BACKUP_TIME = time(hour=12, minute=0)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

def message_parser(content):
    ROOM_PATTERN = r"(?:room\s*)?(\d+)"
    trigger_phrases = ('who is on', 'who is in', 'room details', 'check room', 'occupant', 'room')
    is_asking_about_rooms = any(phrase in content for phrase in trigger_phrases)

    if is_asking_about_rooms:
        matches = re.findall(ROOM_PATTERN, content)
        rooms = [i.room_number for i in get_all_rooms()]
        selected_rooms = []
        if matches:
            for match in matches:
                if str(match) in str(rooms):
                    selected_rooms.append(match)
        elif 'all':
            return 'Room', rooms
        return 'Room', selected_rooms
    
    trigger_phrases = ('payment', 'transaction')
    is_asking_about_transaction = any(phrase in content for phrase in trigger_phrases)

    if is_asking_about_transaction:
        search_date = re.findall(r"(\d{1,2}-\d{1,2}-\d{2,4})", content)
        selected_transaction = []
        if len(search_date) == 2:
            selected_transaction.extend(Transaction.query.filter(Transaction.transaction_time >= datetime.strptime(search_date[0], '%d-%m-%Y'), Transaction.transaction_time < (datetime.strptime(search_date[1], '%d-%m-%Y') + timedelta(1))).all())
        
        elif len(search_date) == 1:
            today = datetime.strptime(search_date[0], '%d-%m-%y')
            next_day = today + timedelta(days=1)
            selected_transaction.extend(Transaction.query.filter(Transaction.modified_time >= today, Transaction.modified_time < next_day))
        
        name_match = re.search(r"(?:from|for|by|name)\s+([a-zA-Z]+)", content, re.IGNORECASE)
        if name_match:
            name = name_match.group(1)
            query = Transaction.register.customer.ilike(f"%{name_match}%")
            selected_transaction.extend(query)
        
        return 'Transaction', selected_transaction
    
    trigger_phrases = ('status', 'view')
    is_asking_about_img = any(phrase in content for phrase in trigger_phrases)
    if is_asking_about_img:
        return 'Status', generate_image()
    
    trigger_phrases = ('delete', 'remove messages')
    is_asking_about_delete = any(phrase in content for phrase in trigger_phrases)
    if is_asking_about_delete:
        count = re.findall(r'\d+', content)
        return 'Delete', [int(i) for i in count]
    
    trigger_phrases = ('get data', 'fetch', 'backup')
    is_asking_about_backup = any(phrase in content for phrase in trigger_phrases)
    if is_asking_about_backup:
        return 'Backup', export_data()

    return None, []

@tasks.loop(time=SCHEDULED_BACKUP_TIME)
async def upload_backup():
    if datetime.now().weekday() in [0, 3]:
        DISCORD_CHANNEL = DISCORD_CHANNEL_ID_TEST or DISCORD_CHANNEL_ID_UPDATES
        if DISCORD_CHANNEL:
            channel = bot.get_channel(int(DISCORD_CHANNEL))
            export = discord.File(fp=export_data(), description='Scheduled Backup')
            await channel.send(file=export)

@tasks.loop(minutes=REPEAT_AFTER)
async def send_updates():
    DISCORD_CHANNEL = DISCORD_CHANNEL_ID_TEST or DISCORD_CHANNEL_ID_UPDATES
    if DISCORD_CHANNEL:
        channel = bot.get_channel(int(DISCORD_CHANNEL))
        if channel:
            img = generate_image()
            update_file = discord.File(fp=img, filename='update.png', description='Updated')
            await channel.send(file=update_file, delete_after=(REPEAT_AFTER * 60) - (5 * 60))
        else:
            print('Channel Not Found')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not send_updates.is_running():
        send_updates.start()
    if not upload_backup.is_running():
        upload_backup.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content:
        context, data = message_parser(content=message.content.lower())
        if context and data:
            if context == 'Room':
                for room in data:
                    get_room = get_register_by_current_stay(Room.query.filter(Room.room_number==room).first().id)
                    if get_room:
                        await message.channel.send(f'{room} is occupied {get_room.customer.name}.', delete_after=DELETE_AFTER)
                    else:
                        await message.channel.send(f'{room} is available.', delete_after=DELETE_AFTER)
            if context == 'Transaction':
                for transaction in data:
                    await message.channel.send(str(transaction), delete_after=DELETE_AFTER)
            
            if context == 'Delete':
                async for msg in message.channel.history(limit=sum(data)):
                    await msg.delete()
            
            if context == 'Status':
                file = discord.File(fp=data, filename='update.png', description='Updated')
                await message.channel.send(file=file, delete_after=DELETE_AFTER)
            
            if context == 'Backup':
                print('Backup is running')
                file = discord.File(fp=data, filename='Backup Data', description='Backup')
                await message.channel.send(file=file)