# Python Standard Library
import datetime
import pytz
import requests

# Discord
import discord
from discord.ext import commands
from discord.errors import Forbidden


class Honkbot(commands.Cog):
    def __init__(self, logger, speedrun_api, google_api, bot=None):
        self.eamuse_maintenance = {
            "normal": (
                datetime.time(hour=20, tzinfo=pytz.utc),
                datetime.time(hour=22, tzinfo=pytz.utc),
            ),
            "extended": (
                datetime.time(hour=17, tzinfo=pytz.utc),
                datetime.time(hour=22, tzinfo=pytz.utc),
            ),
            "us": (
                datetime.time(hour=12, tzinfo=pytz.utc),
                datetime.time(hour=17, tzinfo=pytz.utc),
            ),
        }

        self.custom_roles = [
            "AKR",
            "CIN",
            "CLE",
            "COL",
            "DAY",
            "TOL",
            "MI",
            "KY",
            "PA",
            "IN",
            "NY",
            "CA",
            "Canada",
        ]

        self.bot = bot
        self.logger = logger
        self.speedrun_api = speedrun_api
        self.google_api = google_api

        self.lastRecordSearch = ""

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f"Logged in as {self.bot.user} - {self.bot.user.id}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if "honk" in message.content.lower():
            if "Skeeter" in message.author.name:
                await message.channel.send("beep")
            else:
                await message.channel.send("HONK!")
        if "dygma" in message.content.lower():
            await message.channel.send("whats dygma")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        self.logger.error(error)
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Use !help to see a list of commands")

    @commands.command()
    async def test(self, ctx):
        """
        Test if the bot is working
        """
        await ctx.send("test")

    @commands.command()
    async def join(self, ctx, *role_input: str):
        """
        Adds the given role to the command invoker

        Gives an error message if there are 0 or >1 roles specified, or if the
        specified role is not allowed.

        User Arguments:
            role: AKR, CIN, CLE, COL, DAY, TOL, MI, KY, PA, IN, NY, CA, Canada

        """
        role, message = self.get_role_from_input(ctx, role_input)
        if not role:
            return await ctx.send(message)
        try:
            if role not in ctx.author.roles:
                await ctx.author.add_roles(role)
                return await ctx.send(f"Adding {ctx.author.display_name} to {role}")
            else:
                return await ctx.send(f"{ctx.author.display_name} is already in {role}")
        except Forbidden:
            await ctx.send(
                "I do not have permissions to assign roles right now. Sorry!"
            )

    @commands.command()
    async def leave(self, ctx, *role_input: str):
        """
        Removes the given role from the command invoker

        Gives an error message if there are 0 or >1 roles specified, or if the
        specified role is not allowed.

        User Arguments:
            role: AKR, CIN, CLE, COL, DAY, TOL, MI, KY, PA, IN, NY, CA, Canada
        """
        role, message = self.get_role_from_input(ctx, role_input)
        if not role:
            return await ctx.send(message)
        try:
            if role in ctx.author.roles:
                await ctx.author.remove_roles(role)
                return await ctx.send(f"Removing {ctx.author.display_name} from {role}")
            else:
                return await ctx.send(f"{ctx.author.display_name} is not in {role}")
        except Forbidden:
            await ctx.send(
                "I do not have permissions to assign roles right now. Sorry!"
            )

    def get_role_from_input(self, ctx, role_input: tuple):
        """
        Turn a user's string from !join or !leave into a Discord Role object

        :param ctx: Discord Context (for accessing the Roles list)
        :param role_input: Tuple of Strings representing user input (split by spaces)
        :return: A tuple of either a Role or False, and an accompanying message
        """
        if len(role_input) != 1:
            return False, "Usage: !join [" + ", ".join(self.custom_roles) + "]"

        role = next((role for role in self.custom_roles if role_input[0].lower() == role.lower()), None)

        if role:
            return discord.utils.get(ctx.guild.roles, name=role), ""
        else:
            return False, "Allowed roles are: " + ", ".join(self.custom_roles)

    def get_display_time(self, timing_type):
        """
        Get a display time for today's eAmusement maintenance time. Includes an
        emoji for if the current time is within that time.

        Uses the timing_types: "us", "normal", "extended" from self
        """
        today = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        begin_datetime = datetime.datetime.combine(
            today.date(), self.eamuse_maintenance[timing_type][0]
        )
        end_datetime = datetime.datetime.combine(
            today.date(), self.eamuse_maintenance[timing_type][1]
        )
        if begin_datetime <= today <= end_datetime:
            emoji = ":x:"
        else:
            emoji = ":white_check_mark:"
        begin_time = begin_datetime.astimezone(pytz.timezone("America/New_York"))
        end_time = end_datetime.astimezone(pytz.timezone("America/New_York"))
        return f"{emoji} - {begin_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"

    @staticmethod
    def is_extended_maintenance_time():
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
        today_in_japan = datetime.datetime.utcnow().replace(
            tzinfo=pytz.timezone("Japan")
        )
        tomorrow_in_japan = today_in_japan + datetime.timedelta(days=1)
        today_in_eastern = datetime.datetime.utcnow().replace(
            tzinfo=pytz.timezone("America/New_York")
        )

        # If it's Monday in America, and either the third Tuesday or the Monday before that in Japan
        if today_in_eastern.weekday() == 0 and (
            (today_in_japan.weekday() == 1 and 15 <= today_in_japan.day <= 21)
            or (tomorrow_in_japan.weekday() == 1 and 15 <= tomorrow_in_japan.day <= 21)
        ):
            return True
        return False

    @commands.command()
    async def eamuse(self, ctx):
        """
        Gets eAmusement maintenance time.

        Japanese Servers: 5:00 AM to 7:00 AM JST every day
        Extended and US Servers: 3:00 AM to 7:00 AM JST on the third Tuesday
        """

        if self.is_extended_maintenance_time():
            ddr_message = self.get_display_time("us")
            other_message = self.get_display_time("extended")
        else:
            ddr_message = ":white_check_mark: - no maintenance today"
            other_message = self.get_display_time("normal")

        await ctx.send(f"DDR: {ddr_message}")
        await ctx.send(f"Other: {other_message}")

    @commands.command()
    async def insult(self, ctx, *name: str):
        """
        Returns a scathing insult about the given name.

        User Arguments:
            name: name of person to insult
        """
        if len(name) < 1:
            await ctx.send("No one to insult :(")
        else:
            r = requests.get("https://quandyfactory.com/insult/json")
            insult = r.json()["insult"]
            await ctx.send(insult.replace("Thou art", f"{' '.join(name)} is"))

    @commands.command()
    async def ranatalus(self, ctx):
        """
        Returns a scathing insult about this particular name.
        """
        await ctx.invoke(self.insult, "ranatalus")

    @commands.command()
    async def record(self, ctx, *, search: str = None):
        """
        Accesses speedrun.com to get world record of given game.

        User Arguments:
            search: the game to search for
        """

        if not self.speedrun_api:
            await ctx.send("Sorry, cant do that right now! Ask your admin to enable")
            return

        if search:
            auth = {"Authorization": "Token {}".format(self.speedrun_api)}
            results = []
            if len(search) < 100:
                base_url = "https://www.speedrun.com/api/v1/"
                api_next = "".join([base_url, "games?name={}".format(search)])
                while api_next:
                    r = requests.get(api_next, headers=auth)
                    for game in r.json()["data"]:
                        results.append(game)
                    next_page = ""
                    for page in r.json()["pagination"]["links"]:
                        if "next" in page["rel"]:
                            next_page = page["uri"]
                    api_next = next_page
                if results:
                    if search == self.lastRecordSearch:
                        results = [results[0]]
                    if len(results) == 1:
                        game_id = results[0]["id"]
                        r = requests.get(
                            "".join([base_url, "games/", game_id]), headers=auth
                        )
                        game_name = r.json()["data"]["names"]["international"]
                        r = requests.get(
                            "".join([base_url, "games/", game_id, "/categories"]),
                            headers=auth,
                        )
                        game_category = {}
                        for category in r.json()["data"]:
                            if category["name"].startswith("Any%"):
                                game_category = category
                                break
                        game_records_url = ""
                        if game_category:
                            for link in game_category["links"]:
                                if "records" in link["rel"]:
                                    game_records_url = link["uri"]
                            r = requests.get(game_records_url, headers=auth)
                            run = r.json()["data"][0]["runs"][0]["run"]
                            record = run["times"]["realtime"][2:]
                            user_id = run["players"][0]["id"]
                            r = requests.get(
                                "".join([base_url, "users/", user_id]), headers=auth
                            )
                            user_name = r.json()["data"]["names"]["international"]

                            await ctx.send(
                                f"The Any% record for {game_name} is {record} by {user_name}"
                            )

                        else:
                            await ctx.send(
                                "There are no Any% records for {}".format(game_name)
                            )
                    elif len(results) < 5:
                        names = []
                        for result in results:
                            names.append(result["names"]["international"])
                        await ctx.send(
                            "Multiple results. Do a search for the following: {}".format(
                                ", ".join(names)
                            )
                        )
                        await ctx.send("If you want the first result, redo the search")
                    else:
                        await ctx.send("Too many results! Be a little more specific")
                else:
                    await ctx.send("No games with that name found!")
            self.lastRecordSearch = search
        else:
            await ctx.send("You gotta give me a game to look for...")

    @commands.command()
    async def image(self, ctx, *, search: str = None):
        """
        Returns an image from Google from the given search terms.

        User Arguments:
            search: The terms to use on Google Images
        """

        if not self.google_api:
            await ctx.send("Sorry, cant do that right now! Ask your admin to enable")
            return

        if search:
            query = "".join(search)
            if len(query) < 150:
                cx_id = "009855409252983983547:3xrcodch8sc"
                url = (
                    f"https://www.googleapis.com/customsearch/v1?q={search}"
                    + f"&cx={cx_id}&safe=active&searchType=image"
                    + f"&key={self.google_api}"
                )
                r = requests.get(url)
                try:
                    response = r.json()["items"][0]["link"]
                    await ctx.send(response)
                except KeyError:
                    await ctx.send(f"No results found for {query} :(")
            else:
                await ctx.send("Query too big!")
        else:
            await ctx.send("Usage: !image <search term>")

    @commands.command()
    async def youtube(self, ctx, *, search: str = None):
        """
        Returns a video from YouTube from the given search terms

        User Arguments:
            search: The terms to use on YouTube
        """

        if not self.google_api:
            await ctx.send("Sorry, cant do that right now! Ask your admin to enable")
            return

        if search:
            query = "".join(search)
            if len(query) < 250:
                google_url = "https://www.googleapis.com/youtube/v3/search?part=snippet&type=video"
                search_query = f"&q={query}&key={self.google_api}"
                r = requests.get(f"{google_url}{search_query}")
                try:
                    response = r.json()["items"][0]["id"]["videoId"]
                except IndexError:
                    await ctx.send(f"Could not find any videos with search {query}")
                    return

                if response:
                    await ctx.send(f"https://youtu.be/{response}")
                else:
                    await ctx.send(f"Could not find any videos with search {query}")
            else:
                await ctx.send("Query too long!")
        else:
            await ctx.send("Usage: !youtube <search terms>")
