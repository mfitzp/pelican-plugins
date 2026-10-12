# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import random
from datetime import datetime

from feedgenerator import Rss201rev2Feed, get_tag_uri
from markupsafe import Markup
from pelican import signals
from pelican.utils import set_date_tzinfo
from pelican.writers import Writer

logger = logging.getLogger(__name__)


FEED_TAGLINES = {
    "pyqt5": """<p>For an in-depth guide to building Python GUIs with PyQt5 see my book, <a href="https://www.pythonguis.com/pyqt5-book/">Create GUI Applications with Python & Qt5.</a></p>""",
    "pyqt6": """<p>For an in-depth guide to building Python GUIs with PyQt6 see my book, <a href="https://www.pythonguis.com/pyqt6-book/">Create GUI Applications with Python & Qt6.</a></p>""",
    "pyside2": """<p>For an in-depth guide to building Python GUIs with PySide2 see my book, <a href="https://www.pythonguis.com/pyside2-book/">Create GUI Applications with Python & Qt5.</a></p>""",
    "pyside6": """<p>For an in-depth guide to building Python GUIs with PySide6 see my book, <a href="https://www.pythonguis.com/pyside6-book/">Create GUI Applications with Python & Qt6.</a></p>""",
}


class CustomRSSWriter(Writer):
    def _add_item_to_the_feed(self, feed, item):
        tz_info = item.date.tzinfo
        now = datetime.now(tz_info)
        prefix = ""

        if item.date > now:
            # Ignore future items.
            return

        if hasattr(item, "subpart_of"):
            # Don't add subparts to the feed.
            return

        if hasattr(item, "canonicalurl"):
            # Don't add canonical url items.
            return

        title = Markup(
            "%s %s — %s" % (prefix, item.title, item.subtitle)
            if hasattr(item, "subtitle")
            else item.title
        ).striptags()

        link = "%s/%s" % (self.site_url, item.url)
        is_rss = isinstance(feed, Rss201rev2Feed)
        if not is_rss or self.settings.get("RSS_FEED_SUMMARY_ONLY"):
            description = item.summary
        else:
            description = item.get_content(self.site_url)

        content = item.get_content(self.site_url)

        # Check if any taglines apply.
        taglines = [
            tagline
            for keyword, tagline in FEED_TAGLINES.items()
            if keyword in content.lower()
        ]
        if taglines:
            tagline = random.choice(taglines)
            content = f"""
            {content}
            {tagline}
            """

        feed.add_item(
            title=title,
            link=link,
            unique_id=get_tag_uri(link, item.date),
            description=description,
            content=content,
            categories=item.tags if hasattr(item, "tags") else None,
            author_name=getattr(item, "author", ""),
            pubdate=set_date_tzinfo(item.date, self.settings.get("TIMEZONE", None)),
        )


def get_custom_writer(_):
    return CustomRSSWriter


def register():
    signals.get_writer.connect(get_custom_writer)
