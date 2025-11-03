from .config import *
from .util import *
from .analysis import get_analysis
from PIL import Image, ImageDraw, ImageFont
import io, psutil, signal
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime

import discord
from discord.ext import tasks, commands

intents = discord.Intents().default()
intents.message_content = True

client = discord.Client(intents=intents)

def create_report_image():
    data = get_rooms_status()
    payments = fetch_payments()
    today_1 = datetime.now().strftime('%Y-%m-%d')
    today_2 = datetime.now().strftime('%d-%m-%Y')
    today_payments = {'total': 0}
    for payment in payments:
        if (today_1 in payment['t'] or today_2 in payment['t']):
            today_payments[payment['m']] = today_payments.get(payment['m'], 0) + (payment['a_x'] if payment['rid'] != -1 else -payment['a_x'])
            today_payments['total'] += payment['a_x']
    mode = 'RGB'
    tile = (400, 400)
    gap = 200
    max_col = 8
    max_row = 8
    size = ((tile[0] + gap) * max_col + gap, (tile[1] + gap) * max_row)
    BG_COLOR= (0, 0, 0)

    img = Image.new(mode, size, BG_COLOR)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", size=120)
    x0, y0 = gap, gap
    for floor, beds in data.items():
        for bed, res in beds.items():
            if x0 + tile[0] >= size[0]:
                x0 = gap
                y0 += gap + tile[1]
            draw.rectangle([(x0, y0), (x0 + tile[0], y0 + tile[1])], fill='red' if res['status'] != 1 else 'green', outline='black', width=3)
            draw.text((x0 + 100, y0 + 125), str(bed).zfill(3), font=font, stroke_fill='black')
            x0 += tile[0] + gap
        x0 = gap
        y0 += gap + tile[1]
    
    for payment in today_payments:
        draw.text((x0, y0), payment.upper() + ': ' + str(today_payments.get(payment, 0)), font=font)
        y0 += 150

    img_byte = io.BytesIO()

    img.save(img_byte, format='PNG')
    img_byte.seek(0)
    return img_byte

@tasks.loop(minutes=15)
async def send_update():
    '''Send Current Room Status'''
    try:
        await client.wait_until_ready()
        channel = client.get_channel(TESTING_CHANNEL_ID if DEBUG else UPDATE_CHANNEL_ID)
        if channel:
            file = discord.File(create_report_image(), filename='update.png')
            await channel.send(file=file, delete_after=960) # type: ignore
    except Exception as e:
        return e

@client.event
async def on_ready():
    channel = client.get_channel(TESTING_CHANNEL_ID if DEBUG else UPDATE_CHANNEL_ID)
    if not send_update.is_running():
        send_update.start()

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    content: str = message.content.strip().lower() # type: ignore
    command, args = content.split(' ')[0], ' '.join(content.split(' ')[1:])
    if command in ['r', 'room']:
        if args[0] == 'a':
            df = find_by({'s': '1'}, ROOMS_DB)
            df = df[df['r'] > 100]
            df['r'] = df['r'].astype(str)
            message_content = str(len(df)) + ' Rooms Available\n'
            message_content += ('Available Rooms: ' + ','.join(df['r'].to_list()))
            embed = discord.Embed(title='Available Rooms', description=message_content)
            await message.reply(embed=embed)
        elif args[0] == 'b':
            df = find_by({'s': '2'}, ROOMS_DB)
            df = df[df['r'] > 100]
            df['r'] = df['r'].astype(str)
            message_content = str(len(df)) + ' Rooms Booked\n'
            message_content += ('Booked Rooms: ' + ','.join(df['r'].to_list()))
            embed = discord.Embed(title='Booked Rooms', description=message_content)
            await message.reply(embed=embed)
        else:
            if ',' in args:
                for room in args.split(','):
                    room = room.strip()
    if command in ['s', 'status']:
        df = read_csv(ROOMS_DB)
        dormitory, booked, available = 0, 0, 0
        for idx, row in df.iterrows():
            if row['r'] >= 1 and row['r'] <= 16:
                if row['s'] == 2:
                    dormitory += 1
            else:
                if row['s'] == 2:
                    booked += 1
                elif row['s'] == 1:
                    available += 1
        img = create_report_image()
        file = discord.File(img, filename='update.png')
        embed = discord.Embed(title='Status', description='Dormitory: ' + str(dormitory) + ' bed in use.\nBooked: ' + str(booked) + '\nAvailable: ' + str(available))
        try:
            await message.reply(embed=embed, file=file)
        except Exception as err:
            print(err)
    if command == 'u' or command == 'update':
        if args.startswith("src") and message.attachments:
            for attachment in message.attachments:
                file_name = attachment.filename
                await attachment.save(os.path.join('src', file_name)) # type: ignore
                print('File saved: src\\' + file_name)
        elif args.startswith("template")  and message.attachments:
            for attachment in message.attachments:
                file_name = attachment.filename
                await attachment.save(os.path.join('src', 'templates', file_name)) # type: ignore
                print('File saved: src\\templates' + file_name)
        else:
            for attachment in message.attachments:
                file_name = attachment.filename
                await attachment.save(file_name) # type: ignore
                print('File saved: ' + file_name)
        await message.reply('File updated successfully.')
        process_list = {process.pid: process.cmdline()[-1] for process in psutil.process_iter() if process.name().lower() in ['python.exe', 'pythonw.exe']}
        os.startfile('restart.py')
        for pid, pname in process_list.items():
            if "main.py" in pname or "main.pyw" in pname:
                os.kill(pid, signal.SIGTERM)
    if command == 'fetch':
        if args.startswith('dataset'):
            zip_buffer = io.BytesIO()
            with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zip_file:
                zip_file.write(CUSTOMERS_DB)
                zip_file.write(REGISTER_DB)
                zip_file.write(TRANSACTIONS_DB)
                zip_file.write(ROOMS_DB)
            zip_buffer.seek(0)
            zipped = discord.File(zip_buffer, filename='dataset.zip')
            await message.reply(file=zipped, content='Files Uploaded Successfully.')
        elif args.startswith('src'):
            try:
                zip_buffer = io.BytesIO()
                with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zip_file:
                    src = os.path.join('src')
                    for file_src in os.listdir(src):
                        cnt = os.path.join(src, file_src)
                        if os.path.isdir(cnt):
                            for sub_folder in os.listdir(cnt):
                                cnt_sub = os.path.join(cnt, sub_folder)
                                zip_file.write(cnt_sub)
                        else:
                            zip_file.write(cnt)
                zip_buffer.seek(0)
                zipped = discord.File(zip_buffer, filename='src.zip')
                await message.reply(file=zipped, content='File Uploaded Successfully.')
            except Exception as err:
                await message.reply("Error: " + str(err))
        elif args.startswith('register'):
            try:
                register = get_register_detail()
                register_str = register.to_csv(index=False)
                buffer = io.BytesIO(register_str.encode('utf-8'))
                buffer.seek(0)
                file = discord.File(buffer, filename="register.csv")
                await message.reply(file=file)
            except Exception as err:
                await message.reply('Error: ' + str(err))
        else:
            await message.reply('Unable to extract \'fetch [args]\'')
    if command == 'delete':
        await message.channel.purge(limit=10 + 1) # type: ignore
    
    if command.startswith('thanks'):
        await message.reply('Your Welcome. \nTo get all command type **\'h\'** or **help**.')
    
    if command.startswith('okay'):
        await message.reply('👍')
    
    if command in ['h' or 'help']:
        embed = discord.Embed(title='📌 Help Menu', color=0xffc0cb, description='1. **\'r\' or \'room\':** \n\ta - to get available rooms\n\tb - to get booked rooms\n\t1,2,3...408 - to get room details [Under Development]\n\n2. **\'s\' or \'status\': **Get an detailed image containing booking status and current money available\n\n3. **\'Delete: \'** Delete last 10 messages.\n\n4. **\'h\' or \'help\': To Get This Menu.**')
        await message.reply(embed=embed)