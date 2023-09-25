import requests


def scrape_page(url, api_key):
    payload = {"api_key": api_key, "url": url}
    res = requests.get("http://api.scraperapi.com", params=payload)
    if res.status_code != 200:
        return None
    res = res.text
    return res
