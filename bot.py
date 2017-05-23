#!/usr/bin/python3

import asyncio
import discord
from discord.ext import commands
import random
import requests

google_api='token'
command_list=["!test","!sleep","!image","!jason","!help"]

client = discord.Client()

@client.event
@asyncio.coroutine
def on_ready():
    print('Logged in as {0} - {1}'.format(client.user.name, client.user.id))

@client.event
@asyncio.coroutine
def on_message(message):
    if message.content.startswith('!test'):
        chosen = random.choice(list(client.get_all_members()))
        yield from client.send_message(message.channel, "Here is a random member to harass:")
        yield from client.send_message(message.channel, " - ".join([chosen.name,chosen.status.name]))
    elif message.content.startswith('!sleep'):
        yield from asyncio.sleep(5)
        yield from client.send_message(message.channel, "Sleeping. Zzzzz...")
    elif message.content.startswith('!help'):
        yield from client.send_message(message.channel, "Fuck off")
        yield from asyncio.sleep(5)
        commands = "".join(["Commands are: ",", ".join(command_list)])
        yield from client.send_message(message.channel, commands)
    elif message.content.startswith('!image'):
        search = message.content.split(" ")
        del search[0]
        if search:
            query = " ".join(search)
            if len(search) < 100:
                url = (
                    "https://www.googleapis.com/customsearch/v1?q={}".format(search) +
                    "&cx=CUSTOMSEARCHCX&searchType=image" +
                    "&key={}".format(google_api))
                r = requests.get(url)
                response = r.json()["items"][0]["link"]
                yield from client.send_message(message.channel, response)
            else:
                yield from client.send_message(message.channel, "Query too big!")
        else:
            yield from client.send_message(message.channel, "Usage: !image <search term>")
    elif message.content.startswith('!jason'):
        r = requests.get("http://quandyfactory.com/insult/json")
        insult = r.json()["insult"]
        yield from client.send_message(message.channel, insult.replace("Thou art","Jason is"))
    elif message.content.startswith('!'):
        commands = "".join(["Commands are: ",", ".join(command_list)])
        yield from client.send_message(message.channel, commands)

client.run('token')
