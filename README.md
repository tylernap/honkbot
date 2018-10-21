# HONKBOT

A dumbass bot that interfaces with discord to do dumb stuff

A list of things that it does:
* Adds people to groups
* Searches google for images
* Searches youtube for videos
* Insults people
* Gives information on eAmuse downtime

## Using Honkbot

Calling honkbot.py directly will pull in environment variables and run the bot. You can also call the bot in python

Example:
```python
import honkbot

discord_apikey=asdfclkwmeroi2j34r09sdfu82oui345th
bot = honkbot.Honkbot(discord_apikey)
```

## Dependencies

The following are required for this bot to run correctly

* Python 3.5 or higher
Modules:
* discord.py
* python-dotenv

## Settings

Honkbot takes advantage of the following services:

* Discord (Required, obviously) - [How-to](https://discordpy.readthedocs.io/en/rewrite/discord.html)
* Google (Optional) - [How-to](https://support.google.com/googleapi/answer/6158862?hl=en)
* Speedrun.com (Optional) - [How-to](https://github.com/speedruncomorg/api/blob/master/authentication.md#aquiring-a-users-api-key)

Calling Honkbot directly, it will try to find the `.env` file located in the same directory. This file contains user specific settings such as API keys for the various services. You can find the template for the `.env` file in `env.example`
