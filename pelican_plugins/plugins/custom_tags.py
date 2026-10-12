"""
Extract and generate custom tags in markdown articles.
"""

import re

from pelican import contents, signals

admonitions_re = re.compile(r"<p>([A-Za-z]*:)")

mdash_re = re.compile(r" -- ")

video_re = re.compile(r"\@\[video (.*?)\]")
imgur_re = re.compile(r"\@\[imgur (.*?)\]")
gfycat_re = re.compile(r"\@\[gfycat (.*?)\]")
youtube_re = re.compile(r"\@\[youtube (.*?)\]")
vimeo_re = re.compile(r"\@\[vimeo (.*?)\]")
tella_re = re.compile(r"\@\[tella (.*?)\]")
button_re = re.compile(r'\@\[button "(.*?)"\s(.*?)\]')


def _match_inline_tag(m):
    tag = m.group(1).lower()
    return f'<a href="/topics/{tag}/" class="tag tag-{tag} inline-tag">{tag}</a>'


def _match_admonitions(m):
    label = m.group(1)[:-1].lower()  # Chop off the trailing colon.
    kind = {
        "info": "fa-info",
        "tip": "fa-lightbulb",
        "run": "fa-rocket",
        "note": "fa-sticky-note",
        "ok": "fa-check",
        "warning": "fa-exclamation-circle",
        "fun": "fa-pastafarianism",
        "update": "fa-plus-square",
        "comment": "fa-comments",
        "important": "fa-exclamation",
    }.get(label)

    if kind is None:
        return m.group(0)

    return f'<p class="admonition admonition-{label}"><span class="admonition-kind"><i class="fas {kind}"></i></span> '


def _match_mdash(m):
    return " &mdash; "


def _match_video(m):
    url = m.group(1)
    return f'''
    <video width="700" height="500" muted loop playsinline preload="none" loading="lazy" v-observe-visibility="playVideo">
        <source src="{url}" type="video/mp4">
    </video>
    '''


def _match_imgur(m):
    identifier = m.group(1)
    return f"""
    <video width="700" height="500" muted loop playsinline preload="none" loading="lazy" v-observe-visibility="playVideo">
        <source src="https://i.imgur.com/{identifier}.mp4" type="video/mp4">
        <source src="https://i.imgur.com/{identifier}.webm" type="video/webm">
    </video>
    """


def _match_gfycat(m):
    identifier = m.group(1)
    return f"""
    <video width="700" height="500" muted loop playsinline preload="none" loading="lazy" class="video media" poster="https://thumbs.gfycat.com/{0}-mobile.jpg" v-observe-visibility="playVideo">
        <source src="https://giant.gfycat.com/{identifier}.webm" type="video/webm">
        <source src="https://giant.gfycat.com/{identifier}.mp4" type="video/mp4">
        <source src="https://thumbs.gfycat.com/{identifier}-mobile.mp4" type="video/mp4">
    </video>
    """


def _match_youtube(m):
    identifier = m.group(1)
    # Extract the id only.
    identifier = identifier.replace("https://youtu.be/", "")
    identifier = identifier.replace("https://www.youtube.com/embed/", "")
    return f"""
    <iframe width="700" height="500"
    src="https://www.youtube.com/embed/{identifier}?rel=0"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen>
    </iframe>
    """


def _match_vimeo(m):
    identifier = m.group(1)
    identifier = identifier.replace("https://player.vimeo.com/video/", "")
    return f"""
    <div style="padding:79.5% 0 0 0;position:relative;"><iframe src="https://player.vimeo.com/video/{identifier}?badge=0&autoplay=1&loop=1&amp;autopause=1&amp;quality_selector=1&amp;player_id=0&amp;app_id=58479&background=1" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" style="position:absolute;top:0;left:0;width:100%;height:100%;" title="pyqtgraph-dynamic-plot"></iframe></div><script src="https://player.vimeo.com/api/player.js"></script>
    """


def _match_tella(m):
    identifier = m.group(1)
    # Strip URL parts if included.
    identifier = identifier.replace("https://www.tella.tv/video/", "")
    identifier = identifier.replace("/embed", "")
    return f"""
    <div style="position: relative; padding-bottom: 56.25%; height: 0;">
    <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" src="https://www.tella.tv/video/{identifier}/embed?b=0&title=0&a=0&autoPlay=true&loop=1&t=0&muted=1&wt=0" allowfullscreen allowtransparency></iframe>
    </div>
    """


def _match_button(m):
    title = m.group(1)
    url = m.group(2)
    return f"""
    <a href="{url}" target="_blank" class="pure-button button-primary button-buy">{title} <i class="fas fa-arrow-right"></i></a>
    """


ctypes = []


def generate_custom_tags(content):
    if isinstance(content, contents.Static):
        return

    content._content = admonitions_re.sub(_match_admonitions, content._content)
    # content._content = inline_tag_re.sub(_match_inline_tag, content._content)
    content._content = video_re.sub(_match_video, content._content)
    content._content = imgur_re.sub(_match_imgur, content._content)
    content._content = gfycat_re.sub(_match_gfycat, content._content)
    content._content = youtube_re.sub(_match_youtube, content._content)
    content._content = vimeo_re.sub(_match_vimeo, content._content)
    content._content = tella_re.sub(_match_tella, content._content)
    content._content = button_re.sub(_match_button, content._content)


def register():
    signals.content_object_init.connect(generate_custom_tags)
