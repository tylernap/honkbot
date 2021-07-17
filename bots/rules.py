import discord
from discord.ext import commands


class RulesBot(commands.Cog):
    """
    Bot that controls whether or not a user has read the server rules via reactions

    :param bot: The bot that is calling this cog
    :type bot: commands.Bot
    :param rules_channel: Channel ID of the channel that contains the message to monitor
    :type rules_channel: str
    :param rules_message: Message ID of the message to monitor
    :type rules_message: str
    :param rules_emoji: Name of the emoji to monitor the message for
    :type rules_emoji: str
    :param rules_role: Name of the role to add/remove
    :type rules_role: str

    :return: None
    """
    def __init__(self, bot, rules_channel, rules_message, rules_emoji, rules_role):
        self.bot = bot
        self.rules_channel = int(rules_channel)
        self.rules_message = int(rules_message)
        self.rules_emoji = rules_emoji
        self.rules_role = rules_role

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Cog listener that waits for a reaction to be added to a message.

        When the correct reaction is made to the rules message, the user is added to the rules role.
        Other emojis added to the message are cleared. All other messages are ignored

        :param payload: payload given by discord of reaction event
        :type payload: discord.RawReactionActionEvent

        :return: None
        """
        if payload.channel_id == self.rules_channel and payload.message_id == self.rules_message:
            guild = self.bot.get_guild(payload.guild_id)
            user = guild.get_member(payload.user_id)
            if payload.emoji.name == self.rules_emoji:
                role = discord.utils.get(guild.roles, name=self.rules_role)
                await user.add_roles(role)
            else:
                channel = guild.get_channel(payload.channel_id)
                message = channel.get_partial_message(payload.message_id)
                await message.clear_reaction(payload.emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Cog listener that waits for a reaction to be removed from a message.

        When the correct reaction is removed from the rules message, the user has their role removed.
        All other messages are ignored.

        :param payload: payload given by discord of reaction event
        :type payload: discord.RawReactionActionEvent

        :return: None
        """
        if payload.channel_id == self.rules_channel and payload.message_id == self.rules_message:
            guild = self.bot.get_guild(payload.guild_id)
            user = guild.get_member(payload.user_id)
            if payload.emoji.name == self.rules_emoji:
                role = discord.utils.get(guild.roles, name=self.rules_role)
                await user.remove_roles(role)
