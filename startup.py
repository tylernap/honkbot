import asyncio
import logging
import dotenv
import os
from bots.honkbot import Honkbot
from bots.remy import Remybot
from bots.smxbot import Smxbot
from bots.codes import EamuseRivals
from discord import Intents
from discord.ext.commands import Bot
import sys


async def add_cogs(bot, cog_list):
    for cog in cog_list:
        await bot.add_cog(cog)


if "__main__" in __name__:
    logging.basicConfig(stream=sys.stdout, level=logging.WARN)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info("Starting Honkbot...")

    dotenv.load_dotenv()
    discord_api_key = os.getenv("DISCORD_API_KEY")
    speedrun_api_key = os.getenv("SPEEDRUN_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    intents = Intents(messages=True, message_content=True, guilds=True)
    discord_bot = Bot(command_prefix='!', intents=intents)

    honkbot = Honkbot(logger, speedrun_api_key, google_api_key, bot=discord_bot)
    bot_cogs = [honkbot, Remybot(), Smxbot(), EamuseRivals()]
    asyncio.run(add_cogs(discord_bot, bot_cogs))

    discord_bot.run(discord_api_key)
