from bs4 import BeautifulSoup
from typing import Optional
import requests


def search_song(query: str) -> Optional[BeautifulSoup]:
    """
    Tries to find a certain song on RemyWiki

    MediaWiki tries to match an exact article title. If it doesn't find the
    exact title, it gives you a page with a list of suggestions. This
    leverages that by either going to the direct page, or going to the first
    page in the list of results.

    :param query: a string representing something that's supposed to be a
        song name to find
    :return: a BeautifulSoup object representing a RemyWiki page for a song,
        or None, representing a lack of results
    """
    search_data = {'search': f"{query} incategory:\"Songs\""}
    remy_search = requests.post('http://remywiki.com/index.php', data=search_data)
    remy_data = BeautifulSoup(remy_search.text, 'html.parser')
    if remy_data.title.string.lower().startswith(query):
        return remy_data
    else:
        first_result = remy_data.find("ul", {"class": "mw-search-results"})
        if first_result:
            song_result = requests.post(f"http://remywiki.com{first_result.li.div.a['href']}")
            return BeautifulSoup(song_result.text, 'html.parser')
        else:
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
    remy_data = search_song(query)
    if remy_data is not None:
        images = remy_data.find_all("div", {"class": "thumbinner"})
        for image in images:
            if image_type in image.find("div", {"class": "thumbcaption"}).text:
                return f"http://remywiki.com{image.find('img')['src']}"

        song_title = remy_data.find("h1", {"id": "firstHeading"}).text
        if song_title.lower() == query.lower():
            return f"{song_title} does not have a {image_type}"
        else:
            return f"{query} seems to be the song {song_title} but it does not have a {image_type}"
    else:
        return f"Could not find a song that looks like: {query}"
