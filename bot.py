#!/usr/bin/python3

import asyncio
import discord
from discord.ext import commands
from discord.errors import Forbidden
import random
import requests

# FIXME: Fill these out with your API tokens
discord_api=""
speedrun_api=""
google_api=""

command_list=["!join","!image","!youtube","!jason","!help"]

lastRecordSearch = ""

client = discord.Client()

@client.event
@asyncio.coroutine
def on_ready():
    print('Logged in as {0} - {1}'.format(client.user.name, client.user.id))

@client.event
@asyncio.coroutine
# TODO: This doesnt work at all lmao.
# This should send to the individual 
def on_member_join(member):
    channel = member.server.default_channel()
    message = "Welcome {0} to the discord channel!!!"
    yield from client.send_message(channel, message)

@client.event
@asyncio.coroutine
def on_message(message):
    if message.content.startswith('!test'):
        chosen = random.choice(list(client.get_all_members()))
        yield from client.send_message(message.channel, "Here is a random member to harass:")
        yield from client.send_message(message.channel, " - ".join([chosen.name,chosen.status.name]))

    elif message.content.startswith('!join'):
        allowed_roles = ['OH','MI','KY','PA']
        if len(message.content.split(" ")) != 2:
            yield from client.send_message(message.channel, "".join(["Usage: !join [", ", ".join(allowed_roles),"]"]))
            return
        role = message.content.split(" ")[1]
        if role not in allowed_roles:
            yield from client.send_message(message.channel, "".join(["Allowed roles are: ",", ".join(allowed_roles)]))
        else:
            server_roles = message.server.roles
            for server_role in server_roles:
                if server_role.name == role:
                    role_object = server_role
            try:
                if message.author.roles:
                    yield from client.replace_roles(message.author, role_object)
                else:
                    yield from client.add_roles(message.author, role_object) 
                yield from client.send_message(
                    message.channel, "Adding {0} to {1}".format(message.author.name, role))
            except Forbidden:
                yield from client.send_message(
                    message.channel, "I do not have permissions to assign roles right now. Sorry!")

    elif message.content.startswith('!help'):
        commands = "".join(["Commands are: ",", ".join(command_list)])
        yield from client.send_message(message.channel, commands)
    elif message.content.startswith('!youtube'):
        search = message.content.split(" ")
        del search[0]
        if search:
            query = " ".join(search)
            if len(query) < 250:
                url = "https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q={0}&key={1}".format(query, google_api)
                r = requests.get(url)
                try:
                    response = r.json()['items'][0]["id"]["videoId"]
                except IndexError:
                    yield from client.send_message(message.channel, "Could not find any videos with search {0}".format(query))
                    return

                if response:
                    yield from client.send_message(message.channel, "https://youtu.be/{0}".format(response))
                else:
                    yield from client.send_message(message.channel, "Could not find any videos with search {0}".format(query))
                    return
            else:
                yield from client.send_message(message.channel, "Query too long!")
                return
        else:
            yield from client.send_message(message.channel, "Usage: !youtube <search terms>")
    elif message.content.startswith('!image'):
        search = message.content.split(" ")
        del search[0]
        if search:
            query = " ".join(search)
            if len(query) < 150:
                url = (
                    "https://www.googleapis.com/customsearch/v1?q={}".format(search) +
                    "&cx=009855409252983983547:3xrcodch8sc&searchType=image" +
                    "&key={}".format(google_api))
                r = requests.get(url)
                try:
                    response = r.json()["items"][0]["link"]
                    yield from client.send_message(message.channel, response)
                except KeyError:
                    yield from client.send_message(message.channel, "No results found for {0} :(".format(query))
            else:
                yield from client.send_message(message.channel, "Query too big!")
        else:
            yield from client.send_message(message.channel, "Usage: !image <search term>")


    elif message.content.startswith('!jason'):
        r = requests.get("http://quandyfactory.com/insult/json")
        insult = r.json()["insult"]
        yield from client.send_message(message.channel, insult.replace("Thou art","Jason is"))


    elif message.content.startswith('!record'):
        global lastRecordSearch
        search = message.content.lower().split(" ")
        del search[0]
        if search:
            auth = {"Authorization":"Token {}".format(speedrun_api)}
            query = " ".join(search)
            results = []
            if len(search) < 100:
                baseUrl = "http://www.speedrun.com/api/v1/"
                apiNext = "".join([baseUrl, "games?name={}".format(query)])
                while apiNext:
                    r = requests.get(apiNext,headers=auth)
                    for game in r.json()["data"]:
                        results.append(game)
                    nextPage = ""
                    for page in r.json()["pagination"]["links"]:
                        if "next" in page['rel']:
                            nextPage = page['uri']
                    apiNext = nextPage
                if results:
                    if query == lastRecordSearch:
                        results = [results[0]]
                    if len(results) == 1:
                        gameId = results[0]["id"]
                        r = requests.get("".join([baseUrl,"games/",gameId]),headers=auth)
                        gameName = r.json()['data']['names']['international']
                        r = requests.get(
                            "".join([baseUrl,"games/",gameId,"/categories"]),headers=auth)
                        gameCategory = ""
                        for category in r.json()['data']:
                            if category['name'].startswith('Any%'):
                                gameCategory = category
                                break
                        if gameCategory:
                            for link in gameCategory['links']:
                                if "records" in link['rel']:
                                    gameRecords = link['uri']
                            r = requests.get(gameRecords, headers=auth)
                            run = r.json()['data'][0]['runs'][0]['run']
                            record = run['times']['realtime'][2:]
                            userId = run['players'][0]['id']
                            r = requests.get("".join([baseUrl,"users/",userId]),headers=auth)
                            userName = r.json()['data']['names']['international']

                            yield from client.send_message(
                                message.channel,
                                "The Any% record for {0} is {1} by {2}".format(gameName,record,userName))
                
                        else:
                            yield from client.send_message(
                                message.channel,
                                "There are no Any% records for {}".format(gameName))
                    elif len(results) < 5:
                        names = []
                        for result in results:
                            names.append(result['names']['international'])
                        yield from client.send_message(
                            message.channel,
                            "Multiple results. Do a search for the following: {}".format(
                                ", ".join(names)))
                        yield from client.send_message(
                            message.channel,
                            "If you want the first result, redo the search")
                    else:
                        yield from client.send_message(
                            message.channel,
                            "Too many results! Be a little more specific")
                else:
                    yield from client.send_message(
                        message.channel,
                        "No games with that name found!")
            lastRecordSearch = query
        else:
            yield from client.send_message(
                message.channel,
                "You gotta give me a game to look for...")

    elif "honk" in message.content.lower() and "bot4u" not in message.author.name:
        yield from client.send_message(message.channel, "HONK!")

    elif message.content.startswith('!'):
        commands = "".join(["Commands are: ",", ".join(command_list)])
        yield from client.send_message(message.channel, commands)

def main():
    while True:
        try:
            client.run(discord_api)
        except Exception as e:
            print("!!! Caught exception: {0}".format(e)

if "__main__" in __name__:
    main()
