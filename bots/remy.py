from bs4 import BeautifulSoup
from typing import Optional
import os
import requests
import re
import discord
from discord.ext import commands

GUILD_ID = os.getenv("GUILD_ID")
REMY_URL = "https://remywiki.com"


def page_is_song(page: BeautifulSoup):
    if page.find("a", {"title": "Category:Songs"}):
        return True
    return False


def search_song(query: str) -> Optional[BeautifulSoup]:
    """
    Tries to find a certain song on RemyWiki

    MediaWiki will tell you if a title that you've searched is found as a direct
        article title. However, if it doesn't find one, the top page may not be
        a song. The category search to force songs won't allow the direct
        article title. So, we search the raw title, see if we've found it, then
        search in songs only if we haven't. So exact titles should always match,
        and close ones should usually match.

    :param query: a string representing something that's supposed to be a
        song name to find
    :return: a BeautifulSoup object representing a RemyWiki page for a song,
        or None, representing a lack of results
    """
    search_data = {"search": query}
    remy_search = requests.get(f"{REMY_URL}/index.php", params=search_data)
    remy_data = BeautifulSoup(remy_search.text, 'html.parser')

    # If we were redirected to a Page and it's a Song, just return it
    if page_is_song(remy_data):
        return remy_data

    # If we're not on a Page, check to see if the Search found an exact match
    already_found = remy_data.find("p", {"class": "mw-search-exists"})
    if already_found:
        song_result = requests.get(f"{REMY_URL}{already_found.strong.a['href']}")
        possible_song = BeautifulSoup(song_result.text, 'html.parser')
        if page_is_song(possible_song):
            return possible_song

    # Otherwise, just take the first search result when searching in category
    search_data = {'search': f"{query} incategory:\"Songs\""}
    remy_search = requests.get(f"{REMY_URL}/index.php", params=search_data)
    remy_data = BeautifulSoup(remy_search.text, 'html.parser')
    first_result = remy_data.find("ul", {"class": "mw-search-results"})
    if first_result:
        song_result = requests.get(f"{REMY_URL}{first_result.li.div.a['href']}")
        return BeautifulSoup(song_result.text, 'html.parser')


def get_image_from_gallery(href: str, image_type: str) -> Optional[str]:
    """
    Gets an image from the Gallery page template on RemyWiki

    :param href: The relative url (including the slash) of a gallery page
    :param image_type: Either "banner" or "jacket"

    :return: A relative URL pointing to an image OR None
    """
    gallery_page = requests.get(f"{REMY_URL}{href}")
    gallery_data = BeautifulSoup(gallery_page.text, 'html.parser')
    image_sections = gallery_data.find_all("li", {"class": "gallerybox"})
    for section in image_sections:
        description = section.find("p").text
        if image_type in description:
            img_urls = section.find("img")['srcset'].split(",")
            largest_image = img_urls[-1]
            return largest_image.split(" ")[1]  # space,url,size
    return None


def get_image(query: str, image_type: str = 'jacket') -> str:
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
    song_page = search_song(query)
    found_images = {}
    if song_page:
        # First try to get the image from the Gallery
        gallery = song_page.find("a", href=re.compile(r"Gallery"))
        if gallery:
            first_gallery_banner = get_image_from_gallery(gallery["href"], 'banner')
            first_gallery_jacket = get_image_from_gallery(gallery["href"], 'jacket')
            if first_gallery_banner:
                found_images['banner'] = first_gallery_banner
            if first_gallery_jacket:
                found_images['jacket'] = first_gallery_jacket
            if image_type in found_images:
                return f"{REMY_URL}{found_images[image_type]}"
        # If there is no Gallery, try to find it on the page
        images = song_page.find_all("div", {"class": "thumbinner"})
        for image in images:
            if 'banner' in image.find("div", {"class": "thumbcaption"}).text:
                found_images['banner'] = f"{REMY_URL}{image.find('img')['src']}"
            elif 'jacket' in image.find("div", {"class": "thumbcaption"}).text:
                found_images['jacket'] = f"{REMY_URL}{image.find('img')['src']}"
            if image_type in found_images:
                return f"{found_images[image_type]}"
        # If we haven't found the right image in either place
        song_title = song_page.find("h1", {"id": "firstHeading"}).text
        # Return any other images we found
        if any(found_images):
            image_url = next(img for img in found_images.values() if img)
            return f"{song_title} does not have a {image_type}, but it does have this:\n{image_url}"
        # Or give a message that there are no related images
        else:
            if song_title.lower() == query.lower():
                return f"{song_title} does not have any images"
            else:
                return f"{query} seems to be the song {song_title} but it does not have any images"
    else:  # No song page
        return f"Could not find a song that looks like: {query}"


class Remybot(commands.Cog):

    @commands.slash_command(guild_ids=[GUILD_ID])
    @discord.option("title", description="Name of the song to search for")
    async def jacket(self, ctx, *, title: str):
        """
        Returns a jacket for a bemani song from remywiki.

        User Arguments:
            title: the name of a song to search for
        """
        response = get_image(title, 'jacket')
        await ctx.respond(response)

    @commands.slash_command(guild_ids=[GUILD_ID])
    @discord.option("title", description="Name of the song to search for")
    async def banner(self, ctx, *, title: str):
        """
        Returns a banner for a bemani song from remywiki.

        User Arguments:
            title: the name of a song to search for
        """
        response = get_image(title, 'banner')
        await ctx.respond(response)
