import logging
import dotenv
import os
from bots.honkbot import Honkbot
from bots.remy import Remybot
from bots.smxbot import Smxbot
from bots.codes import EamuseRivals
from discord.ext.commands import Bot
import sys

if "__main__" in __name__:
    logging.basicConfig(stream=sys.stdout, level=logging.WARN)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info("Starting Honkbot...")

    dotenv.load_dotenv()
    discord_api_key = os.getenv("DISCORD_API_KEY")
    speedrun_api_key = os.getenv("SPEEDRUN_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    bot = Bot(command_prefix='!')

    honkbot = Honkbot(logger, speedrun_api_key, google_api_key, bot=bot)
    bot.add_cog(honkbot)
    bot.add_cog(Remybot())
    bot.add_cog(Smxbot())
    bot.add_cog(EamuseRivals())

    bot.run(discord_api_key)
