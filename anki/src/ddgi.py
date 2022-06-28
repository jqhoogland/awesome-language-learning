"""Built on top of https://github.com/deepanprabhu/duckduckgo-images-api"""
import requests
import re
import json
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DDGI_BASE_URL = 'https://duckduckgo.com/'
def get_ddgi_headers(lang): 
    return {
        'authority': 'duckduckgo.com',
        'accept': 'application/json, text/javascript, */* q=0.01',
        'sec-fetch-dest': 'empty',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Macintosh Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'referer': 'https://duckduckgo.com/',
        'accept-language': lang,
    }

def get_ddgi_token(**kwargs):
    #   First make a request to above DDGI_BASE_URL, and parse out the 'vqd'
    #   This is a special token, which should be used in the subsequent request
    logger.debug("Hitting DuckDuckGo for Token")

    res = requests.post(DDGI_BASE_URL, **kwargs)
    searchObj = re.search(r'vqd=([\d-]+)\&', res.text, re.M|re.I)

    if not searchObj:
        raise ValueError("Token could not be obtained.")

    logger.debug("Obtained Token")

    return searchObj.group(1)


def get_ddgi_params(keywords, lang="en-US"):
    vqd = get_ddgi_token(data={'q': keywords})

    return (
        ('l', lang),
        ('o', 'json'),
        ('q', keywords),
        ('vqd', vqd),
        ('f', ',,,'),
        ('p', '1'),
        ('v7exp', 'a'),
    )


def get_ddgi_results(keywords: str, max_results: int | None = None, lang: str = "en-US"):
    request_url = DDGI_BASE_URL + "i.js"
    headers = get_ddgi_headers(lang=lang)
    params = get_ddgi_params(keywords, lang=lang)

    logger.debug("Hitting DDGI_BASE_URL : %s", request_url)

    while True:
        try:
            res = requests.get(request_url, headers=headers, params=params)
            data = json.loads(res.text)
            return data["results"][:max_results]
        except ValueError as e:
            logger.debug("Hitting DDGI_BASE_URL Failure - Sleep and Retry: %s", request_url)
            time.sleep(5)
            continue
    
    