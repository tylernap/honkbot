import discord
from discord.ext import commands

class RulesBot(commands.Cog):
    """
    Bot that controls whether or not a user has read the server rules via reactions
    """
    def __init__(self, bot, rules_channel, rules_message, rules_emoji, rules_role):
        self.bot = bot
        self.rules_channel = int(rules_channel)
        self.rules_message = int(rules_message)
        self.rules_emoji = rules_emoji
        self.rules_role = rules_role

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id == self.rules_channel and payload.message_id == self.rules_message:
            if payload.emoji.name == self.rules_emoji:
                guild = self.bot.get_guild(payload.guild_id)
                role = discord.utils.get(guild.roles, name=self.rules_role)
                user = guild.get_member(payload.user_id)
                await user.add_roles(role)