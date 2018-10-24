from calendar import monthrange
import datetime
import discord
import logging
import os
import pytz
import requests
import sys

from discord.errors import Forbidden
import dotenv

logging.basicConfig(stream=sys.stdout, level=logging.WARN)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Starting Honkbot...")


class Honkbot:
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
        bot.run()
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

        self.eamuse_maintenance = {
            "normal": ("20:00", "22:00"),
            "extended": ("17:00", "22:00"),
            "us": ("12:00", "17:00")
        }

        self.discord_api = discord_api
        self.speedrun_api = speedrun_api
        self.google_api = google_api

        self.client = discord.Client()

        self.lastRecordSearch = ""

        self.on_ready = self.client.event(self.on_ready)
        self.on_message = self.client.event(self.on_message)

    def run(self):
        self.client.run(self.discord_api)

    # @self.client.event
    async def on_ready(self):
        logger.info('Logged in as {0} - {1}'.format(self.client.user.name, self.client.user.id))

    # @self.client.event
    # @asyncio.coroutine
    async def on_message(self, message):
        if message.content.startswith('!test'):
            test = "test"
            await self.client.send_message(message.author, test)

        elif message.content.startswith('!join'):
            await self.set_channel_role(message)

        elif message.content.startswith('!help'):
            commands = "".join(["Commands are: ", ", ".join(self.command_list)])
            await self.client.send_message(message.channel, commands)

        elif message.content.startswith('!youtube'):
            await self.search_youtube(message)
        elif message.content.startswith('!image'):
            await self.search_google_images(message)
        elif message.content.startswith('!insult'):
            if len(message.content.lower().split(" ")) > 1:
                name = message.content.lower().split(" ")[1]
            else:
                await self.client.send_message(message.channel, "No one to insult :(")
                return
            await self.get_insult(message, name=name)
        elif message.content.startswith('!ranatalus'):
            await self.get_insult(message, name="ranatalus")
        elif message.content.startswith('!record'):
            await self.get_record(message)
        elif message.content.startswith('!eamuse'):
            await self.get_eamuse_maintenance(message)

        elif "honk" in message.content.lower() and message.author != self.client.user:
            # HONK WINS AGAIN
            if "Skeeter" in message.author.name:
                await self.client.send_message(message.channel, "beep")
            else:
                await self.client.send_message(message.channel, "HONK!")

        elif message.content.startswith('!'):
            commands = "".join(["Commands are: ", ", ".join(self.command_list)])
            await self.client.send_message(message.channel, commands)

    async def get_eamuse_maintenance(self, message):
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
        first_monday = (0 - bom) % 7 + 1
        third_monday = range(first_monday, days+1, 7)[2]
        if today.day == third_monday:
            maint['ddr'] = self.eamuse_maintenance['us']
            maint['other'] = self.eamuse_maintenance['extended']
        else:
            maint['ddr'] = None
            maint['other'] = self.eamuse_maintenance['normal']

        if maint['ddr']:
            begin_time = east_time.replace(hour=int(maint['ddr'][0].split(":")[0]), minute=0)
            end_time = east_time.replace(hour=int(maint['ddr'][1].split(":")[0]), minute=0)
            if begin_time <= east_time <= end_time:
                await self.client.send_message(
                    message.channel,
                    "DDR: :x: - {0}-{1}".format(maint['ddr'][0], maint['ddr'][1]))
            else:
                await self.client.send_message(
                    message.channel,
                    "DDR: :white_check_mark: - {0}-{1}".format(maint['ddr'][0], maint['ddr'][1]))

            begin_time = today.replace(hour=int(maint['other'][0].split(":")[0]), minute=0)
            end_time = today.replace(hour=int(maint['other'][1].split(":")[0]), minute=0)
            if (
                    begin_time.astimezone(pytz.timezone("America/New_York"))
                    <= east_time <= end_time.astimezone(pytz.timezone("America/New_York"))
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
            begin_time = today.replace(hour=int(maint['other'][0].split(":")[0]), minute=0)
            end_time = today.replace(hour=int(maint['other'][1].split(":")[0]), minute=0)
            if east_time.weekday() in [4, 5]:
                await self.client.send_message(
                    message.channel, "Other: :white_check_mark: - no maintenance today")
            else:
                if (
                        begin_time.astimezone(pytz.timezone("America/New_York"))
                        <= east_time <= end_time.astimezone(pytz.timezone("America/New_York"))
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

    async def get_insult(self, message, name):
        """
        Returns a scathing insult about the given name

        Required:
        name (str) - name of person to insult
        """
        r = requests.get("http://quandyfactory.com/insult/json")
        insult = r.json()["insult"]
        await self.client.send_message(message.channel, insult.replace("Thou art", "{0} is".format(name)))

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
            auth = {"Authorization": "Token {}".format(self.speedrun_api)}
            query = " ".join(search)
            results = []
            if len(search) < 100:
                base_url = "http://www.speedrun.com/api/v1/"
                api_next = "".join([base_url, "games?name={}".format(query)])
                while api_next:
                    r = requests.get(api_next, headers=auth)
                    for game in r.json()["data"]:
                        results.append(game)
                    next_page = ""
                    for page in r.json()["pagination"]["links"]:
                        if "next" in page['rel']:
                            next_page = page['uri']
                    api_next = next_page
                if results:
                    if query == self.lastRecordSearch:
                        results = [results[0]]
                    if len(results) == 1:
                        game_id = results[0]["id"]
                        r = requests.get("".join([base_url, "games/", game_id]), headers=auth)
                        game_name = r.json()['data']['names']['international']
                        r = requests.get(
                            "".join([base_url, "games/", game_id, "/categories"]), headers=auth)
                        game_category = ""
                        for category in r.json()['data']:
                            if category['name'].startswith('Any%'):
                                game_category = category
                                break
                        game_records_url = ""
                        if game_category:
                            for link in game_category['links']:
                                if "records" in link['rel']:
                                    game_records_url = link['uri']
                            r = requests.get(game_records_url, headers=auth)
                            run = r.json()['data'][0]['runs'][0]['run']
                            record = run['times']['realtime'][2:]
                            user_id = run['players'][0]['id']
                            r = requests.get("".join([base_url, "users/", user_id]), headers=auth)
                            user_name = r.json()['data']['names']['international']

                            await self.client.send_message(
                                message.channel,
                                "The Any% record for {0} is {1} by {2}".format(game_name, record, user_name))
                
                        else:
                            await self.client.send_message(
                                message.channel,
                                "There are no Any% records for {}".format(game_name))
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
                    "&key={}".format(self.google_api))
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
                url = "https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q={0}&key={1}"\
                    .format(query, self.google_api)
                r = requests.get(url)
                try:
                    response = r.json()["items"][0]["id"]["videoId"]
                except IndexError:
                    await self.client.send_message(message.channel, "Could not find any videos with search {0}"
                                                   .format(query))
                    return

                if response:
                    await self.client.send_message(message.channel, "https://youtu.be/{0}".format(response))
                else:
                    await self.client.send_message(message.channel, "Could not find any videos with search {0}"
                                                   .format(query))
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

        allowed_roles = ['OH', 'MI', 'KY', 'PA', 'IN', 'NY']
        if len(message.content.split(" ")) != 2:
            await self.client.send_message(message.channel, "".join(["Usage: !join [", ", ".join(allowed_roles), "]"]))
            return
        role = message.content.split(" ")[1]
        if role not in allowed_roles:
            await self.client.send_message(message.channel, "".join(["Allowed roles are: ", ", ".join(allowed_roles)]))
        else:
            role_object = discord.utils.get(message.server.roles, name=role)
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
    discord_api_key = os.getenv("DISCORD_API_KEY")
    speedrun_api_key = os.getenv("SPEEDRUN_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    bot = Honkbot(discord_api_key, speedrun_api_key, google_api_key)
    bot.run()
