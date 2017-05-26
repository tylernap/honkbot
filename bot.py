#!/usr/bin/python3

import asyncio
import discord
from discord.ext import commands
import random
import requests

speedrun_api='token'
google_api='token'
command_list=["!test","!record","!image","!jason","!help"]

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
    elif message.content.startswith('!record'):
        search = message.content.lower().split(" ")
        del search[0]
        if search:
            auth = {"Authorization":"Token {}".format(speedrun_api)}
            query = " ".join(search)
            results = []
            if len(search) < 100:
                baseUrl = "http://www.speedrun.com/api/v1/"
                apiNext = "".join([baseUrl, "games"])
                while apiNext:
                    r = requests.get(apiNext,headers=auth)
                    for game in r.json()["data"]:
                        if query in game['names']['international'].lower():
                            results.append(game)
                    nextPage = ""
                    for page in r.json()["pagination"]["links"]:
                        if "next" in page['rel']:
                            nextPage = page['uri']
                    apiNext = nextPage
                if results:
                    if len(results) = 1:
                        gameId = results[0]["id"]
                        r = requests.get("".join([baseUrl,"games/",gameId]),headers=auth)
                        gameName = r.json()['data']['names']['international']
                        r = requests.get(
                            "".join([baseUrl,"games/",gameId,"/categories"]),headers=auth)
                        gameCategory = ""
                        for category in r.json()['data']:
                            if category['name'].startswith('Any%'):
                                gameCategory = category['category']
                                break
                        if gameCategory:
                            for link in gameCategory['links']:
                                if "records" in link['rel']:
                                    gameRecords = link['uri']
                            r = requests.get(gameRecords, headers=auth)
                            run = r.json()['data'][0]['runs'][0]['run']
                            record = run['times']['realtime'][2:]
                            userId = run['players'][0]['id']
                            r = requests.get("".join([baseUrl,"/users/",userId]),headers=auth)
                            userName = r.json()['data']['names']['international']

                            yield from client.send_message(
                                message.channel,
                                "The record for {0} is {1} by {2}".format(gameName,record,userName))
                
                        else:
                            yield from client.send_message(
                                message.channel,
                                "There are no Any% records for {}".format(gameName))
                    elif len(results) < 5:
                        pass
                    else:
                        pass
                else:
                    yield from client.send_message(
                        message.channel,
                        "No games with that name found!")
            yield from client.send_message(
                message.channel,
                "You gotta give me something to look for...")
    elif message.content.startswith('!'):
        commands = "".join(["Commands are: ",", ".join(command_list)])
        yield from client.send_message(message.channel, commands)

client.run('token')
