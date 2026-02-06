# Python Standard Library
import datetime
import pytz
import re

# Third party libraries
import requests

# Discord
import discord
from discord.ext import commands
from discord.errors import Forbidden

CUSTOM_ROLES = {
    "AKR": "Akron",
    "CIN": "Cincinnati",
    "CLE": "Cleveland",
    "COL": "Columbus",
    "DAY": "Dayton",
    "TOL": "Toledo",
    "MI": "Michigan",
    "KY": "Kentucky",
    "PA": "Pennsylvania",
    "IN": "Indiana",
    "NY": "New York",
    "CA": "California",
    "Canada": "Canada",
    "EX-OH": "Ex-Ohio",
}


class RoleDropdown(discord.ui.Select):
    def __init__(self, action="join"):
        options = [
            discord.SelectOption(label=label, description=description, value=label)
            for label, description in CUSTOM_ROLES.items()
        ]
        super().__init__(placeholder="Choose role", options=options)
        self.action = action

    async def callback(self, interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        try:
            if self.action == "join":
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role)

                    view = RoleView()
                    view.children[0].placeholder = "(Optional) Add another role"
                    return await interaction.response.edit_message(
                        content=f"Adding {interaction.user.display_name} to {self.values[0]}",
                        view=view,
                    )
                return await interaction.response.edit_message(
                    content=f"{interaction.user.display_name} is already in {self.values[0]}",
                    view=RoleView(),
                )
            elif self.action == "leave":
                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role)

                    view = RoleView(action="leave")
                    view.children[0].placeholder = "(Optional) Leave another role"
                    return await interaction.response.edit_message(
                        content=f"Removing {interaction.user.display_name} from {self.values[0]}",
                        view=view,
                    )
                return await interaction.response.edit_message(
                    content=f"{interaction.user.display_name} is not in {self.values[0]}",
                    view=RoleView(action="leave"),
                )
        except Forbidden:
            await self.respond_to_user(ctx, "I do not have permissions to assign roles right now!", view=RoleView())


class RoleView(discord.ui.View):
    def __init__(self, *, action="join", timeout=180):
        super().__init__(timeout=timeout)
        self.add_item(RoleDropdown(action=action))


class Honkbot(commands.Cog):
    def __init__(self, logger, speedrun_api, bot=None):
        self.eamuse_maintenance = {
            "daily": (
                datetime.time(hour=20, tzinfo=pytz.utc),
                datetime.time(hour=22, tzinfo=pytz.utc),
            ),
            "extended": (
                datetime.time(hour=17, tzinfo=pytz.utc),
                datetime.time(hour=22, tzinfo=pytz.utc),
            ),
        }

        self.messages = {
            "us_games": "US Servers (DDR White, IIDX Lightning)",
            "jp_games": "JP Servers (DDR Gold, IIDX Classic, All Other)",
            "website_down": "Login to e-amusement website unavailable during this time.",
            "card_down": "e-amusement card cannot be used during this time.",
        }

        self.custom_roles = [key for key in CUSTOM_ROLES.keys()]

        self.bot = bot
        self.logger = logger
        self.speedrun_api = speedrun_api

        self.lastRecordSearch = ""

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f"Logged in as {self.bot.user} - {self.bot.user.id}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.eastereggs(message)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        self.logger.error(error)
        if isinstance(error, commands.CommandNotFound):
            if ctx.invoked_with.isalnum():
                await ctx.send(f"{ctx.invoked_with} is not a command. Use !help to see a list of commands")

    async def respond_to_user(self, ctx, message, view=None):
        if ctx.interaction:
            return await ctx.interaction.response.send_message(message, view=view, ephemeral=True)
        return await ctx.send(message)

    async def respond(self, ctx, message, view=None):
        if ctx.interaction:
            return await ctx.interaction.response.send_message(message, view=view)
        return await ctx.send(message)

    @commands.hybrid_command()
    async def sync(self, ctx):
        synced = await ctx.bot.tree.sync()
        await self.respond_to_user(ctx, f"Synced {len(synced)} command(s).")

    @commands.hybrid_command()
    async def test(self, ctx):
        """
        Test if the bot is working
        """
        await ctx.send("test")

    @commands.hybrid_command()
    async def join(self, ctx, role=""):
        """
        Adds the given role to the command invoker

        Gives an error message if there are 0 or >1 roles specified, or if the
        specified role is not allowed.

        User Arguments:
            role: AKR, CIN, CLE, COL, DAY, TOL, MI, KY, PA, IN, NY, CA, Canada, EX-OH

        """
        if not role and ctx.interaction:
            return await ctx.interaction.response.send_message(
                content="Choose your role to join", view=RoleView(), ephemeral=True
            )

        role_obj, message = self.get_role_from_input(ctx, role)
        if not role_obj:
            return await self.respond_to_user(ctx, message, view=RoleView())
        try:
            if role_obj not in ctx.author.roles:
                await ctx.author.add_roles(role_obj)

                view = RoleView()
                view.children[0].placeholder = "(Optional) Add another role"
                return await self.respond_to_user(ctx, f"Adding {ctx.author.display_name} to {role}", view=view)
            return await self.respond_to_user(ctx, f"Already in {role}", view=RoleView())
        except Forbidden:
            await self.respond_to_user(ctx, "I do not have permissions to assign roles right now!", view=RoleView())

    @commands.hybrid_command()
    async def leave(self, ctx, role=""):
        """
        Removes the given role from the command invoker

        Gives an error message if there are 0 or >1 roles specified, or if the
        specified role is not allowed.

        User Arguments:
            role: AKR, CIN, CLE, COL, DAY, TOL, MI, KY, PA, IN, NY, CA, Canada, EX-OH
        """
        if not role and ctx.interaction:
            return await ctx.interaction.response.send_message(
                content="Choose your role to leave", view=RoleView(action="leave"), ephemeral=True
            )

        role_obj, message = self.get_role_from_input(ctx, role)
        if not role_obj:
            return await self.respond_to_user(ctx, message, view=RoleView(action="leave"))
        try:
            if role_obj in ctx.author.roles:
                await ctx.author.remove_roles(role_obj)

                view = RoleView(action="leave")
                view.children[0].placeholder = "(Optional) Leave another role"
                return await self.respond_to_user(ctx, f"Removing {ctx.author.display_name} from {role}", view=view)
            return await self.respond_to_user(ctx, f"Not in {role}", view=RoleView(action="leave"))
        except Forbidden:
            await self.respond_to_user(
                ctx,
                "I do not have permissions to assign roles right now!",
                view=RoleView(action="leave"),
            )

    def get_role_from_input(self, ctx, role_input):
        """
        Turn a user's string from !join or !leave into a Discord Role object

        :param ctx: Discord Context (for accessing the Roles list)
        :param role_input: Tuple of Strings representing user input (split by spaces)
        :return: A tuple of either a Role or False, and an accompanying message
        """
        if not role_input and not ctx.interaction:
            return False, "Usage: !join [" + ", ".join(self.custom_roles) + "]"
        role = next((role for role in self.custom_roles if role_input.lower() == role.lower()), None)
        if role:
            return discord.utils.get(ctx.guild.roles, name=role), ""
        else:
            return False, "Allowed roles are: " + ", ".join(self.custom_roles)

    def get_display_time(self, timing_type):
        """
        Get a display time for today's e-amusement maintenance time.

        Uses the timing_types: "daily", "extended" from self

        :returns A String in the format "4PM-6PM" based on today's maintenance time
        """
        today = datetime.datetime.utcnow().astimezone(pytz.utc)
        begin_datetime = datetime.datetime.combine(today.date(), self.eamuse_maintenance[timing_type][0])
        end_datetime = datetime.datetime.combine(today.date(), self.eamuse_maintenance[timing_type][1])
        begin_hour = begin_datetime.astimezone(pytz.timezone("America/New_York")).strftime("%I").lstrip("0")
        end_hour = end_datetime.astimezone(pytz.timezone("America/New_York")).strftime("%I").lstrip("0")
        return f"{begin_hour}PM-{end_hour}PM ET"

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
        today_in_japan = datetime.datetime.utcnow().astimezone(pytz.timezone("Japan"))
        tomorrow_in_japan = today_in_japan + datetime.timedelta(days=1)
        today_in_eastern = datetime.datetime.utcnow().astimezone(pytz.timezone("America/New_York"))

        # If it's Monday in America, and either the third Tuesday or the Monday before that in Japan
        if today_in_eastern.weekday() == 0 and (
            (today_in_japan.weekday() == 1 and 15 <= today_in_japan.day <= 21)
            or (tomorrow_in_japan.weekday() == 1 and 15 <= tomorrow_in_japan.day <= 21)
        ):
            return True
        return False

    @commands.hybrid_command()
    async def eamuse(self, ctx):
        """
        Gets e-amusement maintenance time.

        Japanese Servers: 5:00 AM to 7:00 AM JST on weekdays
        Extended and US Servers: 3:00 AM to 7:00 AM JST on the third Tuesday
        """

        if self.is_extended_maintenance_time():
            await self.respond(
                ctx,
                (
                    "**Extended Maintenance today. "
                    "All games and e-amusement websites under maintenance from "
                    + f"{self.get_display_time('extended')}. "
                    + f"{self.messages['website_down']} "
                    + f"{self.messages['card_down']}**"
                ),
            )

        else:
            ddr_message = f"{self.messages['us_games']}: **No maintenance today.**"
            website_message = (
                "**Website under maintenance from "
                + f"{self.get_display_time('daily')} daily. "
                + f"{self.messages['website_down']}**"
            )

            if datetime.datetime.today().weekday() in [6, 0, 1, 2, 3]:
                other_message = (
                    f"{self.messages['jp_games']}: "
                    + "**Japanese game servers under maintenance from "
                    + f"{self.get_display_time('daily')} today. "
                    + f"{self.messages['card_down']}**"
                )
            else:
                other_message = f"{self.messages['jp_games']}: **No maintenance today.**"

            await self.respond(ctx, f"{ddr_message}\n{other_message}\n{website_message}")

    @commands.hybrid_command()
    async def insult(self, ctx, *, name=""):
        """
        Returns a scathing insult about the given name.

        User Arguments:
            name: name of person to insult
        """
        if not name:
            await self.respond(ctx, "No one to insult :(")
        else:
            r = requests.get("https://quandyfactory.com/insult/json")
            insult = r.json()["insult"]
            await self.respond(ctx, insult.replace("Thou art", f"{name} is"))

    @commands.hybrid_command()
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
                        r = requests.get("".join([base_url, "games/", game_id]), headers=auth)
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
                            r = requests.get("".join([base_url, "users/", user_id]), headers=auth)
                            user_name = r.json()["data"]["names"]["international"]

                            await ctx.send(f"The Any% record for {game_name} is {record} by {user_name}")

                        else:
                            await ctx.send("There are no Any% records for {}".format(game_name))
                    elif len(results) < 5:
                        names = []
                        for result in results:
                            names.append(result["names"]["international"])
                        await ctx.send("Multiple results. Do a search for the following: {}".format(", ".join(names)))
                        await ctx.send("If you want the first result, redo the search")
                    else:
                        await ctx.send("Too many results! Be a little more specific")
                else:
                    await ctx.send("No games with that name found!")
            self.lastRecordSearch = search
        else:
            await ctx.send("You gotta give me a game to look for...")

    async def eastereggs(self, message):
        if "honk" in message.content.lower():
            if "Skeeter" in message.author.display_name:
                await message.channel.send("beep")
            else:
                await message.channel.send("HONK!")
        if " izakaya " in message.content.lower():
            await message.channel.send(
                "Izakaya, an anime-themed restaurant and bar offering pizza, spirits, Korean corn dogs and Japanese pop culture, located at Fairfield Commons Mall in Beavercreek, Ohio?"
            )
        if "dygma" in message.content.lower():
            await message.channel.send("whats dygma")
        if re.search(r"(s?he|they)\s.+\son\smy\s.+\still?\si", message.content.lower()):
            await message.channel.send("# [𝐄𝐗𝐓𝐑𝐄𝐌𝐄𝐋𝐘 𝐋𝐎𝐔𝐃 𝐈𝐍𝐂𝐎𝐑𝐑𝐄𝐂𝐓 𝐁𝐔𝐙𝐙𝐄𝐑]")
