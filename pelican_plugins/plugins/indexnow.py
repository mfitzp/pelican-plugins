import datetime
import os
from random import shuffle

import requests

basename = os.path.dirname(__file__)

SEARCH_ENGINE_INDEXNOW_URLS = [
    "https://api.indexnow.org/indexnow",
]


def get_modified(articles, days=1):
    return [a for a in articles if is_modified(a, days=days)]


def is_modified(article, days=1):
    if not hasattr(article, "modified"):
        return False
    tz_info = article.date.tzinfo
    now = datetime.datetime.now(tz_info)
    return article.modified > (now - datetime.timedelta(days=days))


def indexnow(generator):
    indexnow_key = generator.settings.get("INDEXNOW_KEY")
    indexnow_max_urls = generator.settings.get("INDEXNOW_MAX_URLS", 5)
    live_domain = generator.settings.get("LIVEDOMAIN")
    live_url = generator.settings.get("LIVEURL")
    is_live = generator.settings.get("IS_LIVE", False)

    if not live_domain or not indexnow_key or not live_url:
        print(
            f"Not configured for IndexNow: key: {indexnow_key}, live_domain: {live_domain}, live_url: {live_url}"
        )
        return

    updated_articles = get_modified(generator.articles)
    print(f"IndexNow: {len(updated_articles)} updated article(s).")
    # Shuffle so we won't send the same articles every time on crop.
    shuffle(updated_articles)
    updated_articles = updated_articles[:indexnow_max_urls]

    data = {
        "host": live_domain,
        "key": indexnow_key,
        "keyLocation": f"{live_url}/{indexnow_key}.txt",
        "urlList": [f"{live_url}/{article.url}" for article in updated_articles],
    }

    if is_live:
        print("Submitting data to IndexNow.", data)
        for url in SEARCH_ENGINE_INDEXNOW_URLS:
            r = requests.post(url, json=data)
            print(f"Response ({url}):", r.status_code, r.content)
    else:
        print("Not live, not sending IndexNow. Would have sent:", data)


def register():
    pass

    # signals.article_generator_finalized.connect(indexnow)
