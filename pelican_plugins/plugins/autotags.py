
from collections import defaultdict
from pelican import signals
from logging import warning
from operator import itemgetter
from pelican.urlwrappers import Tag
from pelican.contents import Article

def autotag_article(content_object):

    # Get the tag mapper. For each article, we iterate
    # through the tags: if any are in AUTOTAGS we
    # automatically add on those in the map.
    AUTOTAGS = content_object.settings.get('AUTOTAGS', {})

    if not isinstance(content_object, Article) or not hasattr(content_object, 'tags'):
        return

    for tag in content_object.tags:

        for tagn in AUTOTAGS.get(tag.name, []):
            tago = Tag(tagn, content_object.settings)
            if tago not in content_object.tags:
                content_object.tags.append(tago)

def synthetictag_article(content_object):
    # Create automerge tags between everythig in the two lists (where something exists on the article).
    SYNTHETIC_TAGS = content_object.settings.get('SYNTHETIC_TAGS', {})

    if not isinstance(content_object, Article) or not hasattr(content_object, 'tags'):
        return

    has_modified = True
    while has_modified:
        has_modified = False

        tagmap = {tag.name:tag for tag in content_object.tags}

        for head,tails in SYNTHETIC_TAGS.items():
            if head in tagmap:
                for tail in tails:
                    if tail in tagmap:
                        # Heads & tails are in our tags. Check if synthtag in map.
                        synth = f'{head}-{tail}'
                        if synth not in tagmap:
                            # Create synthtag and add it.
                            stag = Tag(synth, content_object.settings)
                            # Store head/tail for styling.
                            stag.parents = [head, tail]
                            content_object.tags.append(stag)
                            tagmap[stag.name] = stag
                            has_modified = True


def register():
    signals.content_object_init.connect(autotag_article)
    signals.content_object_init.connect(synthetictag_article)
