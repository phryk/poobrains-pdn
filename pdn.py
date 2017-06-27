#! /usr/bin/env python

# -*- coding: utf-8 -*-

import math
import os
import random
import datetime
import requests
import bs4
import markdown
import flask
import poobrains

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageSequence

app = poobrains.app

class MemePattern(markdown.inlinepatterns.Pattern):

    name = None

    def __init__(self, pattern, name, markdown_instance=None):

        super(MemePattern, self).__init__(pattern, markdown_instance=markdown_instance)
        self.name = name

    def handleMatch(self, match):

        if match:

            caption = match.group(2)
            if not MemeWhiteList.select().where(MemeWhiteList.caption == caption).count():
                cache_entry = MemeWhiteList()
                cache_entry.caption = caption
                cache_entry.save()

            element = markdown.util.etree.Element('img')
            element.set('src', "/meme/%s/%s" % (self.name, caption))
            element.set('alt', caption)
            return element

        return super(MemePattern, self).handleMatch(match)


class Memextension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        for name in app.config['MEMES']:
            md.inlinePatterns.add(name, MemePattern('<%s>(.*?)</%s>' % (name, name), name), '<reference')

poobrains.md.md.registerExtensions([Memextension()], [])

@app.expose('/meme/<string:name>/<string:caption>')
class Mememage(poobrains.auth.Protected):
    
    def view(self, mode='full', name=None, caption=None):

        if name in app.config['MEMES'] and MemeWhiteList.select().where(MemeWhiteList.caption == caption).count():

            # TODO: is input sanitation still needed?
            if ':' in caption and len(caption.split(':')) == 2:
                upper, lower = caption.split(':')
            else:
                upper = None
                lower = caption

            filename = os.path.join(app.root_path, app.config['MEMES'][name])
            extension = filename.split('.')[-1]

            template = Image.open(filename)
            font = ImageFont.truetype(os.path.join(app.root_path, 'LeagueGothic-Regular.otf'), 80)

            resized = (750, int(template.height * (750.0 / template.width)))

            if upper:
                upper_size = font.getsize(upper)
                upper_x = int(round(resized[0] / 2.0 - upper_size[0] / 2.0))
                upper_y = 0

            if lower:
                lower_size = font.getsize(lower)
                lower_x = int(round(resized[0] / 2.0 - lower_size[0] / 2.0))
                lower_y = resized[1] - lower_size[1] - 10 # last int is margin from bottom


            if extension == 'gif':

                frames = []
                for frame in ImageSequence.Iterator(template):

                    frame = frame.convert('RGBA').resize(resized, Image.BICUBIC)
                    text_layer = Image.new('RGBA', frame.size, (0,0,0,0))
                    text_draw = ImageDraw.Draw(text_layer)

                    if upper:
                        outlined_text(text_draw, upper, upper_x, upper_y, font=font)

                    if lower:
                        outlined_text(text_draw, lower, lower_x, lower_y, font=font)

                    frames.append(Image.alpha_composite(frame, text_layer))

                meme = frames.pop(0).convert('P')

                if template.info.has_key('duration'):
                    meme.info['duration'] = template.info['duration']

                if template.info.has_key('loop'):
                    meme.info['loop'] = template.info['loop']

                out = BytesIO()
                meme.save(out, save_all=True, append_images=frames, format='GIF')


                r = flask.Response(
                    out.getvalue(),
                    mimetype='image/gif'
                )

                r.cache_control.public = True
                r.cache_control.max_age = 604800

                return r


            else:

                meme = template.convert('RGBA').resize(resized, Image.BICUBIC)

                text_layer = Image.new('RGBA', resized, (0,0,0,0))
                text_draw = ImageDraw.Draw(text_layer)

                if upper:
                    outlined_text(text_draw, upper, upper_x, upper_y, font=font)

                if lower:
                    outlined_text(text_draw, lower, lower_x, lower_y, font=font)

                meme = Image.alpha_composite(meme, text_layer)

                out = BytesIO()
                meme.save(out, format='PNG')
                
                #img.save(filename='memes/foo.png')
                r = flask.Response(
                    out.getvalue(),
                    mimetype='image/png'
                )
                r.cache_control.public = True
                r.cache_control.max_age = 604800

                return r


        raise poobrains.auth.AccessDenied()


def outlined_text(drawing, text, x=0, y=0, font=None):
    drawing.text((x-1, y-1), text, font=font, fill=(0,0,0,255))
    drawing.text((x-1, y+1), text, font=font, fill=(0,0,0,255))
    drawing.text((x+1, y+1), text, font=font, fill=(0,0,0,255))
    drawing.text((x+1, y-1), text, font=font, fill=(0,0,0,255))
    drawing.text((x, y), text, font=font, fill=(255,255,255,255))


# content types

class MemeWhiteList(poobrains.storage.Model):

    # TODO: add functionality to remove references to deleted/removed storable instances

    caption = poobrains.storage.fields.CharField()


class ScoredLink(poobrains.auth.Administerable):

    form_blacklist = ['id', 'external_site_count', 'updated']

    link = poobrains.storage.fields.CharField(null=True, unique=True) # TODO: Add an URLField to poobrains.
    external_site_count = poobrains.storage.fields.IntegerField(null=True)
    updated = poobrains.storage.fields.DateTimeField(null=False, default=datetime.datetime.now)

    mean = None
    median = None
    set_size = None


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

    
    def prepared(self):

        super(ScoredLink, self).prepared()
        self.set_size = self.__class__.select().count()

        external_site_counts = []
        for row in self.__class__.select(self.__class__.external_site_count).order_by(self.__class__.external_site_count).dicts():
            external_site_counts.append(row['external_site_count'])

        self.mean = sum(external_site_counts) / float(len(external_site_counts))

        median_idx = int(math.floor(len(external_site_counts) / 2.0))
        if len(external_site_counts) % 2 == 0:

            a = external_site_counts[median_idx -1]
            b = external_site_counts[median_idx]

            self.median = a + b / 2.0
        else:
            self.median = external_site_counts[median_idx]



    @property
    def name(self):
        return self.link


@app.expose('/source/organization/', mode='full')
class SourceOrganization(poobrains.commenting.Commentable):

    parent = poobrains.storage.fields.ForeignKeyField('self', null=True)
    title = poobrains.storage.fields.CharField()
    link = poobrains.storage.fields.ForeignKeyField(ScoredLink, null=True)
    description = poobrains.md.MarkdownField(null=True)


@app.expose('/source/author/', mode='full')
class SourceAuthor(poobrains.commenting.Commentable):

    title = poobrains.storage.fields.CharField()
    link = poobrains.storage.fields.ForeignKeyField(ScoredLink, null=True)
    description = poobrains.md.MarkdownField(null=True)


class SourceOrganizationAuthor(poobrains.storage.Model):

    organization = poobrains.storage.fields.ForeignKeyField(SourceOrganization)
    author = poobrains.storage.fields.ForeignKeyField(SourceAuthor)


@app.expose('/source/', mode='full')
class Source(poobrains.commenting.Commentable):

    title = poobrains.storage.fields.CharField()
    type = poobrains.storage.fields.CharField() # TODO: We need some logic to make this useful. Also, build enum type compatible to sqlite+postgres?
    author = poobrains.storage.fields.ForeignKeyField(SourceOrganizationAuthor)
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
