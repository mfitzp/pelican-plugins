"""
Export data into the repo root, which can be fed into models
to help with writing and other tasks.
"""

import os

from pelican import signals

basename = os.path.dirname(__file__)
data_folder = os.path.join(basename, "..", "data")


def export_article_links(generator, writer):
    # We always want the live site, so we can use for link insertion.
    # If not, fall back to relative URLs.
    site_url = generator.settings.get("LIVEURL", "")
    urls = []
    seo_errors = []

    for article in generator.articles:
        urls.append(f"{site_url}/{article.url}\n")
        if (
            not getattr(article, "seotitle", None)
            or not getattr(article, "description", None)
            or '<a href="' not in article.content
        ):
            # We don't care about image here, since we can't autofix.
            seo_errors.append(f"{article.slug}\n")

    output_path = os.path.join(data_folder, "urls.txt")
    with open(output_path, "w") as f:
        f.writelines(urls)

    output_path = os.path.join(data_folder, "seo_errors.txt")
    with open(output_path, "w") as f:
        f.writelines(seo_errors)


def register():
    # This needs to be triggered after all articles are written, otherwise
    # Pelican fails to handle {static} urls.
    signals.article_writer_finalized.connect(export_article_links)
