#! /usr/bin/env python

# -*- coding: utf-8 -*-

import random
import flask
import poobrains
import markdown
import poobrains_markdown

app = poobrains.app

# markdown extensions

class SourceExtension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        app.debugger.set_trace()

# content types

class SourceOrganization(poobrains.tagging.Taggable):
    parent = poobrains.storage.fields.ForeignKeyField('self', null=True)
    trustworthiness = poobrains.storage.fields.IntegerField()
    url = poobrains.storage.fields.CharField(null=True) # TODO: Add an URLField to poobrains.


class SourceAuthor(poobrains.tagging.Taggable):

    organization = poobrains.storage.fields.ForeignKeyField(SourceOrganization, null=True)
    trustworthiness = poobrains.storage.fields.IntegerField()
    url = poobrains.storage.fields.CharField(null=True) # TODO: Add an URLField to poobrains.


class Source(poobrains.tagging.Taggable):

    type = poobrains.storage.fields.CharField()
    author = poobrains.storage.fields.ForeignKeyField(SourceAuthor)
    url = poobrains.storage.fields.CharField(null=True) # TODO: Add an URLField to poobrains.
    description = poobrains_markdown.MarkdownField()


class Article(poobrains.tagging.Taggable):

    title = poobrains.storage.fields.CharField()
    text = poobrains_markdown.MarkdownField()


class ArticleSource(poobrains.storage.Storable):

    article = poobrains.storage.fields.ForeignKeyField(Article)
    source = poobrains.storage.fields.ForeignKeyField(Source)


class CuratedContent(poobrains.tagging.Taggable):

    title = poobrains.storage.fields.CharField()
    description = poobrains_markdown.MarkdownField()
    url = poobrains.storage.fields.CharField(null=True) # TODO: Add an URLField to poobrains.


poobrains_markdown.parser.registerExtensions([SourceExtension()], [])

DOGE = {
    'prefix': [
        'wow',
        'such',
        'many',
        'more',
        'so',
        'all your base',
        'lol',
        'very',
        'omg'
    ],

    'thing': [
        'wow',
        'doge',
        'shibe',
        '1337 h4xx0rz',
        'internet',
        'pretty',
        'computer',
        'free software',
        'website',
        'content',
        'python',
        'flask',
        'poobrains',
        'are belong to us',
        'NOT PHP'
    ],

    'thing_tls': [
        'transport layer security',
        'X.509',
        'certificate'
    ],

    'suffix': [
        'wow',
        'pls',
        'mystery',
        'anarchy',
        'bees'
    ]
}

@app.after_request
def mkdoge(response):

    items = [
        DOGE['prefix'],
        DOGE['thing'] + DOGE['thing_tls'] if flask.request.is_secure else DOGE['thing'],
        DOGE['suffix']
    ]

    doge = []

    for l in items:
        doge.append(l[random.randint(0, len(l) - 1)])

    response.headers['X-Doge'] = ' '.join(doge)
    return response


if __name__ == '__main__':
   app.run() 
