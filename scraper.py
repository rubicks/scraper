#!/usr/bin/env python3

# scraper.py


from bs4 import BeautifulSoup
import os,re,requests,sys,urltools
from pprint import pprint
from urllib.parse import urlsplit,urlunsplit,urljoin,SplitResult


urls_old = set()

urls_new = set()

emails = set()

addy_regex = re.compile("(?:mailto:)?([-+.\w]+@[-+.\w]+\.[a-z]+)",re.I)

bad_extensions = tuple([".zip",".pdf",".do",".pl"])


def _find_addys(text):
    #return re.findall(r"(?:mailto:)?([-+.\w]+@[-+.\w]+\.[a-z]+)",text,re.I)
    return re.findall(addy_regex,text)


def _urlsplit(arg):
    parts = urlsplit( arg, scheme="http", allow_fragments=True )
    # dump the query and the fragment
    return SplitResult( parts.scheme, parts.netloc, parts.path, "", "" )


def _sanitize(url):
    ret = url
    ret = _urlsplit( ret )
    ret = urlunsplit( ret )
    ret = urltools.normalize( ret )
    return ret


def _links(url,content):

    # print("making soup")
    soup = BeautifulSoup(content,"lxml")

    # print("\ngetting links")
    links = set(a.attrs["href"] for a in soup.find_all('a') if "href" in a.attrs)
    links = set(filter(lambda e: e.startswith("http"),links))
    links = set(map(_urlsplit,links))
    links = set(filter(lambda e: e.hostname.endswith(_urlsplit(url).hostname), links))
    links = set(map(urlunsplit,links))
    links = set(map(urltools.normalize,links))
    links = set(urljoin(url,link) for link in links)
    links = set(filter(lambda e: not e.endswith(bad_extensions),links))
    links = set(filter(lambda e: not re.search(r'pdf',e,re.I),links))
    # print("len(links) == ",len(links))
    # pprint(links)
    return links


def main():
    print("main()")
    urls_new = set( map( _sanitize, sys.argv[:0:-1] ) )
    while urls_new:
        print("len(emails)   == ",len(emails))
        print("len(urls_new) == ",len(urls_new))
        print("len(urls_old) == ",len(urls_old))
        # print("urls_new == ",urls_new)
        url = urls_new.pop()
        urls_old.add(url)
        # print("URLS_OLD:")
        # pprint(urls_old)
        # print("urls_old == ",urls_old)
        print("Processing \"%s\"" % url)
        try:
            response = requests.get(url)
        except(requests.exception.MissingSchema,
               requests.exception.TooManyRedirects,
               requests.exception.ConnectionError):
            print("Error on %s" % url)
            continue
        
        emails.update( set( _find_addys( response.text ) ) )

        urls_new.update( _links( url, response.text ) - urls_old )

    return 0
        

if '__main__' == __name__:
    main()
    print(emails)
    exit(0)



