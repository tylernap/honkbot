import re

import discord
from discord.ext import commands

import models


class EamuseRivals(commands.Cog):

    @commands.command()
    async def ddrrival(self, ctx, action=None, *args):
        """
        Accesses eAmuse rival data stored by the users

        Actions:
            create [NAME DDR-CODE [DANRANK (8dan, kai, etc.)]]
            search [[name=NAME] [code=DDR-CODE] [rank=DANRANK]]
            update [[name=NAME] [code=DDR-CODE] [rank=DANRANK]]
            delete

        Examples:
            !ddrrival create SPOOKY 1234-5678 8dan
            !ddrrival search name=SPOOKY
            !ddrrival update code=8888-8888 rank=10dan
            !ddrrival delete

        """

        actions = ["create", "search", "update", "delete"]
        if action not in actions:
            return await ctx.send("Bad action! Use `!help ddrrival` for more information")

        try:
            ddrcode = models.DDRCode(ctx.author.name)
        except Exception as e:
            return await ctx.send("DDR Rival codes are currently unavailable. Send help!")
            raise e

        if action == "create":
            # Some form validation
            # First two args are required. Third arg is optional
            if len(args) < 2:
                return await ctx.send("Missing required arguments! Use `!help ddrrival` for more information")
            if len(args) >= 2:
                name = args[0].upper()
                code = args[1]
                if len(args) > 2:
                    rank = args[2].upper()
                else:
                    rank = None

            # Check to see if entries are valid
            if not name or len(name) > 8:
                return await ctx.send("Dancer name must be at most 8 characters!")
            if not re.search("^[0-9]{4}-[0-9]{4}$", code):
                return await ctx.send("DDR ID must follow the following format: `####-####`")
            if rank:
                if not re.search("^((10|[1-9])(DAN|KYU)|CHUU|KAI)$", rank):
                    return await ctx.send("Rank is not valid! Options are #dan, #kyu, chuu, or kai")

            # Entries have been validated. Initiate model object and create entry
            try:
                ddrcode.create(name=name, code=code, rank=rank)
            except Exception as e:
                if "An entry already exists" in str(e):
                    return await ctx.send(str(e))
                await ctx.send(f"Cannot create entry for {name}! Send help!")
                raise e

            return await ctx.send(f"Created DDR Rival {name}!")

        elif action == "search":
            # Need to have some filters
            if not args:
                return await ctx.send("Missing filters! Use `!help ddrrival` for more information")
            filters = {}
            # Check to see if each filter is properly formatted
            for arg in args:
                arg_filter = arg.split("=")
                if len(arg_filter) != 2:
                    return await ctx.send("Invalid filters! Use `!help ddrrival` for more information")
                if arg_filter[0] not in ddrcode.AVAILABLE_ATTRIBUTES:
                    return await ctx.send(f"Invalid filter {arg_filter[0]}! Use `!help ddrrival` for more information")
                filters[arg_filter[0]] = arg_filter[1]
            # Search!
            try:
                response = ddrcode.search(**filters)
            except Exception as e:
                await ctx.send("Cannot search for rivals! Send help!")
                raise e

            if not response:
                return await ctx.send("No rivals found with that filter!")
            response_text = "\n".join([f"{item[0]}\t{item[1]}\t{item[2]}\t{item[3]}" for item in response])
            return await ctx.send(f"```\n{response_text}\n```")

        elif action == "update":
            # Need to have some filters
            if not args:
                return await ctx.send("Missing filters! Use `!help ddrrival` for more information")
            filters = {}
            # Check to see if each filter is properly formatted
            for arg in args:
                arg_filter = arg.split("=")
                if len(arg_filter) != 2:
                    return await ctx.send("Invalid filters! Use `!help ddrrival` for more information")
                if arg_filter[0] not in ddrcode.AVAILABLE_ATTRIBUTES:
                    return await ctx.send(f"Invalid filter {arg_filter[0]}! Use `!help ddrrival` for more information")
                filters[arg_filter[0]] = arg_filter[1]
            # Make the update
            try:
                ddrcode.update(**filters)
            except Exception as e:
                if "Entry must be created first" in str(e):
                    return await ctx.send("Your entry must be created first. See `!help ddrrival` for more information")
                else:
                    await ctx.send("Cannot update entry! Send help!")
                    raise e
            return await ctx.send("Entry has been updated!")

        elif action == "delete":
            try:
                ddrcode.delete()
            except Exception as e:
                if "Entry must be created first" in str(e):
                    return await ctx.send("Your entry must be created first. See `!help ddrrival` for more information")
                else:
                    await ctx.send("Cannot delete entry! Send help!")
                    raise e
            return await ctx.send("Entry has been deleted!")

    @commands.command()
    async def iidxrival(self, ctx, action=None, *args):
        """
        Accesses eAmuse rival data stored by the users

        Actions:
            create [NAME IIDX-CODE [DANRANK (8dan, kai, etc.)]]
            search [[name=NAME] [code=IIDX-CODE] [rank=DANRANK]]
            update [[name=NAME] [code=IIDX-CODE] [rank=DANRANK]]
            delete

        Examples:
            !iidxrival create SPOOKY 1234-5678 8dan
            !iidxrival search name=SPOOKY
            !iidxrival update code=8888-8888 rank=10dan
            !iidxrival delete

        """

        actions = ["create", "search", "update", "delete"]
        if action not in actions:
            return await ctx.send("Bad action! Use `!help iidxrival` for more information")

        try:
            iidxcode = models.IIDXCode(ctx.author.name)
        except Exception as e:
            return await ctx.send("IIDX Rival codes are currently unavailable. Send help!")
            raise e

        if action == "create":
            # Some form validation
            # First two args are required. Third arg is optional
            if len(args) < 2:
                return await ctx.send("Missing required arguments! Use `!help iidxrival` for more information")
            if len(args) >= 2:
                name = args[0].upper()
                code = args[1]
                if len(args) > 2:
                    rank = args[2].upper()
                else:
                    rank = None

            # Check to see if entries are valid
            if not name or len(name) > 6:
                return await ctx.send("DJ name must be at most 6 characters!")
            if not re.search("^[0-9]{4}-[0-9]{4}$", code):
                return await ctx.send("IIDX ID must follow the following format: `####-####`")
            if rank:
                if not re.search("^((10|[1-9])(DAN|KYU)|CHUU|KAI)$", rank):
                    return await ctx.send("Rank is not valid! Options are #dan, #kyu, chuu, or kai")

            # Entries have been validated. Initiate model object and create entry
            try:
                iidxcode.create(name=name, code=code, rank=rank)
            except Exception as e:
                if "An entry already exists" in str(e):
                    return await ctx.send(str(e))
                await ctx.send(f"Cannot create entry for {name}! Send help!")
                raise e

            return await ctx.send(f"Created IIDx Rival {name}!")

        elif action == "search":
            if not args:
                return await ctx.send("Missing filters! Use `!help iidxrival` for more information")
            filters = {}
            for arg in args:
                arg_filter = arg.split("=")
                if len(arg_filter) != 2:
                    return await ctx.send("Invalid filters! Use `!help iidxrival` for more information")
                if arg_filter[0] not in iidxcode.AVAILABLE_ATTRIBUTES:
                    return await ctx.send(f"Invalid filter {arg_filter[0]}! Use `!help iidxrival` for more information")
                filters[arg_filter[0]] = arg_filter[1]

            try:
                response = iidxcode.search(**filters)
            except Exception as e:
                await ctx.send("Cannot search for rivals! Send help!")
                raise e
            if not response:
                return await ctx.send("No rivals found with that filter!")
            response_text = "\n".join([f"{item[0]}\t{item[1]}\t{item[2]}\t{item[3]}" for item in response])
            return await ctx.send(f"```\n{response_text}\n```")

        elif action == "update":
            if not args:
                return await ctx.send("Missing filters! Use `!help iidxrival` for more information")
            filters = {}
            for arg in args:
                arg_filter = arg.split("=")
                if len(arg_filter) != 2:
                    return await ctx.send("Invalid filters! Use `!help iidxrival` for more information")
                if arg_filter[0] not in iidxcode.AVAILABLE_ATTRIBUTES:
                    return await ctx.send(f"Invalid filter {arg_filter[0]}! Use `!help iidxrival` for more information")
                filters[arg_filter[0]] = arg_filter[1]
            try:
                iidxcode.update(**filters)
            except Exception as e:
                if "Entry must be created first" in str(e):
                    return await ctx.send(
                        "Your entry must be created first. See `!help iidxrival` for more information"
                    )
                else:
                    await ctx.send("Cannot update entry! Send help!")
                    raise e
            return await ctx.send("Entry has been updated!")

        elif action == "delete":
            try:
                iidxcode.delete()
            except Exception as e:
                if "Entry must be created first" in str(e):
                    return await ctx.send(
                        "Your entry must be created first. See `!help iidxrival` for more information"
                    )
                else:
                    await ctx.send("Cannot delete entry! Send help!")
                    raise e
            return await ctx.send("Entry has been deleted!")
