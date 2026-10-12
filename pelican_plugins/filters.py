import collections
import datetime
import json
import os
import random
import re
from collections import defaultdict, namedtuple
from itertools import zip_longest
from operator import itemgetter
from random import shuffle

import humanize
import markdown
import requests
from csscompressor import compress as csscompress
from jsmin import jsmin
from pelican.utils import get_date, set_date_tzinfo, slugify

p_re = re.compile(r"</?p[^>]*?>")

ps_re = re.compile(r"<p>.*?<\/p>", re.S)

re_striptags = re.compile(r"<[^>]*?>")
re_stripimgs = re.compile(r"<img[^>]*?>")
re_stripdivs = re.compile(r"<div.*</div>", re.S)
re_striplink = re.compile(r"<a[^>]*?>([^<]*?)</a>")
re_truncatecode = re.compile(
    r"<pre[^>]*?><code[^>]*?>((?:.*\n){1,10})[\S\s]*?</code></pre>"
)

re_parts = re.compile(r"<!--[^>]*?>")

DOCUMENT_ICONS = {
    ".pdf": "fas fa-file-pdf",
    ".mobi": "fas fa-book",
    ".epub": "fas fa-book",
    ".zip": "fas fa-file-archive",
    ".dmg": "fab fa-apple",
    ".deb": "fab fa-ubuntu",
    ".exe": "fab fa-windows",
    ".dsk": "fas fa-save",
}

MIN_TITLE_LENGTH = 30
MAX_TITLE_LENGTH = 60


github_repo_data = {}


def human_format(num, dp=2):
    format_s = "{" + f":.{dp}g" + "}"
    num = float(format_s.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return "{}{}".format(
        "{:f}".format(num).rstrip("0").rstrip("."), ["", "K", "M", "B", "T"][magnitude]
    )


def fn_escape(s):
    return s.replace('"', '"')


def fn_github(repo_path, key=None):
    if repo_path not in github_repo_data:
        print(f"Fetching data for Github: {repo_path}")
        r = requests.get(f"https://api.github.com/repos/{repo_path}")
        github_repo_data[repo_path] = None  # Don't retry.
        if r.status_code == 200:
            data = r.json()
            stargazers_count = data.get("stargazers_count")
            if stargazers_count:  # Only show if positive.
                github_repo_data[repo_path] = {
                    "stargazers_count": human_format(stargazers_count)
                }
    if key:
        return github_repo_data[repo_path].get(key)
    else:
        return github_repo_data[repo_path]


def filter_first_p(content):
    m = ps_re.search(content)
    if m:
        return m.group(0)
    return content


def filter_strip_comment_tags(s):
    # Remove images
    s = re_stripimgs.sub("", s)

    # Remove lightboxes
    s = re_stripdivs.sub("", s)

    # Truncate code blocks
    s = re_truncatecode.sub(r"<pre><code>\1</code></pre>", s)

    # Convert links to text
    s = re_striplink.sub(r"\1", s)

    return s


def filter_pluralize(number, singular="", plural="s"):
    if number == 1:
        return singular
    else:
        return plural


def filter_minify_js(s):
    return jsmin(s)


def filter_minify_css(s):
    return csscompress(s)


def filter_json(o):
    return json.dumps(o)


def filter_trim_by_multiple(articles, n, max=None):
    """Trim the list of articles to the nearest multiple of n less
    than the total number of articles. Gives complete rows in card stacks."""
    if max:
        articles = articles[:max]
    n_articles = len(articles)
    n_rounded = (n_articles // n) * n
    return articles[:n_rounded]


def filter_meta_description(value):
    """Returns the given HTML with all tags stripped."""
    first_sentence, *_ = value.split(".", 1)
    return re_striptags.sub("", first_sentence).replace("\n", " ") + "."


def filter_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def filter_date(dt):
    return dt.strftime("%Y-%m-%d")


def filter_markdown(content, *args):
    return markdown.markdown(content)


def filter_ucfirst(s):
    return s[0].upper() + s[1:]


def filter_slugify(s):
    return slugify(s).replace(" ", "-")


def filter_shuffle(seq):
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq


def filter_is_list(o):
    return isinstance(o, list)


def filter_as_dict(o):
    return dict(o)


def filter_as_set(seq):
    if (not isinstance(seq, collections.Iterable)) or isinstance(seq, str):
        seq = [seq]

    try:
        result = set(seq)
        return result
    except:
        return seq


def filter_as_list(seq):
    if (not isinstance(seq, collections.Iterable)) or isinstance(seq, str):
        seq = [seq]

    return seq


def filter_is_recent(dt):
    tz_info = dt.tzinfo
    now = datetime.datetime.now(tz_info)
    return now - datetime.timedelta(weeks=12) < dt > now


def filter_exclude_tags(tags, exclude):
    if exclude:
        return [t for t in tags if t not in exclude]

    return tags


def filter_split_on_first_h2(article_content, minimum_h2=3):
    # Split to find the total number of headers in the article.
    result = article_content.split("<h2")

    # If less than minimum_h2, ignore, just return the content, no header.
    if len(result) < minimum_h2:
        return "", article_content

    # Re-split to minimize the chance of errors.
    result = article_content.split("<h2", 1)

    # If more than minimum, split off the first result, reassemble the rest.
    return result[0], "<h2" + result[1]


############
# PRODUCTS #
############


def filter_insert_products(s, products):
    split_on_p = s.split("</p>")
    total_parts = len(split_on_p)

    products = products.strip().split("<!-- end -->")

    if not products:
        return s

    insert_at = min(total_parts, 7)
    max_inserts = 2
    then_every = (total_parts - insert_at) // (max_inserts - 1)

    # Shuffle after cropping to max.
    products = products[:max_inserts]
    shuffle(products)

    result = []
    for n, chunk in enumerate(split_on_p, 1):
        if products and n == insert_at:
            product = products.pop(0)
            result.append(chunk + product)
            insert_at += then_every
        else:
            result.append(chunk)

    return "</p>".join(result)


def filter_select_products(products, article_tags):
    return [
        product for product in products if set(product.tags).intersection(article_tags)
    ]


def duplicate_products_by_priority(products):
    # Iterate a list of products, duplicating n* for priority
    # and then shuffling the result.
    result = [product for product in products for _ in range(product.priority)]
    shuffle(result)
    return result


def filter_get_article_product(products, article):
    products = filter_get_article_products(products, article)
    if products:
        return products[0]


def filter_get_article_products(products, article):
    """Get products for an article via various methods.
    Products a single long-list, with no duplicates, with the most relevant
    products near the beginning.
    """
    # Shuffle every time, so each page is different.
    products = duplicate_products_by_priority(products)
    article_products = []
    if hasattr(article, "products"):
        manual_products = filter_get_products(products, article.products)
        article_products.extend(manual_products)
    if hasattr(article, "tags"):
        tag_products = filter_products_for_tags(products, article.tags)
        article_products.extend(tag_products)

    article_products += products  # Add irrelevant.

    # Try and avoid repetition.
    final_products = []
    to_append = []
    for product in article_products:
        if product in final_products:
            to_append.append(product)
            continue
        final_products.append(product)
    final_products.extend(to_append)
    return final_products


def filter_get_products(products, article_products):
    if not article_products:
        return []
    req_products = article_products.split(",")
    result = [product for product in products if product.id in req_products]
    # Sort by priority. Highest priority first.
    # result.sort(key=lambda p:p.priority, reverse=True)
    return result


def filter_get_product(products, article_products):
    products = filter_get_products(products, article_products)
    if products:
        return products[0]


def filter_products_for_tags(products, tags):
    if isinstance(tags, list):
        tags = [tag.name for tag in tags]
    elif isinstance(tags, str):
        tags = tags.split(",")
    else:
        tags = [tags.name]

    result = [
        product for product in products if any(tag in product.tags for tag in tags)
    ]
    # Sort by priority. Highest priority first.
    # result.sort(key=lambda p:p.priority, reverse=True)
    return result


###################
# Text Processing #
###################


def filter_pure_tables(s):
    return s.replace(
        "<table>", '<table class="pure-table pure-table-horizontal pure-table-tight">'
    )


def filter_strip_p(s):
    return p_re.sub("", s)


def filter_fullstop(s):
    if s and s[-1] != ".":
        return s + "."
    return s


############
# Taxinomy #
############


def filter_top_tags(tags, n=20, filter_by=None):
    tagcounts = []
    if filter_by:
        filter_by = [t.slug for t in filter_by]

    for tag, articles in tags:
        if filter_by and tag.slug not in filter_by:
            continue
        tagcounts.append((tag, len(articles)))

    tagcounts.sort(key=itemgetter(1), reverse=True)
    tagcounts = tagcounts[:n]
    return [t for t, _ in tagcounts]


def filter_order_tags(tags):
    def sort_algo(tag):
        t, _ = tag
        if hasattr(t, "page"):
            return getattr(t.page, "order", t.name)
        return t.name

    return sorted(tags, key=sort_algo)


def filter_get_page_tags(page, tags):
    tagmap = {t.name: (t, a) for t, a in tags}
    return [tagmap[t.name] for t in page.tags if t.name in tagmap]


def _tags_check(article, tags):
    for tag in getattr(article, "tags", []):
        if tag in tags:
            return True


def filter_filter_by(articles, category=None, tag=None, library=None):
    result = []
    for article in articles:
        if category is not None and article.category != category:
            continue

        if tag is not None and (
            not hasattr(article, "tags") or tag not in article.tags
        ):
            continue

        if library is not None and (
            not hasattr(article, "library") or article.library != library
        ):
            continue

        result.append(article)
    return result


def filter_category_articles(
    categories, category_name, tags=None, limit=5, reverse=True
):
    """Iterate categories lists, extracting articles for matches, sort by date, limit"""
    articles = set()

    for cat, carticles in categories:
        if cat.name == category_name:
            articles.update(carticles)

    articles = list(articles)

    # tag filter
    if tags:
        articles = [a for a in articles if _tags_check(a, tags)]

    articles.sort(key=lambda a: a.date, reverse=reverse)

    return articles[:limit]


def fn_get_topics(categories, tags):
    topics = []
    topics.extend(
        c
        for c, _ in categories
        if hasattr(c, "page") and c.page and hasattr(c.page, "featured")
    )
    topics.extend(t for t, _ in tags if hasattr(t, "page") and t.page)
    return topics


def filter_tags_with_icons(a, b):
    return [t for t in a if (hasattr(t, "slug") and t.slug in b) or (t in b)]


############
# Metadata #
############


def filter_any_new(articles):
    return any(filter_is_new(a) for a in articles)


def filter_get_new(articles):
    return [a for a in articles if filter_is_new(a)]


def filter_get_n_new(articles):
    return len([a for a in articles if filter_is_new(a)])


def filter_is_new(article):
    if hasattr(article, "isrepublished"):
        return False
    tz_info = article.date.tzinfo
    now = datetime.datetime.now(tz_info)
    return now - datetime.timedelta(days=5) < article.date < now


def filter_any_modified(articles, days=1):
    return any(filter_is_modified(a, days=days) for a in articles)


def filter_get_modified(articles, days=1):
    return [a for a in articles if filter_is_modified(a, days=days)]


def filter_get_n_modified(articles, days=1):
    return len([a for a in articles if filter_is_modified(a, days=days)])


def filter_is_modified(article, days=1):
    if not hasattr(article, "modified"):
        return False
    tz_info = article.date.tzinfo
    now = datetime.datetime.now(tz_info)
    return now - datetime.timedelta(days=days) < article.modified < now


def filter_copyrightrange(articles):
    if not articles:
        today = datetime.datetime.now().year
        return f"{today}"

    oldest = articles[-1].date.year
    newest = articles[0].date.year
    return f"{oldest}-{newest}"


def filter_prepare_downloads(downloads):
    if not isinstance(downloads, list):
        downloads = [downloads]

    result = []
    for line in downloads:
        if "," in line:
            title, url = line.split(",")
        else:
            title = os.path.basename(line)
            url = line

        ext = os.path.splitext(url)[1].lower()
        icon = DOCUMENT_ICONS.get(ext, "fas fa-file")

        result.append({"title": title, "url": url, "icon": icon})

    return result


#######
# SEO #
#######


def filter_generate_title(obj, sitename, sitesubtitle):
    # Use SEO title if set.
    seotitle = getattr(obj, "seotitle", None)
    if seotitle:
        return seotitle.replace(" -- ", " &mdash; ")

    # Use default title.
    title = obj.title.replace(" -- ", " &mdash; ")

    # if hasattr(obj, 'codelang'):
    #    langs = ', '.join(obj.codelang.split(','))
    #    title += ' (%s)' % langs

    if "&mdash;" not in title:
        subtitle = getattr(obj, "subtitle", None)
        if subtitle:
            cl = len(title)
            al = cl + len(subtitle) + 2
            if _title_should_extend(cl, al):
                title += f" &mdash; {subtitle}"

    if "&mdash;" not in title:
        # Iterate some optional extensions to the title, add if doesn't make it too long.
        te = [
            f" &mdash; {sitesubtitle} by {sitename}",
            f" &mdash; {sitesubtitle}",
            f" &mdash; {sitename}",
        ]

        for t in te:
            cl = len(title)
            al = cl + len(t) + 2
            if _title_should_extend(cl, al):
                title += t
                break

    return title


def get_object_social_image(obj):
    if hasattr(obj, "seoimage"):
        return obj.seoimage
    if hasattr(obj, "image"):
        return obj.image


def filter_get_social_image(obj):
    # Auto-select the optimum image for an article/page, based on
    # settings. Selects in this order:
    # - SEO image
    # - article image (non-SEO optimized)
    # - course image
    # - track image
    # - tag image (any tag)
    # - category image
    # - site image
    image = get_object_social_image(obj)
    if image:
        return image

    if hasattr(obj, "course"):
        image = get_object_social_image(obj.course)
        if image:
            return image

    if hasattr(obj, "track"):
        image = get_object_social_image(obj.course)
        if image:
            return image

    if hasattr(obj, "tags"):
        # This is unreliable, sometimes tag pages have not been processed beforehand.
        for tag in obj.tags:
            if hasattr(tag, "page"):
                image = get_object_social_image(tag.page)
                if image:
                    return image

    # if hasattr(article, 'library'):
    #    # We need to look up the pages manually, they're not linked in the library objects.
    #    image = get_object_social_image(article.library)
    #    if image:
    #        return image

    if hasattr(obj, "category") and hasattr(obj.category, "page"):
        image = get_object_social_image(obj.category.page)
        if image:
            return image

    return "theme/images/logo-card.png"


def get_object_social_image(obj):
    if hasattr(obj, "seoimage"):
        return obj.seoimage
    if hasattr(obj, "image"):
        return obj.image


#############
# Ecommerce #
#############


def filter_get_author_page(authors, article_author):
    for author, _ in authors:
        if author.slug == article_author.slug:
            return author.page


def filter_books_tagged(books, tag):
    return [book for book in books if tag in book.page.tags]


def _title_should_extend(cl, al):
    return al <= MAX_TITLE_LENGTH or cl < MIN_TITLE_LENGTH


def filter_fullstop(s):
    if s and s[-1] != ".":
        return s + "."
    return s


def filter_prepare_downloads(downloads):
    if not isinstance(downloads, list):
        downloads = [downloads]

    result = []
    for line in downloads:
        if "," in line:
            title, url = line.split(",")
        else:
            title = os.path.basename(line)
            url = line

        ext = os.path.splitext(url)[1].lower()
        icon = DOCUMENT_ICONS.get(ext, "fas fa-file")

        result.append({"title": title, "url": url, "icon": icon})

    return result


def filter_merge_feeds(articles, *args):
    """
    Merge any number of alternate feeds with the article list,
    keeping them sorted in chronological order.
    """
    articles = articles[:]  # copy
    for feed in args:
        articles.extend(feed)
    return sorted(articles, key=lambda x: x.date, reverse=True)


def filter_get_email_tags(email_tags, article_tags):
    tags = []
    article_tags = [tag.name.lower() for tag in article_tags if hasattr(tag, "name")]
    for tag in email_tags:
        if tag.lower() in article_tags:
            tags.append(tag)
    return ";".join(tags)


def filter_humanize(value):
    return humanize.naturalday(value)


def fn_get_featured(courses, books):
    result = []
    result.extend([c for c in courses if hasattr(getattr(c, "page", None), "featured")])
    result.extend(
        [cgrp for cgrp in books if hasattr(getattr(cgrp, "page", None), "featured")]
    )
    random.shuffle(result)
    return result


def filter_latest_modified(articles, n_articles=50):
    articles = sorted(articles, key=lambda a: a.modified, reverse=True)
    return articles[:n_articles]


def filter_library_articles(articles, library, n_total=6):
    farticles = []
    narticles = []

    # Iterate articles, adding them and accumulating totals for each library.
    # once all libraries have sufficient n_total, we can exit.
    for article in articles:
        if hasattr(article, "library"):
            if article.library == library:
                # Has a library, accumulate the library/
                farticles.append(article)
        else:
            # Non-library article, accumulate all.
            narticles.append(article)

        if len(farticles) >= n_total:
            break

    # Extend the list with non-library if they are not enough library-specific.
    if len(farticles) < n_total:
        farticles = (farticles + narticles)[:n_total]

    return farticles


def filter_library_tags(tags, library_tags):
    return [
        t
        for t in tags
        if (hasattr(t, "slug") and t.slug in library_tags) or (t in library_tags)
    ]


def filter_latest_siblings(articles):
    seen = []
    filtered_articles = []
    for article in articles:
        if article in seen:
            continue
        filtered_articles.append(article)
        seen.append(article)
        if hasattr(article, "siblings"):
            seen.extend(article.siblings)

    return filtered_articles


def filter_process_articles(articles):
    img_articles = []
    txt_articles = []

    for article in articles:
        if hasattr(article, "image") or hasattr(article, "listimage"):
            img_articles.append(article)

        else:
            txt_articles.append(article)

    # article_list.sort(key=itemgetter(1), reverse=True)

    # At this point the grouped articles/images are in the article list, in order.
    return img_articles, txt_articles


def filter_process_article_list(articles):
    """
    Process article list to:

    Bunch articles with no-images, not from different issues into
    groups of N (summary list)

    :param articles:
    :return:
    """
    article_list = []
    img_article_list = []
    txt_article_list = []

    # Non-series bundles.
    img_articles = []
    txt_articles = []
    bundle_size = 8
    text_bundle_size = 3

    for article in articles:
        if hasattr(article, "image") or hasattr(article, "listimage"):
            img_articles.append(article)
            if len(img_articles) == bundle_size:
                datetime = img_articles[0].date
                img_article_list.append(("image", datetime, img_articles))
                img_articles = []

        else:
            txt_articles.append(article)
            if len(txt_articles) == text_bundle_size:
                datetime = txt_articles[0].date
                txt_article_list.append(("text", datetime, txt_articles))
                txt_articles = []

    #  Final append.
    if img_articles:
        datetime = img_articles[0].date
        img_article_list.append(("image", datetime, img_articles))

    if txt_articles:
        datetime = txt_articles[0].date
        txt_article_list.append(("text", datetime, txt_articles))

    # Sort by date.
    img_article_list.sort(key=itemgetter(1), reverse=True)
    txt_article_list.sort(key=itemgetter(1), reverse=True)

    #  Combine, taking alternates, starting from images.
    article_list = filter(
        None, sum(zip_longest(img_article_list, txt_article_list), ())
    )

    # At this point the grouped articles/images are in the article list, in order.
    return list(article_list)


future_article = namedtuple("future_article", "date article delta_days")


def filter_planner(articles, drafts):
    """Process articles to find all future articles, sort inc. republish date,"""
    future = []
    now = datetime.datetime.now()
    now = set_date_tzinfo(now, "UTC")

    all_articles = list(articles) + list(drafts)

    for article in all_articles:
        date = article.date
        republish_date = getattr(article, "republish", None)
        if republish_date:
            date = get_date(republish_date)
            date = set_date_tzinfo(date, "UTC")
        if date > now:
            future.append((date, article))

    # Sort by dates.
    future.sort(key=itemgetter(0))

    # Calculate gaps for annotations.
    future_articles = []
    latest_date = now
    for date, article in future:
        delta_days = (date - latest_date).days
        future_articles.append(future_article(date, article, delta_days))
        latest_date = date

    return future_articles


def filter_planner_getting_old(all_articles, exclude_categories):
    """Return articles which haven't been updated in a long time"""
    articles = [
        article
        for article in all_articles
        if article.category.name not in exclude_categories
    ]

    getting_old = []
    for article in articles:
        date = article.date
        if hasattr(article, "modified"):
            date = article.modified
        getting_old.append((date, article))

    getting_old.sort(key=itemgetter(0))
    return getting_old[:10]


def filter_planner_updates(all_articles, exclude_categories):
    """Return articles which haven't been updated in a long time"""
    articles = [
        article
        for article in all_articles
        if article.category.name not in exclude_categories
    ]

    now = datetime.datetime.now()
    now = set_date_tzinfo(now, "UTC")

    # Sort by age & traffic. We log10 it to scale the age. Something with
    # 100x the hits will appear to be 2x older than something than 1 hit.
    # Repeat for landing & for hits.
    articles_old = []
    for article in articles:
        date = article.date
        if hasattr(article, "republish"):
            republish_date = getattr(article, "republish")
            date = get_date(republish_date)
            date = set_date_tzinfo(date, "UTC")
        if hasattr(article, "modified"):
            date = article.modified

        delta_days = (now - date).days

        if delta_days > 365:  # Review articles yearly?
            article.age_days = delta_days
            articles_old.append((date, article))

    articles_old.sort(key=lambda a: a[1].age_days, reverse=True)

    return articles_old[:10]


def filter_planner_seo_errors(all_articles):
    """Return articles which haven't been updated in a long time"""
    articles_to_fix = defaultdict(list)
    for article in all_articles:
        seo_errors = []
        seo_errors_score = 0

        if article.status == "draft":
            continue

        if not getattr(article, "seotitle", None):
            seo_errors.append("No SEO title")
            seo_errors_score += 10

        if getattr(article, "seotitle", None) == article.title:
            seo_errors.append("SEO title and Title should not be the same")
            seo_errors_score += 10

        if not getattr(article, "image", None):
            seo_errors.append("No image")
            seo_errors_score += 5

        if not getattr(article, "description", None):
            seo_errors.append("No meta description")
            seo_errors_score += 2

        if '<a href="' not in article.content:
            seo_errors.append("No links")
            seo_errors_score += 1

        if seo_errors:
            article.seo_errors_score = seo_errors_score
            seo_errors_str = ", ".join(seo_errors)
            article.seo_errors = f"({len(seo_errors)}) {seo_errors_str} "

            for seo_error in seo_errors:
                articles_to_fix[seo_error].append(article)

    for k in articles_to_fix:
        articles_to_fix[k].sort(key=lambda a: a.seo_errors_score, reverse=True)

    return articles_to_fix


def filter_planner_missing_library_versions(all_articles, siblings_groups):
    """Build a table showing, for articles which appear to have an associated
    library, where other libaries are missing. For example, a tutorial for PyQt5
    which has no associated PyQt6 version available.
    """
    articles_to_fix = []
    for article in all_articles:
        if not hasattr(article, "siblings"):
            continue

        article_library = getattr(article, "library", None)
        article_siblings = getattr(article, "siblings", [])

        # Find the sibling group.
        for sg in siblings_groups:
            if article_library in sg:
                possible_sibling_libraryvers = list(sg)
                break
        else:
            continue

        # Remove ourselves.
        possible_sibling_libraryvers.remove(article_library)

        n_total_sibling_libraryvers = len(possible_sibling_libraryvers)

        # Calculate based on library & siblings.
        for sibling in article_siblings:
            slibrary = getattr(sibling, "library", None)
            if slibrary in possible_sibling_libraryvers:
                # Remove them as we find them.
                possible_sibling_libraryvers.remove(slibrary)

        n_missing_sibling_libraryvers = len(possible_sibling_libraryvers)
        n_found_sibling_libraryvers = (
            n_total_sibling_libraryvers - n_missing_sibling_libraryvers
        )

        if possible_sibling_libraryvers:
            article.siblings_score = (
                n_found_sibling_libraryvers / n_total_sibling_libraryvers
            )
            article.n_siblings_vs_expected = (
                f"{n_found_sibling_libraryvers}/{n_total_sibling_libraryvers}"
            )
            articles_to_fix.append(article)

    articles_to_fix.sort(key=lambda a: a.siblings_score, reverse=True)
    return articles_to_fix[:20]


def filter_planner_sourcecode_not_in_repo(articles):
    articles_without_code = []
    for article in articles:
        # Ignore articles without code.
        if "<pre" not in article.content:
            continue
        if not hasattr(article, "sourcecode") or not article.sourcecode:
            articles_without_code.append(article)
    return articles_without_code


def filter_n_videos(course):
    return sum(getattr(a, "video", None) is not None for a in course.all_articles)


def filter_n_tutorials(course):
    return sum(getattr(a, "video", None) is None for a in course.all_articles)


def filter_total_duration(course):
    dts = (a.duration for a in course.all_articles if a.duration)
    return sum(dts, datetime.timedelta())


def filter_track_n_videos(courses):
    return sum(
        1
        for c in courses
        for a in c.all_articles
        if a.duration and getattr(a, "video", None)
    )


def filter_track_n_tutorials(courses):
    return sum(1 for c in courses for a in c.all_articles)


def filter_short_duration(dt):
    """Don't show hours on short durations."""
    s = str(dt)
    return s[2:] if s.startswith("0:") else s


def filter_course_step(article):
    if not hasattr(article, "course"):
        return None

    return 1 + article.course.all_articles.index(article)


def filter_course_length(article):
    if not hasattr(article, "course"):
        return None

    return len(article.course.all_articles)


def filter_course_pc(article):
    if not hasattr(article, "course"):
        return None

    return 100 * filter_course_step(article) / filter_course_length(article)


def filter_get_course_article_slugs(course):
    return [{"slug": a.slug} for a in course.all_articles]


def filter_curriculum(course):
    # Get articles for specific curriculum.
    articles = getattr(course, "all_articles", None)
    if articles is None:
        return

    image = getattr(course.page, "image", None)

    # category.descendents = sorted(descendents[category])
    # category.children = sorted(children[category])
    data = {
        "id": course.slug,
        "url": course.url,
        "title": course.title,
        "subtitle": getattr(course.page, "subtitle", None),
        "content": getattr(course, "content", None),
        "image": image,
        "first_child": articles[0].url if articles else None,
        "n_videos": filter_n_videos(course),
        "n_tutorials": filter_n_tutorials(course),
        "is_collapsed": getattr(course.page, "iscollapsed", None),
    }
    items = []

    for article in articles:
        items.append(
            {
                "id": article.slug,  # use the slug for unique id
                "title": article.title,
                "subtitle": getattr(article, "subtitle", None),
                "url": article.url,
                "duration": article.short_duration,
                "is_premium": getattr(article, "ispremium", None) is not None,
                "has_video": getattr(article, "video", None) is not None,
            }
        )
    data["items"] = items
    return data


def filter_courseslug(obj):
    obj = getattr(obj, "course", None)
    obj = getattr(obj, "book", None)
    obj = getattr(obj, "page", None)
    return getattr(obj, "product", None)


def filter_get_email_template(mailing_templates, article_tags):
    for tag in article_tags:
        if hasattr(tag, "name") and tag.name.lower() in mailing_templates:
            return mailing_templates.get(tag.name.lower())
    return "email/default.html"
