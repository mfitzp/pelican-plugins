# -*- coding: utf-8 -*-

from pelican import signals
from six import text_type

from pelican.utils import slugify
from pelican.contents import Page
import logging

from .utils import make_pages



class Track(Page):
    default_template = 'track'


# class TrackIndex(Page):
#    default_template = 'track_index'



def get_track_pages(generator):
    settings = generator.settings
    readers = generator.readers
    context = generator.context

    tracks_path = settings.get("TRACK_PAGE_PATH", "tracks")
    return make_pages(Track, readers, context, tracks_path)


def create_track(generator, track_page):
    # Create a track page, holding the parts to display.
    track = Track(track_page.content, settings=generator.settings)
    track.page = track_page

    for attr in ['title', 'subtitle', 'date', 'author', 'template', 'slug', 'image', 'featured', 'parts']:
        v = getattr(track_page, attr, None)
        if v is not None:
            setattr(track, attr, v)

    track.first_part = track.parts[0] if track.parts else None
    track.last_part = track.parts[-1] if track.parts else None

    if track.first_part and track.first_part.all_articles:
        track.first_article = track.first_part.all_articles[0]
    else:
        track.first_article = None

    track.all_articles = [a for c in track.parts for a in c.all_articles]

    for part in track.parts:
        part.track = track

    return track


def process_tracks(generator):

    track_pages = get_track_pages(generator)

    # Collect required part slugs, so we can find the course in one pass.
    part_slugs = [slug for bp in track_pages for slug in bp.parts]
    course_map = {o.slug:o for o in generator.courses if o.slug in part_slugs}

    # Cycle through the track pages, iterating parts.
    # Lookup articles, collection objects by slug.
    tracks = []
    for track_page in track_pages:
        logging.debug("Processing track: %s (%s)", track_page.title, track_page.slug)
        logging.debug("- parts: %s", track_page.parts)
        # Iterate the "parts" of this track page, looking up those course by slug.
        track_page.parts = [course_map[s] for s in track_page.parts if s]
        track = create_track(generator, track_page)
        tracks.append(track)

    generator.tracks = tracks
    generator._update_context(['tracks'])


def write_tracks(generator, writer):
    # Write individual collection files.
    for track in generator.tracks:
        logging.info("Writing track page %s (%s)", track.title, track.slug)
        signals.page_generator_write_page.send(
            generator,
            content=track
        )
        writer.write_file(
            track.save_as, generator.get_template(track.template),
            generator.context, track=track, page=track.page,
            override_output=hasattr(track, 'override_save_as'),
            relative_urls=generator.settings['RELATIVE_URLS']
        )


# def write_index(generator, writer):
#    # Write the collection index, under collection/index.html.
#    index = TrackIndex("", settings=generator.settings)
#    index.title = generator.settings.get("TRACK_INDEX_TITLE", "Tracks")
#    index.slug = "index"
#    index.all_tracks = generator.tracks
#
#    writer.write_file(
#        index.save_as, generator.get_template(index.template),
#        generator.context,
#        track_index=index,
#        override_output=hasattr(index, 'override_save_as'),
#        relative_urls=generator.settings['RELATIVE_URLS']
#    )
