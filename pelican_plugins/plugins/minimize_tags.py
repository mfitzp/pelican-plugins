# -*- coding: utf-8 -*-
"""
Strips tags not used a minimum of X times, allowing you to tag
articles thoroughly without generating a load of redundant
single-entry pages.
"""

from collections import Counter, defaultdict
from logging import warning
from operator import itemgetter

from pelican import signals


def minimize_tags(generator):

    all_tags = []
    for article in generator.articles:
        if not hasattr(article, 'tags'):
            continue

        all_tags.extend(article.tags)

    tag_counts = Counter(all_tags)

    minitag_count = generator.settings.get('MINIMUM_TAG_ARTICLES', 2)
    for article in generator.articles:
        if not hasattr(article, 'tags'):
            continue

        article.tags = [tag for tag in article.tags if tag_counts[tag] >= minitag_count]


def register():
    signals.article_generator_pretaxonomy.connect(minimize_tags)
