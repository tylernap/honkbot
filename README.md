# HONKBOT

A mission-critical bot that interfaces with discord to do highly important stuff

A list of things that it does:
* Adds people to groups
* Searches google for images
* Searches youtube for videos
* Insults people
* Gives information on eAmuse downtime

## Installing

No special installations needed for the bot itself. Simply clone and run

Dependencies can be installed by running `pip install -r requirements.txt` in the project directory

## Using Honkbot

Calling honkbot.py directly will pull in environment variables and run the bot. You can also call the bot in python

Example:
```python
import honkbot

discord_apikey = "asdfclkwmeroi2j34r09sdfu82oui345th"
bot = honkbot.Honkbot(discord_apikey)
bot.run()
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

## Contributing

Want to help keep Honkbot awesome? Great! Just a couple things:

* This repo will follow a [Forking workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow) for non-contributors. You will have to fork the repo to your own and merge back in via PR
* Contributors will follow a [Feature branch workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow). All new code will be done in a separate branch and merged via PR
* `master` is protected so that the code owner must approve all changes

This is another test
