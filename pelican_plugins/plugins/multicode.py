'''
Extract and generate admonitions in articles.
'''

from __future__ import unicode_literals

import os
import re
from tempfile import NamedTemporaryFile

from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from markdown import Markdown
from pelican import contents, signals
from pelican.readers import MarkdownReader
from pelican.utils import pelican_open, slugify
import uuid

# Extract multicode blocks. We can explode + replace with HTML before Markdown processor.
multicode_re = re.compile(r'```[^`]*(?:```\n```[^`]*)+```')
blocks_re = re.compile(r'```(.*?)\n([^`]*?)```')
codeblock_re = re.compile('<pre><code( class="(.*?)")?>(.*?)<\/code><\/pre>', re.M | re.S)


def replace_multicode(m):

    tabs = []
    codeblocks = []
    current = "current"
    s = m.group(0)
    blocks = blocks_re.findall(s)

    def _is_python(s):
        s = s.lower()
        return any(l in s for l in ['pyside', 'pyqt'])

    for title, code in blocks:

        parts = title.split(':')
        if len(parts) > 1:
            language, title = parts

        else:
            language = 'python' if _is_python(title) else title

        slug = uuid.uuid4().hex

        tabs.append(f"""<li class="tab-link {current}" data-tab="{slug}" v-on:click="switch_tab">{title}</li>""")
        codeblocks.append(
            f"""<div id="{slug}" class="tab-content {current} code-block-outer">
                <pre><code class="{language}">{code}</code></pre>
                </div>
            """
        )

        # Only the first block is current.
        current = ''

    tabs = '\n'.join(tabs)
    codeblocks = '\n'.join(codeblocks)

    return f"""<div class="tabbed-area multicode"><ul class="tabs">{tabs}</ul>{codeblocks}</div>"""


class MulticodeMixin:
    def read(self, source_path):

        self._source_path = source_path
        self._md = Markdown(**self.settings['MARKDOWN'])
        with pelican_open(source_path) as text:
            text = multicode_re.sub(replace_multicode, text)
            content = self._md.convert(text)

        if hasattr(self._md, 'Meta'):
            metadata = self._parse_metadata(self._md.Meta)
        else:
            metadata = {}
        return content, metadata


class MulticodeMarkdownReader(MulticodeMixin, MarkdownReader):
    pass


def add_reader(readers):
    for ext in MulticodeMarkdownReader.file_extensions:
        readers.reader_classes[ext] = MulticodeMarkdownReader


def generate_codeblocks(content):
    if isinstance(content, contents.Static):
        return

    def replace_codeblocks(m):
        language = m.group(2) or 'python'
        code = m.group(3)
        return '''
        <div class="code-block">
        <span class="code-block-language code-block-{0}">{0}</span>
        <pre><code class="{0}">{1}</code></pre>
        </div>
        '''.format(
            language, code
        )

    content._content = codeblock_re.sub(replace_codeblocks, content._content)


def register():
    signals.readers_init.connect(add_reader)
    signals.content_object_init.connect(generate_codeblocks)

