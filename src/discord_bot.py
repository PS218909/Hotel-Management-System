import discord
from .util import *

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    channel = client.get_channel(1399468788969377812)
    if channel:
        await channel.send('Hello I am online!') # type: ignore
    else:
        print(str(channel) + 'not found')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    message_ = message.content.lower().strip()
    if message_.startswith('room ') or message_.startswith('r '):
        room_no = ' '.join(message.content.split(' ')[1:])
        for i in room_no.split(','):
            i = i.strip()
            detail = get_room_details(int(i))
            if detail != {}:
                embed = discord.Embed(title=str(i), description='**Name: **' + str(detail['name']) + '\n**Phone: **' + str(detail['phone']) + '\n**Purpose Of Visit: **' + str(detail['pov']) + '\n**ID: **' + str(detail['id_type']) + ' ' + str(detail['id_detail']) + '\n**Amount Paid: **' + detail['amt_paid'])
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
