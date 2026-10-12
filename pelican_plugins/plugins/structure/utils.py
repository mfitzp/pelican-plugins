import os
import logging


def yield_files(root):
    root = os.path.realpath(os.path.abspath(root))

    for dirpath, dirnames, filenames in os.walk(root):
        for dirname in list(dirnames):
            try:
                if dirname.startswith("."):
                    dirnames.remove(dirname)
            except IndexError:
                # duplicate already removed?
                pass
        for filename in filenames:
            if filename.startswith("."):
                continue
            yield os.path.join(dirpath, filename)


def make_page(cls, readers, context, filename):
    base_path, filename = os.path.split(filename)
    page = readers.read_file(base_path, filename, cls, None, context)
    return page


def make_pages(cls, readers, context, path):
    pages = []
    for filename in yield_files(path):
        try:
            page = make_page(cls, readers, context, filename)
        except Exception:
            logging.exception("Could not make %s: %r", cls, filename)
            continue
        pages.append(page)
    return pages
