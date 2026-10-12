"""
Rewrite md files to put replace (../images/ with {static}/images/.
"""

from __future__ import unicode_literals

import re

from pelican import signals
from pelican.contents import Article, Page

static_images_re = re.compile(r'src="\./(.*?)"', flags=re.DOTALL)


def process_content(article):
    if not isinstance(article, Article) and not isinstance(article, Page):
        return

    article._content = static_images_re.sub(r'src="{static}\1"', article._content)


def register():
    signals.content_object_init.connect(process_content)
