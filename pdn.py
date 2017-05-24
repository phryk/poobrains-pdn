#! /usr/bin/env python

# -*- coding: utf-8 -*-

import os
import random
import datetime
import requests
import bs4
import markdown
import flask
import poobrains

from wand import image, drawing, color

app = poobrains.app

class Meme(markdown.inlinepatterns.Pattern):

    name = None

    def __init__(self, pattern, name, markdown_instance=None):

        super(Meme, self).__init__(pattern, markdown_instance=markdown_instance)
        self.name = name

    def handleMatch(self, match):

        if match:

            Memesez = match.group(2)
            element = markdown.util.etree.Element('img')
            element.set('src', "/meme/%s/%s" % (self.name, Memesez))
            element.set('alt', Memesez)
            return element

        return super(Meme, self).handleMatch(match)


class Memextension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        for name in app.config['MEMES']:
            md.inlinePatterns.add(name, Meme('<%s>(.*?)</%s>' % (name, name), name), '<reference')

poobrains.md.md.registerExtensions([Memextension()], [])

@app.expose('/meme/<string:name>/<string:text>')
class Mememage(poobrains.auth.Protected):
    
    def view(self, mode='full', name=None, text=None):

        if name in app.config['MEMES']:

            filename = app.config['MEMES'][name]
            extension = filename.split('.')[-1]

            with image.Image(filename=filename) as template:

                #template.transform(resize='750')
                height = int(template.height * (750. / template.width))
                template.resize(width=750, height=height)
                img = template.clone()
                #img.transform(resize='750')

                # TODO: is input sanitation still needed?
                if ':' in text:
                    upper, lower = text.split(':')
                else:
                    upper = None
                    lower = text

                if extension == 'gif':

                    with image.Image(width=img.width, height=img.height) as gif:


                        for frame in img.sequence:

                            with frame.clone() as frame_modded:

                                index = frame.index
                                delay = frame.delay
                                with drawing.Drawing() as t:
                                    t.stroke_color = color.Color('#000000')
                                    t.fill_color = color.Color('#ffffff')
                                    t.font = os.path.join(poobrains.app.root_path, 'LeagueGothic-Regular.otf')
                                    t.font_size = 60
                                    if upper:
                                        t.gravity = 'north'
                                        t.text(0,0, upper)
                                    if lower:
                                        t.gravity = 'south'
                                        t.text(0,0, lower)
                                    t(frame_modded)

                                if index == 0:
                                    gif.sequence[0] = frame_modded
                                else:
                                    gif.sequence.append(frame_modded)
                                gif.sequence[index].delay = delay


                        #gif.save(filename='memes/foo.gif')
                        r = flask.Response(
                            gif.make_blob('gif'),
                            mimetype='image/gif'
                        )

                        r.cache_control.public = True
                        r.cache_control.max_age = 604800

                        return r

                else:

                    t = drawing.Drawing()
                    t.stroke_color = color.Color('#000000')
                    t.fill_color = color.Color('#ffffff')
                    t.font = os.path.join(poobrains.app.root_path, 'LeagueGothic-Regular.otf')
                    t.font_size = 60

                    if upper:
                        t.gravity = 'north'
                        t.text(0,0, upper)
                    if lower:
                        t.gravity = 'south'
                        t.text(0,0, lower)
                    t(img)

                #img.save(filename='memes/foo.png')
                r = flask.Response(
                    img.make_blob('png'),
                    mimetype='image/png'
                )
                r.cache_control.public = True
                r.cache_control.max_age = 604800

                return r


        raise poobrains.auth.AccessDenied()

# content types

class ScoredLink(poobrains.auth.Administerable):

    form_blacklist = ['id', 'external_site_count', 'updated']

    link = poobrains.storage.fields.CharField(null=True, unique=True) # TODO: Add an URLField to poobrains.
    external_site_count = poobrains.storage.fields.IntegerField(null=True)
    updated = poobrains.storage.fields.DateTimeField(null=False, default=datetime.datetime.now)


    def scrape_external_site_count(self):

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
                    if isinstance(attribute_value, basestring) and attribute_value.find('://') >= 0:
                        attribute_domain = attribute_value.split('/')[2]
                        if attribute_domain != link_domain:
                            external_site_count += 1

        return external_site_count

    
    def save(self, *args, **kwargs):

        try:
            self.external_site_count = self.scrape_external_site_count()
            self.updated = datetime.datetime.now()
        except Exception as e: # Match all errors so failures here don't interfere with normal operations
            poobrains.app.logger.error('Could not scrape external site count for URL: %s' % self.link)
            poobrains.app.logger.debug('Problem when scraping external site count: %s: %s' % (str(type(e)), e.message))

        return super(ScoredLink, self).save(*args, **kwargs)


@app.expose('/source/organization/', mode='full')
class SourceOrganization(poobrains.commenting.Commentable):

    parent = poobrains.storage.fields.ForeignKeyField('self', null=True)
    title = poobrains.storage.fields.CharField()
    link = poobrains.storage.fields.ForeignKeyField(ScoredLink, null=True)


@app.expose('/source/author/', mode='full')
class SourceAuthor(poobrains.commenting.Commentable):

    title = poobrains.storage.fields.CharField()
    organization = poobrains.storage.fields.ForeignKeyField(SourceOrganization, null=True)
    link = poobrains.storage.fields.ForeignKeyField(ScoredLink, null=True)


@app.expose('/source/', mode='full')
class Source(poobrains.commenting.Commentable):

    title = poobrains.storage.fields.CharField()
    type = poobrains.storage.fields.CharField()
    author = poobrains.storage.fields.ForeignKeyField(SourceAuthor)
    link = poobrains.storage.fields.ForeignKeyField(ScoredLink, null=True)
    description = poobrains.md.MarkdownField()


@app.expose('/article/', mode='full')
class Article(poobrains.commenting.Commentable):

    title = poobrains.storage.fields.CharField()
    text = poobrains.md.MarkdownField()


@app.expose('/projects/', mode='full')
class Project(poobrains.commenting.Commentable):

    title = poobrains.storage.fields.CharField()
    text = poobrains.md.MarkdownField()
    link = poobrains.storage.fields.CharField()


@app.expose('/curated/', mode='full')
class CuratedContent(poobrains.commenting.Commentable):

    title = poobrains.storage.fields.CharField()
    description = poobrains.md.MarkdownField()
    link = poobrains.storage.fields.ForeignKeyField(ScoredLink, null=True)


@app.site.box('menu_main')
def menu_main():
   
    menu = poobrains.rendering.Menu('main')

    try:
        menu.append(Article.url('teaser'), 'Articles')
    except poobrains.auth.AccessDenied:
        pass

    try:
        menu.append(Project.url('teaser'), 'Projects')
    except poobrains.auth.AccessDenied:
        pass

    try:
        CuratedContent.url('teaser')
        menu.append(CuratedContent.url('teaser'), 'Curated content')
    except poobrains.auth.AccessDenied:
        pass

    try:
        menu.append(Source.url('teaser'), 'Sources')
    except poobrains.auth.AccessDenied:
        pass

    return menu


DOGE = {
    'prefix': [
        'wow',
        'such',
        'many',
        'more',
        'so',
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
