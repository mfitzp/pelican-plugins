# -*- coding: utf-8 -*-

import sys

from pelican import signals

from . pelican_code_include_markdown_extension import PelicanCodeIncludeMarkdownExtension

def code_include_markdown_extension(pelicanobj):

    # Instantiate Markdown extension and append it to the current extensions
    try:
        if isinstance(pelicanobj.settings.get('MD_EXTENSIONS'), list):  # pelican 3.6.3 and earlier
            pelicanobj.settings['MD_EXTENSIONS'].append(PelicanCodeIncludeMarkdownExtension())
        else:
            pelicanobj.settings['MARKDOWN'].setdefault('extensions', []).append(PelicanCodeIncludeMarkdownExtension())
    except:
        sys.excepthook(*sys.exc_info())
        sys.stderr.write("\nError - Code include extension is non-functional.\n")
        sys.stderr.flush()

def pelican_init(pelicanobj):
    # Configure Markdown Extension
    code_include_markdown_extension(pelicanobj)

def register():
    """Plugin registration"""
    signals.initialized.connect(pelican_init)
