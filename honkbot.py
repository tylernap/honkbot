import datetime
import discord
import logging
import os
import pytz
import sys
from bs4 import BeautifulSoup
import requests
from typing import Optional

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
            "!insult",
            "!jacket",
            "!banner"
        ]

        self.eamuse_maintenance = {
            "normal": (
                datetime.time(hour=20, tzinfo=pytz.utc),
                datetime.time(hour=22, tzinfo=pytz.utc)
            ),
            "extended": (
                datetime.time(hour=17, tzinfo=pytz.utc),
                datetime.time(hour=22, tzinfo=pytz.utc)
            ),
            "us": (
                datetime.time(hour=12, tzinfo=pytz.utc),
                datetime.time(hour=17, tzinfo=pytz.utc)
            ),
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
        elif message.content.startswith('!jacket'):
            await self.get_jacket(message)
        elif message.content.startswith('!banner'):
            await self.get_banner(message)

        elif "honk" in message.content.lower() and message.author != self.client.user:
            # HONK WINS AGAIN
            if "Skeeter" in message.author.name:
                await self.client.send_message(message.channel, "beep")
            else:
                await self.client.send_message(message.channel, "HONK!")

        elif message.content.startswith('!'):
            commands = "".join(["Commands are: ", ", ".join(self.command_list)])
            await self.client.send_message(message.channel, commands)

    def get_display_time(self, timing_type):
        """
        Get a display time for today's eAmusement maintenance time. Includes an
        emoji for if the current time is within that time.

        Uses the timing_types: "us", "normal", "extended" from self
        """
        today = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        begin_datetime = datetime.datetime.combine(today.date(), self.eamuse_maintenance[timing_type][0])
        end_datetime = datetime.datetime.combine(today.date(), self.eamuse_maintenance[timing_type][1])
        if begin_datetime <= today <= end_datetime:
            emoji = ":x:"
        else:
            emoji = ":white_check_mark:"
        begin_time = begin_datetime.astimezone(pytz.timezone("America/New_York"))
        end_time = end_datetime.astimezone(pytz.timezone("America/New_York"))
        return f"{emoji} - {begin_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"

    def is_extended_maintenance_time(self):
        """
        This function returns true if this represents the Monday that Americans
        have to deal with maintenance.

        Maintenance is on the Third Tuesday in Japan.

        Gotchas:
            -The second Monday in America can be the Third Tuesday in Japan.
            -We literally don't care about this at all if it's Tuesday in
             in America, even if it's Tuesday in Japan
            -We DO care about it if it's Monday in America but still Monday in Japan

        :return: True if this is a Monday that Americans have to deal with maintenance
                 False if it's not
        """
        today_in_japan = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone("Japan"))
        tomorrow_in_japan = today_in_japan + datetime.timedelta(days=1)
        today_in_eastern = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone("America/New_York"))

        # If it's Monday in America, and either the third Tuesday or the Monday before that in Japan
        if today_in_eastern.weekday() == 0 and (
                (today_in_japan.weekday() == 1 and 15 <= today_in_japan.day <= 21) or (
                tomorrow_in_japan.weekday() == 1 and 15 <= tomorrow_in_japan.day <= 21)):
            return True
        return False

    async def get_eamuse_maintenance(self, message):
        """
        Gets eAmusement maintenance time.

        DDR (US Servers) - Third Monday of the month from 12 to 5 (?)
        Everything else - Sun-Thurs from 4 to 6. Third Monday 1 to 6 

        Required:
        """

        if self.is_extended_maintenance_time():
            ddr_message = self.get_display_time("us")
            other_message = self.get_display_time("extended")
        else:
            ddr_message = ":white_check_mark: - no maintenance today"
            other_message = self.get_display_time("normal")

        await self.client.send_message(message.channel, f"DDR: {ddr_message}")
        await self.client.send_message(message.channel, f"Other: {other_message}")

    async def get_insult(self, message, name):
        """
        Returns a scathing insult about the given name

        Required:
        name (str) - name of person to insult
        """
        r = requests.get("http://quandyfactory.com/insult/json")
        insult = r.json()["insult"]
        await self.client.send_message(message.channel, insult.replace("Thou art", f"{name} is"))

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
                                f"The Any% record for {game_name} is {record} by {user_name}")

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
                cx_id = "009855409252983983547:3xrcodch8sc"
                url = (
                        f"https://www.googleapis.com/customsearch/v1?q={search}" +
                        f"&cx={cx_id}&searchType=image" + f"&key={self.google_api}"
                )
                r = requests.get(url)
                try:
                    response = r.json()["items"][0]["link"]
                    await self.client.send_message(message.channel, response)
                except KeyError:
                    await self.client.send_message(message.channel,
                                                   f"No results found for {query} :(")
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
                google_url = "https://www.googleapis.com/youtube/v3/search?part=snippet&type=video"
                search_query = f"&q={query}&key={self.google_api}"
                r = requests.get(f"{google_url}{search_query}")
                try:
                    response = r.json()["items"][0]["id"]["videoId"]
                except IndexError:
                    await self.client.send_message(
                        message.channel,
                        f"Could not find any videos with search {query}"
                    )
                    return

                if response:
                    await self.client.send_message(message.channel, f"https://youtu.be/{response}")
                else:
                    await self.client.send_message(message.channel,
                                                   f"Could not find any videos with search {query}")
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
            await self.client.send_message(
                message.channel, "".join(["Usage: !join [", ", ".join(allowed_roles), "]"]))
            return
        role = message.content.split(" ")[1]
        if role not in allowed_roles:
            await self.client.send_message(
                message.channel, "".join(["Allowed roles are: ", ", ".join(allowed_roles)]))
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

    def search_remy_song(self, query: str) -> Optional[BeautifulSoup]:
        """
        Tries to find a certain song on RemyWiki

        MediaWiki tries to match an exact article title. If it doesn't find the
        exact title, it gives you a page with a list of suggestions. This
        leverages that by either going to the direct page, or going to the first
        page in the list of results.

        :param query: a string representing something that's supposed to be a
            song name to find
        :return: a BeautifulSoup object representing a RemyWiki page for a song,
            or None, representing a lack of results
        """
        search_data = {'search': f"{query} incategory:\"Songs\""}
        remy_search = requests.post('http://remywiki.com/index.php', data=search_data)
        remy_data = BeautifulSoup(remy_search.text, 'html.parser')
        if remy_data.title.string.lower().startswith(query):
            return remy_data
        else:
            first_result = remy_data.find("ul", {"class": "mw-search-results"})
            if first_result:
                song_result = requests.post(f"http://remywiki.com{first_result.li.div.a['href']}")
                return BeautifulSoup(song_result.text, 'html.parser')
            else:
                return None

    def get_remy_image(self, query: str, image_type: str = 'jacket') -> str:
        """
        Gets an image (or a message about no image) from a RemyWiki song page.

        This is intended to be used for jackets or banners. This searches the
        song page for "song name's jacket" or "song name's banner" and returns
        the image connected to that.

        :param query: a string representing something that's supposed to be a
            song name to find
        :param image_type: Either "jacket" or "banner", default "jacket"
        :return: a response fitting for the bot to return, either the requested
            image or a message describing what it found instead
        """
        remy_data = self.search_remy_song(query)
        if remy_data is not None:
            images = remy_data.find_all("div", {"class": "thumbinner"})
            for image in images:
                if image_type in image.find("div", {"class": "thumbcaption"}).text:
                    return f"http://remywiki.com{image.find('img')['src']}"

            song_title = remy_data.find("h1", {"id": "firstHeading"}).text
            if song_title.lower() == query.lower():
                return f"{song_title} does not have a {image_type}"
            else:
                return f"{query} seems to be the song {song_title} but it does not have a {image_type}"
        else:
            return f"Could not find a song that looks like: {query}"

    async def get_jacket(self, message):
        _, _, query = message.content.partition(" ")
        response = self.get_remy_image(query, 'jacket')
        await self.client.send_message(message.channel, response)

    async def get_banner(self, message):
        _, _, query = message.content.partition(" ")
        response = self.get_remy_image(query, 'banner')
        await self.client.send_message(message.channel, response)


if "__main__" in __name__:
    dotenv.load_dotenv()
    discord_api_key = os.getenv("DISCORD_API_KEY")
    speedrun_api_key = os.getenv("SPEEDRUN_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    bot = Honkbot(discord_api_key, speedrun_api_key, google_api_key)
    bot.run()
