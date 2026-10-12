# -*- coding: utf-8 -*-
"""
Link across between tracks
"""

from collections import defaultdict

from pelican import signals
from pelican.contents import Page
from pelican.utils import slugify
from six import text_type


def process_crosslinks(generator):

    # Iterate all articles, if they have a track, store them by their parent folder.
    article_folders = defaultdict(list)

    for article in generator.articles:
        if hasattr(article, 'course'):
            article_folders[article.relative_dir].append(article)

    # Add articles in the same folder to each article under .crosslinks.
    for articles in article_folders.values():
        for article in articles:
            articles_filtered = articles[::]
            articles_filtered.remove(article)
            article.crosslinks = articles_filtered

    generator._update_context(['articles'])
