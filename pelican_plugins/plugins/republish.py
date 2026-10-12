# -*- coding: utf-8 -*-
"""
Calculation duration, as timedelta (using provided minutes, or using readtime)
"""

from pelican import signals, utils
from pelican.utils import get_date, set_date_tzinfo, order_content
from datetime import datetime


def republish_articles(generator):

    now = datetime.utcnow()
    now = set_date_tzinfo(now, 'UTC')

    for article in generator.articles:
        republish = article.metadata.get('republish')
        if republish:
            # Parse the date, and if it is in the past replace the published date.
            republished = get_date(republish)
            republished = set_date_tzinfo(republished, 'UTC')

            if republished < now:
                article.date = republished
                article.metadata['date'] = republished
                article.isrepublished = True

                # All articles should be modified on/after their publication date.
                if article.date > article.modified:
                    article.modified = article.date

    generator.articles = order_content(generator.articles, 'reversed-date')
    #generator.articles = sorted(generator.articles, key=lambda article: article.date, reverse=True)


def register():
    signals.article_generator_finalized.connect(republish_articles)
