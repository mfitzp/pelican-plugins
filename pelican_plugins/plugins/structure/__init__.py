from pelican import signals

from . import courses, crosslinks, tracks


def process(generator):
    courses.process_courses(generator)
    tracks.process_tracks(generator)
    crosslinks.process_crosslinks(generator)


def write(generator, writer):
    courses.write_courses(generator, writer)
    courses.write_index(generator, writer)

    tracks.write_tracks(generator, writer)
    # tracks.write_index(generator, writer)


def register():
    signals.article_generator_finalized.connect(process)
    signals.article_writer_finalized.connect(write)
