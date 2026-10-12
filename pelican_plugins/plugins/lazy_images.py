'''
Extract and generate custom tags in markdown articles.
'''


import json
import os
import re

from pelican import contents, signals
from PIL import Image

attachedsrc_re = re.compile(r'src=\"{static}(.*?\.(png|jpg|jpeg))\"', re.IGNORECASE)

IMAGE_METADATA_PATH = 'image_metadata.json'

image_metadata = {}

# Cache image metadata for build speed.
def read_metadata(_):
    try:
        with open(IMAGE_METADATA_PATH, 'r') as f:
            image_metadata.update(json.load(f))
    except:
        pass


def generate_lazy_load_images(content):

    if isinstance(content, contents.Static):
        return

    html = content._content
    matches = attachedsrc_re.findall(html)

    for match in matches:
        image_src = match[0]

        rd, _ = os.path.split(content.relative_source_path)

        image_id = os.path.join(rd, image_src)
        if image_id in image_metadata:
            width, height = image_metadata[image_id]
        else:
            ad, _ = os.path.split(content.source_path)
            image_path = os.path.join(ad, image_src)
            im = Image.open(image_path)
            width, height = im.size
            image_metadata[image_id] = (width, height)

        image_cdn_base = content.settings.get('IMAGE_CDN_BASE')
        if image_cdn_base:
            srcset = ', '.join(
                [
                    f'{image_cdn_base}/{rd}/{image_src}?tr=w-100 100w',
                    f'{image_cdn_base}/{rd}/{image_src}?tr=w-200 200w',
                    f'{image_cdn_base}/{rd}/{image_src}?tr=w-400 400w',
                    f'{image_cdn_base}/{rd}/{image_src}?tr=w-600 600w',
                ]
            )
            srcset = f'srcset="{srcset}"'
        else:
            srcset = ''

        html = html.replace(
            f'src="{{static}}{image_src}"', f'src="{{static}}{image_src}" {srcset} loading="lazy" width="{width}" height="{height}"'
        )


    content._content = html


def write_metadata(_):
    with open(IMAGE_METADATA_PATH, 'w') as f:
        json.dump(image_metadata, f)


def register():
    signals.initialized.connect(read_metadata)
    signals.content_object_init.connect(generate_lazy_load_images)
    signals.finalized.connect(write_metadata)
