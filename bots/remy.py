import logging
from typing import Dict, Optional

import requests
from discord.ext import commands

REMY_URL = "https://remywiki.com"
REMY_API = f"{REMY_URL}/api.php"

HEADERS = {"User-Agent": "OhioDDR-honkbot"}

logger = logging.getLogger(__name__)


async def search_song(query: str) -> Optional[str]:
    """
    Tries to find a certain song on RemyWiki

    :param query: a string representing something that's supposed to be a
        song name to find
    :return: a str representing a RemyWiki page for a song,
        or None, representing a lack of results
    """
    # See if its a direct query
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": f"{query} incategory:\"Songs\"",
        "formatversion": "2",
    }
    logger.debug(f"Searching for song with query: {str(params)}")
    response = requests.get(REMY_API, params=params, headers=HEADERS).json()
    logger.debug(f"Received response: {str(response)}")
    pages = response.get("query", {}).get("search", [])
    if pages:
        logger.debug(f"Found title {pages[0]["title"]}")
        return pages[0]["title"]
    return None


async def get_image_from_page(title: str, image_type: str) -> tuple[Optional[str], Optional[str]]:
    """
    Gets all images from a page through the API

    :param title: Title of the song to search for
    :param image_type: Either "banner" or "jacket"

    :return: A tuple with URL pointing to an image OR None, and a backup image if None
    """
    params = {
        "action": "query",
        "format": "json",
        "prop": "images",
        "titles": title,
        "formatversion": "2"
    }
    logger.debug(
        f"Getting {title} {image_type} from song page with query: {str(params)}"
    )
    response = requests.get(REMY_API, params=params, headers=HEADERS).json()
    logger.debug(f"Received response: {str(response)}")
    return await parse_image_response(response, image_type)


async def get_image_from_gallery(title: str, image_type: str) -> tuple[Optional[str], Optional[str]]:
    """
    Gets an image from the Gallery page template on RemyWiki

    :param title: Title of the song to search for
    :param image_type: Either "banner" or "jacket"

    :return: A tuple with URL pointing to an image OR None, and a backup image if None
    """
    params = {
        "action": "query",
        "format": "json",
        "prop": "images",
        "titles": f"Gallery:{title}",
        "formatversion": 2
    }
    logger.debug(
        f"Getting {title} {image_type} from gallery with query: {str(params)}"
    )
    response = requests.get(REMY_API, params=params, headers=HEADERS).json()
    logger.debug(f"Received response: {str(response)}")
    return await parse_image_response(response, image_type)


async def parse_image_response(response: Dict, image_type: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parses response from Remywiki for image information

    :param response: requests response

    :return: A tuple with URL pointing to an image OR None, and a backup image if None
    """
    # Get images from the song's gallery
    images = []
    backup = None
    for page in response.get("query", {}).get("pages", []):
        if page.get("missing", False):
            return None, None

        for image in page.get("images", []):
            image_title = image.get("title", "")
            if image_title:
                images.append(image_title)

    logger.debug(f"Found {len(images)} images")
    # Check the comment of the image to see if it is a banner or jacket
    # iilimit max returns all revisions of a file so we can check all revisions for comments
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "titles": "|".join(images),
        "formatversion": 2,
        "iiprop": "comment|url",
        "iilimit": "max"
    }
    logger.debug(f"Getting image info from params: {str(params)}")
    response = requests.get(REMY_API, params=params, headers=HEADERS).json()
    logger.debug(f"Received response: {response}")
    for page in response["query"]["pages"]:
        for revision in page.get("imageinfo", []):
            if image_type in revision.get("comment", ""):
                # We want the latest version
                # even if the revision we are looking at is not the latest
                # Praying Remywiki is not mixing up jackets and banners for the same file
                return page["imageinfo"][0]["url"], None
            else:
                backup = page["imageinfo"][0]["url"]
    return None, backup


async def get_image(query: str, image_type: str = "jacket") -> str:
    """
    Gets an image (or a message about no image) from a RemyWiki song page.

    This is intended to be used for jackets or banners. This searches the
    song page for "song name's jacket" or "song name's banner" and returns
    the image connected to that.

    :param query: a string representing something that's supposed to be a
        song name to find
    :param image_type: Either "jacket" or "banner", default "jacket"
    :return: a response fitting for the bot to return, either the requested
        image or a message describing what it found instead
    """
    song_title = await search_song(query)
    found_images = {}
    backup = None
    if song_title:
        # First try to get the image from the Gallery
        first_gallery_banner, backup = await get_image_from_gallery(song_title, "banner")
        found_images["backup"] = backup
        first_gallery_jacket, backup = await get_image_from_gallery(song_title, "jacket")
        if not found_images.get("backup", ""):
            found_images["backup"] = backup
        if first_gallery_banner:
            logger.debug(f"Found banner for {song_title} from gallery")
            found_images["banner"] = first_gallery_banner
        if first_gallery_jacket:
            logger.debug(f"Found jacket for {song_title} from gallery")
            found_images["jacket"] = first_gallery_jacket
        if image_type in found_images:
            return found_images[image_type]

        # If there is no Gallery or not in the Gallery, try to find it on the page
        logger.debug(f"No gallery {image_type} images for {song_title} found. Checking page")
        if "banner" not in found_images:
            first_page_banner, backup = await get_image_from_page(song_title, "banner")
            if not found_images.get("backup", ""):
                found_images["backup"] = backup
            if first_page_banner:
                logger.debug(f"Found banner for {song_title} from page")
                found_images["banner"] = first_page_banner
        if "jacket" not in found_images:
            first_page_jacket, backup = await get_image_from_page(song_title, "jacket")
            if not found_images.get("backup", ""):
                found_images["backup"] = backup
            if first_page_jacket:
                logger.debug(f"Found jacket for {song_title} from page")
                found_images["jacket"] = first_page_jacket
        if image_type in found_images:
            return found_images[image_type]

        # Return any other images we found
        logger.debug(f"Found images for {song_title}: {found_images}")
        if any(found_images):
            logger.debug(f"No {image_type} images found for {song_title}. Providing other")
            image_url = next(img for img in found_images.values() if img)
            return f"{song_title} does not have a designated {image_type}, but it does have:\n{image_url}"
        # Or give a message that there are no related images
        else:
            if song_title.lower() == query.lower():
                logger.debug(f"{song_title} does not have any images")
                return f"{song_title} does not have any images"
            else:
                return f"{query} seems to be the song {song_title} but it does not have any images"
    else:  # No song page
        logger.debug(f"Could not find any song for {query}")
        return f"Could not find a song that looks like: {query}"


class Remybot(commands.Cog):

    @commands.hybrid_command()
    async def jacket(self, ctx, *, title: str):
        """
        Returns a jacket for a bemani song from remywiki.

        User Arguments:
            title: the name of a song to search for
        """
        await ctx.defer()
        response = await get_image(title, "jacket")
        await ctx.send(response)

    @commands.hybrid_command()
    async def banner(self, ctx, *, title: str):
        """
        Returns a banner for a bemani song from remywiki.

        User Arguments:
            title: the name of a song to search for
        """
        await ctx.defer()
        response = await get_image(title, "banner")
        await ctx.send(response)
