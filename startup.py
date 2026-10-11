import asyncio
import logging
import dotenv
import os
from bots.honkbot import Honkbot
from bots.google import Googlebot
from bots.remy import Remybot
from bots.smxbot import Smxbot
from bots.codes import EamuseRivals
from discord import Intents
from discord.ext.commands import Bot
import sys

LOGLEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARN,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


async def add_cogs(bot, cog_list):
    for cog in cog_list:
        await bot.add_cog(cog)


if "__main__" in __name__:
    dotenv.load_dotenv()
    log_level = os.getenv("DEBUGLEVEL", default="info")
    logging.basicConfig(stream=sys.stdout, level=LOGLEVELS.get(log_level, logging.INFO))
    logger = logging.getLogger(__name__)
    logger.info("Starting Honkbot...")

    discord_api_key = os.getenv("DISCORD_API_KEY")
    speedrun_api_key = os.getenv("SPEEDRUN_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    intents = Intents(messages=True, message_content=True, guilds=True)
    discord_bot = Bot(command_prefix="!", intents=intents)

    honkbot = Honkbot(logger, speedrun_api_key, bot=discord_bot)
    googlebot = Googlebot(logger, google_api_key, bot=discord_bot)
    bot_cogs = [honkbot, googlebot, Remybot(), Smxbot(), EamuseRivals()]
    asyncio.run(add_cogs(discord_bot, bot_cogs))

    discord_bot.run(discord_api_key)
