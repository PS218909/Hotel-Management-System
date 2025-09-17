import discord
from .util import *
from .config import DISCORD_TESTING_CHANNEL_ID, DISCORD_UPDATE_CHANNEL_ID

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    channel = client.get_channel(DISCORD_TESTING_CHANNEL_ID)
    if channel:
        await channel.send('Hello I am online!') # type: ignore
    else:
        print(str(channel) + 'not found')
    channel_2 = client.get_channel(DISCORD_UPDATE_CHANNEL_ID)
    if channel_2:
        rooms = get_data(ROOMS_DB)
        available = 0
        booked = 0
        dor = 0
        for i in rooms:
            if int(i['Room No.']) < 100:
                if i['Status'] == 2:
                    dor += 1
                continue
            if i['Status'] == 1:
                available += 1
            else:
                booked += 1
        embed = discord.Embed(title='Status', description='Dormiory: ' + str(dor) + '\nAvailable: ' + str(available) + '\nBooked: ' + str(booked))
        await channel_2.send(content="Before sleeping the status was:", embed=embed) # type: ignore
    else:
        print(str(channel_2)+ ' Not Found')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    message_ = message.content.lower().strip()
    if message_.startswith('room ') or message_.startswith('r '):
        if message_.split(" ")[1].strip().lower() == "a":
            rooms = get_data(ROOMS_DB)
            room_no = ','.join([str(i['Room No.']) for i in rooms if i['Status'] == 2])
        else:
            room_no = ' '.join(message.content.split(' ')[1:])
        for i in room_no.split(','):
            i = i.strip()
            detail = get_room_details(int(i))
            time_passed = (datetime.now(ZoneInfo('Asia/Kolkata')).replace(tzinfo=None) - datetime.strptime(detail['check_in'], "%Y-%m-%dT%H:%M"))
            time_passed = str(time_passed.days) + " Days " + str(time_passed.seconds // (60 * 60)) + " Hours"
            if detail != {}:
                embed = discord.Embed(title=str(i), description='**Name: **' + str(detail['name']) + '\n**Phone: **' + str(detail['phone']) + '\n**Purpose Of Visit: **' + str(detail['pov']) + '\n**ID: **' + str(detail['id_type']) + ' ' + str(detail['id_detail']) + '\n**Amount Paid: **' + str(detail['amt_paid']) + '\nTime Passed: ' + str(time_passed))
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(title=str(i), description='Available')
                await message.channel.send(embed=embed)
    elif message_.startswith('delete '):
        amt = int(message_.split(' ')[1])
        await message.channel.purge(limit=amt+1)
    elif message_ in ['status', 's']:
        rooms = get_data(ROOMS_DB)
        available = 0
        booked = 0
        for i in rooms:
            if int(i['Room No.']) < 100:
                continue
            if i['Status'] == 1:
                available += 1
            else:
                booked += 1
        embed = discord.Embed(title='Status', description='Available: ' + str(available) + '\nBooked: ' + str(booked))
        await message.channel.send(embed=embed)
    elif message_ in ['booked', 'b']:
        rooms = get_data(ROOMS_DB)
        contain = ','.join([str(i['Room No.']) for i in rooms if i['Status'] == 2])
        if contain == '':
            contain = 'None'
        embed = discord.Embed(title='Booked Room\'s', description=contain)
        await message.channel.send(embed=embed)
    elif message_ in ['available', 'a']:
        rooms = get_data(ROOMS_DB)
        contain = ','.join([str(i['Room No.']) for i in rooms if i['Status'] == 1])
        if contain == '':
            contain = 'None'
        embed = discord.Embed(title='Available Room\'s', description=contain)
        await message.channel.send(embed=embed)