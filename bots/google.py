import requests

from discord.ext import commands


class Googlebot(commands.Cog):
    def __init__(self, logger, google_api, bot=None):
        self.bot = bot
        self.logger = logger
        self.google_api = google_api

    async def respond(self, ctx, message, view=None):
        if ctx.interaction:
            return await ctx.interaction.response.send_message(message, view=view)
        return await ctx.send(message)

    @commands.hybrid_command()
    async def image(self, ctx, *, search: str = ""):
        """
        Returns an image from Google from the given search terms.

        User Arguments:
            search: The terms to use on Google Images
        """

        if not self.google_api:
            await self.respond(ctx, "Sorry, cant do that right now! Ask your admin to enable")
            return

        if search:
            query = "".join(search)
            if len(query) < 150:
                # TODO: I guess this is unique to each deployment?
                cx_id = "009855409252983983547:3xrcodch8sc"
                url = (
                    f"https://www.googleapis.com/customsearch/v1?q={search}"
                    + f"&cx={cx_id}&safe=active&searchType=image"
                    + f"&key={self.google_api}"
                )
                r = requests.get(url)
                try:
                    response = r.json()["items"][0]["link"]
                    await self.respond(ctx, response)
                except KeyError:
                    await self.respond(ctx, f"No results found for {query} :(")
            else:
                await self.respond(ctx, "Query too big!")
        else:
            await self.respond(ctx, "Usage: !image <search term>")

    @commands.hybrid_command()
    async def youtube(self, ctx, *, search: str = None):
        """
        Returns a video from YouTube from the given search terms

        User Arguments:
            search: The terms to use on YouTube
        """
        print(search)
        if not self.google_api:
            await self.respond(ctx, "Sorry, cant do that right now! Ask your admin to enable")
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
                    await self.respond(ctx, f"Could not find any videos with search {query}")
                    return

                if response:
                    await self.respond(ctx, f"https://youtu.be/{response}")
                else:
                    await self.respond(ctx, f"Could not find any videos with search {query}")
            else:
                await self.respond(ctx, "Query too long!")
        else:
            await ctx.send("Usage: !youtube <search terms>")
