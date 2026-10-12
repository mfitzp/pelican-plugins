from datetime import datetime

from pelican import signals

CURRENT_YEAR = datetime.now().year


def generate_dynamic_titles(content):
    # Substitute current year in titles.
    for attrib in ("title", "seotitle", "subtitle", "_content", "description"):
        v = getattr(content, attrib, None)
        if v and "{current_year}" in v:
            v = v.replace("{current_year}", f"{CURRENT_YEAR}")
            setattr(content, attrib, v)


def register():
    signals.content_object_init.connect(generate_dynamic_titles)
