# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
Generates an additional social feed, for specified categories.
Titles use hashtags, shuffle latest posts. The normal feeds
are not affected.
"""

import logging
import random
import re
from datetime import datetime, timedelta, timezone

from feedgenerator import Rss201rev2Feed, get_tag_uri
from jinja2.utils import markupsafe
from pelican import signals
from pelican.utils import get_date, set_date_tzinfo
from pelican.writers import Writer

logger = logging.getLogger(__name__)


def latest_date(e):
    latest_date = e.date
    republish = getattr(e, "republish", None)
    # modified_date = getattr(e, 'modified', None)
    if republish:
        republish_date = get_date(republish)
        republish_date = set_date_tzinfo(republish_date, "UTC")
        if republish_date > latest_date:
            latest_date = republish_date
    # if modified_date:
    #    if modified_date > latest_date:
    #        latest_date = modified_date
    return latest_date


class SocialRSSWriter(Writer):
    def _add_item_to_the_feed(self, feed, item):
        tz_info = item.date.tzinfo
        now = datetime.now(tz_info)
        if item.date > now:
            # Don't add future items to feed.
            return

        if hasattr(item, "subpart_of"):
            # Don't add subparts to the feed.
            return

        if hasattr(item, "seotitle"):
            title = item.seotitle
        else:
            title = markupsafe.Markup(
                "%s — %s" % (item.title, item.subtitle)
                if hasattr(item, "subtitle")
                else item.title
            ).striptags()

        if hasattr(item, "isrepublished"):
            notice = getattr(item, "republishnote", None)
            if notice:
                title = f"{title} ({notice})"

        # Replace tag/category names with with hashtags.
        if hasattr(item, "tags"):
            social_max_hashtags = self.settings.get("SOCIAL_FEED_MAX_HASHTAGS", 3)
            modifications = 0
            prev_title = title
            for tag in item.tags:
                # Only replace where preceded by space, so don't replace inside other tags.
                title = re.sub(
                    f" {tag.name} ", f" #{tag.name} ", title, flags=re.IGNORECASE
                )
                if title != prev_title:
                    modifications += 1
                    if modifications >= social_max_hashtags:
                        break

                prev_title = title

        if isinstance(feed, Rss201rev2Feed):
            # RSS feeds use a single tag called 'description' for both the full
            # content and the summary
            content = None
            if self.settings.get("RSS_FEED_SUMMARY_ONLY"):
                description = item.summary
            else:
                description = item.get_content(self.site_url)

        else:
            content = item.get_content(self.site_url)
            description = item.summary
            if description == content:
                description = None

        link = "%s/%s" % (self.site_url, item.url)

        feed.add_item(
            title=title,
            link=link,
            unique_id=get_tag_uri(
                link, now
            ),  # Use todays date, so all items are new/unique.
            description=description,
            content=content,
            categories=item.tags if hasattr(item, "tags") else None,
            author_name=getattr(item, "author", ""),
            pubdate=set_date_tzinfo(item.date, self.settings.get("TIMEZONE", None)),
        )

    def write_feed(
        self,
        elements,
        context,
        path=None,
        url=None,
        feed_type="atom",
        override_output=False,
        feed_title=None,
    ):
        # Filter the feed to things which were within the last year only.
        social_max_age = self.settings.get("SOCIAL_FEED_MAX_AGE", 365)
        last_year = datetime.now(timezone.utc) - timedelta(days=social_max_age)

        elements = [e for e in elements if latest_date(e) > last_year]

        # Shuffle the elements in the feed. We are only interested in the tutorials feed
        # so we don't need to worry about time-specific stuff. All tutorials are fine to
        # resyndicate.
        random.shuffle(elements)

        social_max_items = self.settings.get("SOCIAL_FEED_MAX_ITEMS", None)
        if social_max_items:
            elements = elements[:social_max_items]

        return super().write_feed(
            elements,
            context,
            path=path,
            url=url,
            feed_type=feed_type,
            override_output=override_output,
            feed_title=feed_title,
        )


def write_custom_feed(generator):
    writer = SocialRSSWriter(
        output_path=generator.settings.get("OUTPUT_PATH"), settings=generator.settings
    )
    articles = generator.articles
    # Filter articles by SOCIAL_FEED_CATEGORIES
    social_feed_cats = generator.settings.get("SOCIAL_FEED_CATEGORIES")
    if social_feed_cats:
        articles = [a for a in articles if a.category.name in social_feed_cats]

    if generator.settings.get("SOCIAL_FEED_ATOM"):
        writer.write_feed(
            articles,
            generator.context,
            generator.settings["SOCIAL_FEED_ATOM"],
            generator.settings["SOCIAL_FEED_ATOM"],
        )

    if generator.settings.get("SOCIAL_FEED_RSS"):
        writer.write_feed(
            articles,
            generator.context,
            generator.settings["SOCIAL_FEED_RSS"],
            generator.settings["SOCIAL_FEED_RSS"],
            feed_type="rss",
        )


def register():
    signals.article_generator_finalized.connect(write_custom_feed)
