# -*- coding: utf-8 -*-
"""
Calculation duration, as timedelta (using provided minutes, or using readtime)
"""

from pelican import signals


import readtime
import datetime

def short_duration(dt):
    """ Don't show hours on short durations."""
    s = str(dt)
    return s[2:] if s.startswith('0:') else s

def calculate_readtime(generator):

    for article in generator.articles:
        minutes = article.metadata.get('duration')
        if minutes:
            article.duration = datetime.timedelta(minutes=int(minutes))
            article.short_duration = short_duration(article.duration)

        else:
            article.duration = readtime.of_html(article._content).delta
            article.short_duration = short_duration(article.duration)

def register():
    signals.article_generator_finalized.connect(calculate_readtime)
