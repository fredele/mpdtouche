#!/usr/bin/python
from xml.sax import make_parser, handler

class XspfParser(handler.ContentHandler):
    def __init__(self):
        handler.ContentHandler.__init__(self)
        self._content = ""
        self.title = ""
        self.path = ""
        self.tracklist= []

    def parseFile(self,filename):
        parser = make_parser()
        parser.setContentHandler(self)
        parser.parse(filename)

    def startDocument(self):
        pass

    def startElement(self, name, attrs):
        self.path += "/%s" % name

        if self.path == '/playlist/trackList/track':
            self.track = dict()

    def endElement(self, name):
        if self.path == '/playlist/trackList/track':
            self.tracklist.append(self.track)

        offset = self.path.rfind("/")
        if offset >= 0:
            self.path = self.path[0:offset]

    def characters(self, content):
        if self.path == '/playlist/trackList/track/title':
            self.track['title'] = content
        if self.path == '/playlist/trackList/track/location':
            self.track['location'] = content
        if self.path == '/playlist/trackList/track/image':
            self.track['image'] = content
        if self.path == '/playlist/title':
            self.title = content

    def getResult(self):
        res = dict()
        res['title'] = self.title
        res['tracklist'] = self.tracklist
        return res

