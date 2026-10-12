'''
Rewrite md files to put replace (../images/ with {static}/images/.
'''

from __future__ import unicode_literals
import re
import os

from pelican import contents, signals
from pelican.contents import Article, Page

images_re = re.compile('(src=\".*?\")')
cache = {}
exclude = ['{attach}', '{static}', '..', '//', '/images/']

def process_content(article):
    # <p><img alt="DiffCast Logo" src="{attach}icon.png"  loading="lazy" width="128" height="128" /></p>

    if not isinstance(article, Article) and not isinstance(article, Page):
        return

    # Process all images in the article.
    for img in images_re.findall(article._content):
        # If local, not static, not already marked attach, not http/etc.
        if any(x in img for x in exclude):
            continue

        # Check the image is in the same folder.
        folder = os.path.dirname(article.source_path)
        img_fn = img[5:-1]
        image_filepath = os.path.join(folder, img_fn)
        if not os.path.exists(image_filepath):
            continue

        # File exists, replace barename with {attach}.
        article._content = article._content.replace(
            img,
            img[:5] + '{attach}' + img[5:]
        )


def register():
    signals.content_object_init.connect(process_content)