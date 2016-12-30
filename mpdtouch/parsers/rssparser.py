#!/usr/bin/python
# -*- coding: utf-8 -*-

#https://docs.python.org/2/library/xml.sax.handler.html

from xml.sax import make_parser, handler

class RssParser(handler.ContentHandler):
    def __init__(self):
        handler.ContentHandler.__init__(self)
        self.path = ""
        self.itemlist= []
        self.res = dict()


    def parseFile(self,filename):
        parser = make_parser()
        parser.setContentHandler(self)
        parser.parse(filename)

    def startDocument(self):
        pass

    def startElement(self, name, attrs):
        self.path += "/%s" % name

        if self.path == '/rss/channel/item':
            self.item = dict()
        if self.path == '/rss/channel/image':
            self.image = dict()
        if self.path == '/rss/channel/item/enclosure':
            self.item['url'] = attrs.get('url', '')

    def endElement(self, name):
        if self.path == '/rss/channel/item':
            self.item['image'] = self.image
            self.itemlist.append(self.item)

        offset = self.path.rfind("/")
        if offset >= 0:
            self.path = self.path[0:offset]

    def characters(self, content):
        if self.path == '/rss/channel/title':
            self.res['title'] = content
        if self.path == '/rss/channel/link':
            self.res['link'] = content
        if self.path == '/rss/channel/description':
            self.res['description'] = content
        if self.path == '/rss/channel/language':
            self.res['language'] = content
        if self.path == '/rss/channel/copyright':
            self.res['copyright'] = content
        if self.path == '/rss/channel/lastBuildDate':
            self.res['lastBuildDate'] = content
        if self.path == '/rss/channel/generator':
            self.res['generator'] = content
        if self.path == '/rss/channel/':
            self.res['lastBuildDate'] = content

        #image
        if self.path == '/rss/channel/image/url':
            self.image['url'] = content
        if self.path == '/rss/channel/image/title':
            self.image['title'] = content
        if self.path == '/rss/channel/image/link':
            self.image['link'] = content

        #item
        if self.path == '/rss/channel/item/title':
            self.item['title'] = content
        if self.path == '/rss/channel/item/link':
            self.item['link'] = content
        if self.path == '/rss/channel/item/description':
            self.item['description'] = content
        if self.path == '/rss/channel/item/author':
            self.item['author'] = content
        if self.path == '/rss/channel/item/category':
            self.item['category'] = content
        if self.path == '/rss/channel/item/enclosure':
            self.item['enclosure'] = content
            print("enclosure" + content)
        if self.path == '/rss/channel/item/guid':
            self.item['guid'] = content
        if self.path == '/rss/channel/item/pubDate':
            self.item['pubDate'] = content
        if self.path == '/rss/channel/item/podcastRF:businessReference':
            self.item['podcastRF_businessReference'] = content
        if self.path == '/rss/channel/item/podcastRF:magnetothequeID':
            self.item['podcastRF_magnetothequeID'] = content
        if self.path == '/rss/channel/item/podcastRF:stepID':
            self.item['podcastRF_stepID'] = content

    def getResult(self):

        self.res['items'] = self.itemlist
        return self.res

