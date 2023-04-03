import logging
import dotenv
dotenv.load_dotenv()
import os
from bots.honkbot import Honkbot
from bots.remy import Remybot
from bots.smxbot import Smxbot
from bots.codes import EamuseRivals
from discord import Intents
from discord.ext.commands import Bot
import sys


if "__main__" in __name__:
    logging.basicConfig(stream=sys.stdout, level=logging.WARN)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info("Starting Honkbot...")

    # TODO: Validate these env vars
    guild_id = os.getenv("GUILD_ID")
    discord_api_key = os.getenv("DISCORD_API_KEY")
    speedrun_api_key = os.getenv("SPEEDRUN_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    intents = Intents(messages=True, message_content=True, guilds=True)
    discord_bot = Bot(intents=intents)

    honkbot = Honkbot(logger, speedrun_api_key, google_api_key, bot=discord_bot)
    bot_cogs = [honkbot, Remybot(), Smxbot()]
    # TODO: Eamuse rival bot needs some TLC. Removing for now since its not in use
    # bot_cogs.append(EamuseRivals())
    for cog in bot_cogs:
        discord_bot.add_cog(cog)

    discord_bot.run(discord_api_key)