import logging
import dotenv
import os

import discord

from bots.honkbot import Honkbot
from bots.remy import Remybot
from bots.codes import EamuseRivals
from bots.rules import RulesBot
from discord.ext.commands import Bot
import sys

if "__main__" in __name__:
    logging.basicConfig(stream=sys.stdout, level=logging.WARN)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info("Starting Honkbot...")

    dotenv.load_dotenv()
    # API keys
    discord_api_key = os.getenv("DISCORD_API_KEY")
    speedrun_api_key = os.getenv("SPEEDRUN_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    # Arguments for the rules bot
    rules_channel = os.getenv("RULES_CHANNEL")
    rules_message = os.getenv("RULES_MESSAGE")
    rules_emoji = os.getenv("RULES_EMOJI")
    rules_role = os.getenv("RULES_ROLE")

    intents = discord.Intents(messages=True, reactions=True, guilds=True, members=True)

    bot = Bot(command_prefix='!', intents=intents)

    honkbot = Honkbot(logger, speedrun_api_key, google_api_key, bot=bot)
    bot.add_cog(honkbot)
    bot.add_cog(Remybot())
    bot.add_cog(EamuseRivals())
    if rules_channel and rules_message and rules_emoji and rules_role:
        bot.add_cog(RulesBot(bot, rules_channel, rules_message, rules_emoji, rules_role))
    else:
        logger.warning(
            "Not all RULE environment variables set. Check .env for missing assignments"
        )
        logger.warning("RulesBot disabled")

    bot.run(discord_api_key)
