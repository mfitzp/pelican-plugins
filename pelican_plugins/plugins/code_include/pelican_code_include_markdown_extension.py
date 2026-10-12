# -*- coding: utf-8 -*-

import logging
import os
import re

import markdown
from markdown.util import Processor

code_re = re.compile("(\s*)include\:\:(?P<path>.*)\[(tags=)*(?P<tag>[a-zA-Z0-9\-_]+)\]")

extensions = {".py": "python"}


def _indent_strip(s):
    if not s.startswith("    "):
        return "    " + s.rstrip()
    return s.rstrip()


class CodeIncludePreProcessor(Processor):
    def run(self, lines):
        lines_out = []

        for line in lines:
            m = code_re.match(line)
            if m:
                args = m.groupdict()
                path = args["path"]
                tag = args["tag"]

                code_path = os.path.join("content", path)

                if not os.path.exists(code_path):
                    logging.error("File {0} could not be found".format(code_path))
                    lines_out.append(line)
                    continue

                # Auto-indent the initial line by at least
                ext = os.path.splitext(path)[1]
                if ext in extensions:
                    lines_out.append("    :::" + extensions[ext])

                with open(code_path) as f:
                    if tag:
                        # Find first and last occurrence, include what is between.
                        store = False
                        for line in f:
                            if ("tag::%s[" % tag) in line:
                                store = True
                                continue
                            if ("end::%s[" % tag) in line:
                                break
                            if store:
                                lines_out.append(_indent_strip(line))
                    else:
                        # No tag, include it all.
                        lines_out.extend(_indent_strip(l) for l in f)

            else:
                lines_out.append(line)

        return lines_out


class PelicanCodeIncludeMarkdownExtension(markdown.Extension):
    """A Markdown extension enabling processing in Markdown for Pelican"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.preprocessors["codeinclude"] = CodeIncludePreProcessor(md)
