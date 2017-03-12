#! /usr/bin/env python

# -*- coding: utf-8 -*-

import poobrains
import markdown
import poobrains_markdown

app = poobrains.app

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


if __name__ == '__main__':
   app.run() 
