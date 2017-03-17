#! /usr/bin/env python

# -*- coding: utf-8 -*-

import random
import requests
import bs4
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

class ScoredLink(poobrains.auth.Administerable):

    form_blacklist = ['id', 'external_site_count']

    link = poobrains.storage.fields.CharField(null=True, unique=True) # TODO: Add an URLField to poobrains.
    external_site_count = poobrains.storage.fields.IntegerField(null=True)


    def scrape_external_site_count(self):
        app.debugger.set_trace()
        external_site_count = 0

        if self.link:

            link_domain = self.link.split('/')[2]

            html = requests.get(self.link).text
            dom = bs4.BeautifulSoup(html)

            scored_elements = {
                'script': 'src',
                'link': 'src',
                'img': 'src',
                'object': 'data'
            }

            for tag, attribute in scored_elements.iteritems():
                for element in dom.find_all(tag):
                    attribute_value = element.get(attribute)
                    if isinstance(attribute_value, str) and attribute_value.find('://') >= 0:
                        attribute_domain = attribute_value.split('/')[2]
                        if attribute_domain != link_domain:
                            external_site_count += 1

        return external_site_count

    
    def save(self, *args, **kwargs):

        try:
            self.external_site_count = self.scrape_external_site_count()
        except Exception as e: # Match all errors so failures here don't interfere with normal operations
            poobrains.app.logger.error('Could not scrape external site count for URL: %s' % link)
            poobrains.app.logger.debug('Problem when scraping external site count: %s: %s' % (str(type(e)), e.message))

        return super(ScoredLink, self).save(*args, **kwargs)


@app.expose('/source/organization/', mode='full')
class SourceOrganization(poobrains.commenting.Commentable):

    parent = poobrains.storage.fields.ForeignKeyField('self', null=True)
    trustworthiness = poobrains.storage.fields.IntegerField()
    link = poobrains.storage.fields.ForeignKeyField(ScoredLink, null=True)


@app.expose('/source/author/', mode='full')
class SourceAuthor(poobrains.commenting.Commentable):

    organization = poobrains.storage.fields.ForeignKeyField(SourceOrganization, null=True)
    trustworthiness = poobrains.storage.fields.IntegerField()
    link = poobrains.storage.fields.ForeignKeyField(ScoredLink, null=True)


@app.expose('/source/', mode='full')
class Source(poobrains.commenting.Commentable):

    type = poobrains.storage.fields.CharField()
    author = poobrains.storage.fields.ForeignKeyField(SourceAuthor)
    link = poobrains.storage.fields.ForeignKeyField(ScoredLink, null=True)
    description = poobrains_markdown.MarkdownField()


@app.expose('/article/', mode='full')
class Article(poobrains.commenting.Commentable):

    title = poobrains.storage.fields.CharField()
    text = poobrains_markdown.MarkdownField()


@app.expose('/curated/', mode='full')
class CuratedContent(poobrains.commenting.Commentable):

    title = poobrains.storage.fields.CharField()
    description = poobrains_markdown.MarkdownField()
    link = poobrains.storage.fields.ForeignKeyField(ScoredLink, null=True)


@app.site.box('menu_main')
def menu_main():
   
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
