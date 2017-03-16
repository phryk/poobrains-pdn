#! /usr/bin/env python

# -*- coding: utf-8 -*-

import random
import flask
import poobrains
import markdown
import poobrains_markdown
import md # markdown stuff specific to this site

app = poobrains.app


def magic_markdown_loader(storable, handle):

    storables = poobrains.storage.Storable.children_keyed()
    for k, v in storables.iteritems():
        storables[k.lower()] = v # Allows us to use the correct case, or just lowercase

    cls = storables[storable]
    return cls.load(handle)

poobrains_markdown.md.references.set_loader(magic_markdown_loader)

# content types

@app.expose('/source/organization/', mode='teaser')
class SourceOrganization(poobrains.commenting.Commentable):
    parent = poobrains.storage.fields.ForeignKeyField('self', null=True)
    trustworthiness = poobrains.storage.fields.IntegerField()
    link = poobrains.storage.fields.CharField(null=True) # TODO: Add an URLField to poobrains.


@app.expose('/source/author/', mode='teaser')
class SourceAuthor(poobrains.commenting.Commentable):

    organization = poobrains.storage.fields.ForeignKeyField(SourceOrganization, null=True)
    trustworthiness = poobrains.storage.fields.IntegerField()
    link = poobrains.storage.fields.CharField(null=True) # TODO: Add an URLField to poobrains.


@app.expose('/source/', mode='teaser')
class Source(poobrains.commenting.Commentable):

    type = poobrains.storage.fields.CharField()
    author = poobrains.storage.fields.ForeignKeyField(SourceAuthor)
    link = poobrains.storage.fields.CharField(null=True) # TODO: Add an URLField to poobrains.
    description = poobrains_markdown.MarkdownField()


@app.expose('/article/', mode='teaser')
class Article(poobrains.commenting.Commentable):

    title = poobrains.storage.fields.CharField()
    text = poobrains_markdown.MarkdownField()


@app.expose('/curated/', mode='teaser')
class CuratedContent(poobrains.commenting.Commentable):

    title = poobrains.storage.fields.CharField()
    description = poobrains_markdown.MarkdownField()
    link = poobrains.storage.fields.CharField(null=True) # TODO: Add an URLField to poobrains.


@app.site.box('menu_main')
def menu_main():
   
    app.debugger.set_trace()
    menu = poobrains.rendering.Menu('main')

    try:
        menu.append(Article.url('teaser'), 'Articles')
    except poobrains.auth.PermissionDenied:
        pass

    try:
        CuratedContent.url('teaser')
        menu.append(CuratedContent.url('teaser'), 'Curated content')
    except poobrains.auth.PermissionDenied:
        pass

    try:
        menu.append(Source.url('teaser'), 'Sources')
    except poobrains.auth.PermissionDenied:
        pass

    return menu


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
