import requests
import json
import re
from discord.ext import commands

"""
Tries to find a certain song jacket via SMX's API.

StepManiaX has an API, however it is intentionally publicly undocumented.
This script uses the format used by StatManiaX to attempt to pull a song
jacket from the requested song.
"""


def get_image(query: str) -> str:
    # Todo: compare to a DB of songs, instead of taking the input at face value
    # First, modify the query string to match the SMX API format.
    titled = "".join(word.capitalize() for word in query.split())
    # Remove & symbol because it breaks the URL.
    titled = titled.replace("&", "")
    # If the song is Stop! & Go, capitalize the whole thing, because it's a jerk
    if titled == "Stop!Go":
        titled = titled.upper()
    url = "https://data.stepmaniax.com/uploads/songs/" + titled + "/cover.png"

    response = requests.request("GET", url)
    # if API returns an image, return the URL
    if response.headers.get("content-type") == "image/png":
        return url
    # If the API fails to return a song, say so.
    elif response.headers.get("content-type") == "application/json":
        responseDump = json.loads(response.text)
        if responseDump["success"] != "false":
            return "StepManiaX API failed to return a song."
    # Anything else returned
    else:
        return "StepManiaX API could not be reached."


class Smxbot(commands.Cog):

    async def respond(self, ctx, message, view=None):
        if ctx.interaction:
            return await ctx.interaction.response.send_message(message, view=view)
        return await ctx.send(message)

    @commands.command()
    async def smxjacket(self, ctx, *, title: str):
        """
        Returns a jacket for a stepmaniax song from the StepManiaX API.

        User Arguments:
            title: the name of a song to search for
        """
        response = get_image(title)
        await self.respond(ctx, response)
