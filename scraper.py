#!/usr/bin/env python3

# scraper.py

from bs4 import BeautifulSoup
from pprint import pprint
from urllib.parse import urlsplit, urlunsplit, urljoin, SplitResult
import os
import re
import requests
import sys
import urltools


bad_extensions = tuple([".zip", ".pdf", ".do", ".pl"])


def _find_addys(text):
    addy_regex = re.compile("(?:mailto:)?([-+.\w]+@[-+.\w]+\.[a-z]+)", re.I)
    return re.findall(addy_regex, text)


def _urlsplit(arg):
    parts = urlsplit(arg, scheme="http", allow_fragments=True)
    # dump the query and the fragment
    return SplitResult(parts.scheme, parts.netloc, parts.path, "", "")


def _sanitize(url):
    ret = url
    ret = _urlsplit(ret)
    ret = urlunsplit(ret)
    ret = urltools.normalize(ret)
    return ret


def _links(url, content):

    soup = BeautifulSoup(content, "lxml")

    ret = set(a.attrs["href"] for a in soup.find_all('a') if "href" in a.attrs)
    ret = set(filter(lambda e: e.startswith("http"), ret))
    ret = set(map(_urlsplit, ret))

    def pred(e):
        return e.hostname and e.hostname.endswith(_urlsplit(url).hostname)

    ret = set(filter(pred, ret))
    ret = set(map(urlunsplit, ret))
    ret = set(map(urltools.normalize, ret))
    ret = set(urljoin(url, link) for link in ret)
    ret = set(filter(lambda e: not e.endswith(bad_extensions), ret))
    ret = set(filter(lambda e: not re.search(r'pdf', e, re.I), ret))
    # print("len(ret) == ",len(ret))
    # pprint(ret)
    return ret


def _scrape(urls):
    emails = set()
    urls_new = set(map(_sanitize, urls))
    urls_old = set()
    while urls_new:
        print("len(emails)   == ", len(emails))
        print("len(urls_new) == ", len(urls_new))
        print("len(urls_old) == ", len(urls_old))
        # print("urls_new == ", urls_new)
        url = urls_new.pop()
        urls_old.add(url)
        # print("URLS_OLD:")
        # pprint(urls_old)
        # print("urls_old == ", urls_old)
        print("Processing \"%s\"" % url)
        try:
            response = requests.get(url)
        except(requests.exception.MissingSchema,
               requests.exception.TooManyRedirects,
               requests.exception.ConnectionError):
            print("Error on %s" % url)
            continue

        emails.update(set(_find_addys(response.text)))

        urls_new.update(_links(url, response.text) - urls_old)

    return emails


def main():
    emails = _scrape(sys.argv[1:])
    print(emails)


if '__main__' == __name__:
    main()
    exit(0)
