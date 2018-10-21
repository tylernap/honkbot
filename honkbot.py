import asyncio
from calendar import monthrange
import datetime
import discord
import logging
import os
import pytz
import random
import requests
import sys
import time

from discord.ext import commands
from discord.errors import Forbidden
import dotenv

logging.basicConfig(stream=sys.stdout, level=logging.WARN)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.warn("Starting Honkbot...")

class Honkbot():
    """
    HONK

    A dumbass bot that interfaces with discord to do dumb stuff

    A list of things that it does:
    * Adds people to groups
    * Searches google for images
    * Searches youtube for videos
    * Insults people
    * Gives information on eAmuse downtime

    example:
        import honkbot
        bot = honkbot.Honkbot(discord_apikey)
    """

    def __init__(self, discord_api, speedrun_api=None, google_api=None):
        self.command_list = [
            "!join",
            "!image",
            "!youtube",
            "!ranatalus",
            "!eamuse",
            "!help",
            "!insult"
        ]

        self.eamuse_maint = {
            "normal": ("20:00", "22:00"),
            "extended": ("17:00", "22:00"),
            "us": ("12:00", "17:00")
        }

        self.discord_api = discord_api
        self.speedrun_api = speedrun_api
        self.google_api = google_api

        self.client = discord.Client()
        try:
            self.client.run(self.discord_api)
        except Exception as e:
            logger.error("!!! Caught exception: {0}".format(e))
            return False

        self.lastRecordSearch = ""

        self.on_ready = self.client.event(self.on_ready)
        self.on_message = self.client.event(self.on_message)

    #@self.client.event
    async def on_ready(self):
        logger.warn('Logged in as {0} - {1}'.format(self.client.user.name, self.client.user.id))

    #@self.client.event
    #@asyncio.coroutine
    async def on_message(self, message):
        if message.content.startswith('!test'):
            test = "test"
            await self.client.send_message(message.author, test)

        elif message.content.startswith('!join'):
            self.set_channel_role(message)

        elif message.content.startswith('!help'):
            commands = "".join(["Commands are: ",", ".join(self.command_list)])
            await self.client.send_message(message.channel, commands)

        elif message.content.startswith('!youtube'):
            self.search_youtube(message)
        elif message.content.startswith('!image'):
            self.search_google_images(message)
        elif message.content.startswith('!insult'):
            if len(message.content.lower().split(" ")) > 1:
                self.name = message.content.lower().split(" ")[1]
            else:
                await self.client.send_message(message.channel, "No one to insult :(")
                return
            self.get_insult(self.name)
        elif message.content.startswith('!ranatalus'):
            self.get_insult("ranatalus")
        elif message.content.startswith('!record'):
            self.get_record(message)
        elif message.content.startswith('!eamuse'):
            self.get_eamuse_maintenance()

        elif "honk" in message.content.lower() and "bot4u" not in message.author.name:
            # HONK WINS AGAIN
            if "Skeeter" in message.author.name:
                await self.client.send_message(message.channel, "beep")
            else:
                await self.client.send_message(message.channel, "HONK!")

        elif message.content.startswith('!'):
            commands = "".join(["Commands are: ",", ".join(self.command_list)])
            await self.client.send_message(message.channel, commands)

    async def get_eamuse_maintenance(self):
        """
        Gets eAmusement maintenance time.

        DDR (US Servers) - Third Monday of the month from 12 to 5 (?)
        Everything else - Sun-Thurs from 4 to 6. Third Monday 1 to 6 

        Required:
        """

        maint = {}
        today = datetime.datetime.utcnow()
        today = today.replace(tzinfo=pytz.utc)
        east_time = today.astimezone(pytz.timezone("America/New_York"))
        bom, days = monthrange(today.year, today.month)
        firstmonday = (0 - bom) % 7 + 1
        thirdmonday = range(firstmonday, days+1, 7)[2]
        if today.day == thirdmonday:
            maint['ddr'] = eamuse_maint['us']
            maint['other'] = eamuse_maint['extended']
        else:
            maint['ddr'] = None
            maint['other'] = eamuse_maint['normal']

        if maint['ddr']:
            begin_time = east_time.replace(hour=int(maint['ddr'][0].split(":")[0]),minute=0)
            end_time = east_time.replace(hour=int(maint['ddr'][1].split(":")[0]),minute=0)
            if east_time >= begin_time and east_time <= end_time:
                await self.client.send_message(
                    message.channel,
                    "DDR: :x: - {0}-{1}".format(maint['ddr'][0],maint['ddr'][1]))
            else:
                await self.client.send_message(
                    message.channel,
                    "DDR: :white_check_mark: - {0}-{1}".format(maint['ddr'][0],maint['ddr'][1]))

            begin_time = today.replace(hour=int(maint['other'][0].split(":")[0]),minute=0)
            end_time = today.replace(hour=int(maint['other'][1].split(":")[0]),minute=0)
            if (
                east_time >= begin_time.astimezone(pytz.timezone("America/New_York")) and
                east_time <= end_time.astimezone(pytz.timezone("America/New_York"))
            ):
                await self.client.send_message(
                    message.channel,
                    "Other: :x: - {0}-{1}".format(
                        begin_time.astimezone(pytz.timezone("America/New_York")).strftime("%H:%M"),
                        end_time.astimezone(pytz.timezone("America/New_York")).strftime("%H:%M")))
            else:
                await self.client.send_message(
                    message.channel,
                    "Other: :white_check_mark: - {0}-{1}".format(
                        begin_time.astimezone(pytz.timezone("America/New_York")).strftime("%H:%M"),
                        end_time.astimezone(pytz.timezone("America/New_York")).strftime("%H:%M")))
        else:
            await self.client.send_message(
                message.channel, "DDR: :white_check_mark: - no maintenance today")
            begin_time = today.replace(hour=int(maint['other'][0].split(":")[0]),minute=0)
            end_time = today.replace(hour=int(maint['other'][1].split(":")[0]),minute=0)
            if east_time.weekday() in [4,5]:
                await self.client.send_message(
                    message.channel, "Other: :white_check_mark: - no maintenance today")
            else:
                if (
                    east_time >= begin_time.astimezone(pytz.timezone("America/New_York")) and
                    east_time <= end_time.astimezone(pytz.timezone("America/New_York"))
                ):

                    await self.client.send_message(
                        message.channel,
                        "Other: :x: - {0}-{1}".format(
                            begin_time.astimezone(pytz.timezone("America/New_York")).strftime("%H:%M"),
                            end_time.astimezone(pytz.timezone("America/New_York")).strftime("%H:%M")))
                else:
                    await self.client.send_message(
                        message.channel,
                        "Other: :white_check_mark: - {0}-{1}".format(
                            begin_time.astimezone(pytz.timezone("America/New_York")).strftime("%H:%M"),
                            end_time.astimezone(pytz.timezone("America/New_York")).strftime("%H:%M")))

    async def get_insult(self, name):
        """
        Returns a scathing insult about the given name

        Required:
        name (str) - name of person to insult
        """
        r = requests.get("http://quandyfactory.com/insult/json")
        insult = r.json()["insult"]
        await self.client.send_message(message.channel, insult.replace("Thou art","{0} is".format(name)))


    async def get_record(self, message):
        """
        Accesses speedrun.com to get world record of given game

        Requires:
        message (obj) - message object from discord object
        """

        if not self.speedrun_api:
            await self.client.send_message(
                message.channel,
                "Sorry, cant do that right now! Ask your admin to enable"
            )
            return

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
                    if query == self.lastRecordSearch:
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

                            await self.client.send_message(
                                message.channel,
                                "The Any% record for {0} is {1} by {2}".format(gameName,record,userName))
                
                        else:
                            await self.client.send_message(
                                message.channel,
                                "There are no Any% records for {}".format(gameName))
                    elif len(results) < 5:
                        names = []
                        for result in results:
                            names.append(result['names']['international'])
                        await self.client.send_message(
                            message.channel,
                            "Multiple results. Do a search for the following: {}".format(
                                ", ".join(names)))
                        await self.client.send_message(
                            message.channel,
                            "If you want the first result, redo the search")
                    else:
                        await self.client.send_message(
                            message.channel,
                            "Too many results! Be a little more specific")
                else:
                    await self.client.send_message(
                        message.channel,
                        "No games with that name found!")
            self.lastRecordSearch = query
        else:
            await self.client.send_message(
                message.channel,
                "You gotta give me a game to look for...")

    async def search_google_images(self, message):
        """
        Returns an image from google from the given search terms

        Requires:
            message (obj) - message object from discord object
        """

        if not self.google_api:
            await self.client.send_message(
                message.channel,
                "Sorry, cant do that right now! Ask your admin to enable"
            )
            return

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
                    await self.client.send_message(message.channel, response)
                except KeyError:
                    await self.client.send_message(message.channel, "No results found for {0} :(".format(query))
            else:
                await self.client.send_message(message.channel, "Query too big!")
        else:
            await self.client.send_message(message.channel, "Usage: !image <search term>")

    async def search_youtube(self, message):
        """
        Returns an video from youtube from the given search terms

        Requires:
            message (obj) - message object from discord object
        """

        if not self.google_api:
            await self.client.send_message(
                message.channel,
                "Sorry, cant do that right now! Ask your admin to enable"
            )
            return

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
                    await self.client.send_message(message.channel, "Could not find any videos with search {0}".format(query))
                    return

                if response:
                    await self.client.send_message(message.channel, "https://youtu.be/{0}".format(response))
                else:
                    await self.client.send_message(message.channel, "Could not find any videos with search {0}".format(query))
                    return
            else:
                await self.client.send_message(message.channel, "Query too long!")
                return
        else:
            await self.client.send_message(message.channel, "Usage: !youtube <search terms>")


    async def set_channel_role(self, message):
        """
        Sets a role to a user based on the given input

        Requires:
            message (obj) - message object from discord object
        """

        allowed_roles = ['OH','MI','KY','PA', 'IN', 'NY']
        if len(message.content.split(" ")) != 2:
            await self.client.send_message(message.channel, "".join(["Usage: !join [", ", ".join(allowed_roles),"]"]))
            return
        role = message.content.split(" ")[1]
        if role not in allowed_roles:
            await self.client.send_message(message.channel, "".join(["Allowed roles are: ",", ".join(allowed_roles)]))
        else:
            server_roles = message.server.roles
            for server_role in server_roles:
                if server_role.name == role:
                    role_object = server_role
            try:
                if message.author.roles:
                    await self.client.replace_roles(message.author, role_object)
                else:
                    await self.client.add_roles(message.author, role_object) 
                await self.client.send_message(
                    message.channel, "Adding {0} to {1}".format(message.author.name, role))
            except Forbidden:
                await self.client.send_message(
                    message.channel, "I do not have permissions to assign roles right now. Sorry!")


if "__main__" in __name__:

    dotenv.load_dotenv()
    discord_api = os.getenv("DISCORD_API_KEY")
    speedrun_api = os.getenv("SPEEDRUN_API_KEY")
    google_api = os.getenv("GOOGLE_API_KEY")

    bot = Honkbot(discord_api) 
