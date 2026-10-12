# -*- coding: utf-8 -*-
"""
Calculation duration, as timedelta (using provided minutes, or using readtime)
"""

import pathlib
from collections import defaultdict

from pelican import signals
from pelican.contents import Article


def identify_article_library(content_object):
    # Get the tag mapper, for each article we try and auto-generate
    # a library based on the filename (checking keys in this map).
    LIBRARIES = content_object.settings.get("LIBRARIES", {})

    if not isinstance(content_object, Article):
        return

    if hasattr(content_object, "library"):
        if content_object.library == "none":
            del content_object.library
        return  # Already set.

    # Collect all possible libraries using names in path & any tags.
    # Library can be set *only* if there is a single definite library.

    filename = pathlib.Path(content_object.source_path).parts[-1]
    fn_parts = filename.split("-")  # List of parts of the slug.
    all_parts = set(fn_parts)

    if hasattr(content_object, "tags"):
        tag_parts = [t.name for t in content_object.tags]  # All tag names.
        all_parts.update(tag_parts)

    all_parts = [t.lower() for t in all_parts]

    matches = []
    for library in LIBRARIES.keys():
        if library in all_parts:
            matches.append(library)

    if len(matches) == 1:  # Only a single match, good!
        content_object.library = matches[0]


def process_siblings(generator):
    # Iterate all articles, if they have a library store them by their parent folder.
    article_folders = defaultdict(list)
    SIBLINGS_FOLDERS = generator.settings.get("SIBLINGS_FOLDERS", {})

    for article in generator.articles:
        # Get first element of the path.
        basefolder = pathlib.Path(article.relative_dir).parts[0]
        if hasattr(article, "library") and basefolder in SIBLINGS_FOLDERS:
            article_folders[article.relative_dir].append(article)

    # Add articles in the same folder to each article under .siblings.
    for articles in article_folders.values():
        for article in articles:
            articles_filtered = articles[::]
            articles_filtered.remove(article)
            article.siblings = articles_filtered

    generator._update_context(["articles"])


def process_article_menu(generator):
    MENUS = generator.settings.get("MENUS", {})

    article_map = {article.slug: article for article in generator.articles}
    parsed_menu = dict()

    for key, menu in MENUS.items():
        menu_sections = {}
        for section, slugs in menu.items():
            art = []
            for slug in slugs:
                article = article_map.get(slug)
                if article:
                    title = getattr(article, "navtitle", None) or article.title
                    art.append((article.url, title, slug))
            menu_sections[section] = art

        parsed_menu[key] = menu_sections

    generator.MENUS = parsed_menu
    generator._update_context(["MENUS"])


def register():
    signals.content_object_init.connect(identify_article_library)
    signals.article_generator_finalized.connect(process_siblings)
    signals.article_generator_finalized.connect(process_article_menu)
