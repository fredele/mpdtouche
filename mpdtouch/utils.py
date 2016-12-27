#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

def TimeToHMS(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if seconds < 3600:
        return "%02d:%02d" % ( m, s)
    else:
        return "%d:%02d:%02d" % (h, m, s)

def format_to_str(input):
    if isinstance(input, basestring):
        return input.encode('UTF-8')

    elif isinstance(input, list):
        s = ", ".join(input)
        return s.encode('UTF-8')
    else:
        pass


def url_exists(path):
    r = requests.head(path)
    return r.status_code == requests.codes.ok


