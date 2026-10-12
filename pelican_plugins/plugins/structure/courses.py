# -*- coding: utf-8 -*-
"""
This plugin extends the original collection plugin
by FELD Boris <lothiraldan@gmail.com>

Copyright (c) Leonardo Giordani <giordani.leonardo@gmail.com>

Joins articles in a collection and provides variables to
manage the collection in the template.
"""

import logging
from collections import defaultdict

from pelican import signals
from pelican.contents import Page
from pelican.utils import slugify
from six import text_type

from .utils import make_pages


class Course(Page):
    default_template = "course"


class CourseIndex(Page):
    default_template = "course_index"


def get_course_pages(generator):
    settings = generator.settings
    readers = generator.readers
    context = generator.context

    course_path = settings.get("COURSE_PAGE_PATH", "courses")
    return make_pages(Course, readers, context, course_path)


def create_course(generator, course_page):
    # Create a course page, holding the articles to display.
    course = Course(course_page.content, settings=generator.settings)
    course.page = course_page

    for attr in [
        "title",
        "subtitle",
        "date",
        "author",
        "template",
        "slug",
        "all_articles",
        "parts",
        "image",
        "featured",
    ]:
        v = getattr(course_page, attr, None)
        if v is not None:
            setattr(course, attr, v)

    course.first_article = course.all_articles[0] if course.all_articles else None
    course.last_article = course.all_articles[-1] if course.all_articles else None

    for n, article in enumerate(course.all_articles):
        article.course = course

        if n > 0:
            article.course_previous = course.all_articles[n - 1]
        if n < len(course.all_articles) - 1:
            article.course_next = course.all_articles[n + 1]

    return course


def process_courses(generator):
    course_pages = get_course_pages(generator)

    # Collect required article slugs, so we can find the course/collections in one pass.
    article_slugs = [slug for sp in course_pages for slug in getattr(sp, "parts", [])]
    course_map = {
        a.slug: a
        for a in generator.articles
        if a.slug in article_slugs and a.status == "published"
    }

    # Cycle through the course, lookup articles, collection objects by slug.
    courses = []
    for course_page in course_pages:

        all_articles = []
        for s in course_page.parts:
            if not s:
                continue  # Skip empty entries.

            if s not in course_map:
                print(f"{s} missing in course {course_page.slug}")
                continue

            # Iterate the entries in this course, looking up the articles by slug.
            all_articles.append(course_map[s])

        course_page.all_articles = all_articles
        course_page.parts = all_articles  # Parts contains the same list//legacy.

        course = create_course(generator, course_page)
        courses.append(course)

    generator.courses = courses
    generator._update_context(["courses"])


def write_courses(generator, writer):
    # Write individual course pages, if not prevented.
    for course in generator.courses:
        logging.info("Writing course page %s (%s)", course.title, course.slug)
        signals.page_generator_write_page.send(generator, content=course)
        writer.write_file(
            course.save_as,
            generator.get_template(course.template),
            generator.context,
            course=course,
            page=course.page,
            override_output=hasattr(course, "override_save_as"),
            relative_urls=generator.settings["RELATIVE_URLS"],
        )


def write_index(generator, writer):
    #  Write the collection index, under collection/index.html.
    index = CourseIndex("", settings=generator.settings)
    index.title = generator.settings.get("COURSE_INDEX_TITLE", "Courses")
    index.slug = "index"
    index.courses = generator.courses

    writer.write_file(
        index.save_as,
        generator.get_template(index.template),
        generator.context,
        course_index=index,
        override_output=hasattr(index, "override_save_as"),
        relative_urls=generator.settings["RELATIVE_URLS"],
    )
