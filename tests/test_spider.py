import sys
sys.path.append("src/cewler")  # noqa (to avoid autopep8 organizing imports)
from cewler.spider import *


def test_OnlyExactSameDomainSpiderMiddleware():
    url = "http://example.com"
    spider = CewlerSpider(Console(), url, file_words=None)
    mw = OnlyExactSameDomainSpiderMiddleware(stats=None)
    pattern = mw.get_host_regex(spider)
    assert pattern.match("example.com") != None
    assert pattern.match("roysolberg.com") == None
    assert pattern.match("2example.com") == None
    assert pattern.match("subdomain.example.com") == None
    assert pattern.match("sub.subdomain.example.com") == None

    url = "https://subdomain.example.com"
    spider = CewlerSpider(Console(), url, file_words=None)
    mw = OnlyExactSameDomainSpiderMiddleware(stats=None)
    pattern = mw.get_host_regex(spider)
    assert pattern.match("example.com") == None
    assert pattern.match("roysolberg.com") == None
    assert pattern.match("2example.com") == None
    assert pattern.match("subdomain.example.com") != None
    assert pattern.match("sub.subdomain.example.com") == None


def test_OnlyChildrenSubdomainAndSameDomainSpiderMiddleware():
    url = "http://example.com"
    spider = CewlerSpider(Console(), url, file_words=None)
    mw = OnlyChildrenSubdomainAndSameDomainSpiderMiddleware(stats=None)
    pattern = mw.get_host_regex(spider)
    assert pattern.match("example.com") != None
    assert pattern.match("roysolberg.com") == None
    assert pattern.match("2example.com") == None
    assert pattern.match("subdomain.example.com") != None
    assert pattern.match("sub.subdomain.example.com") != None

    url = "http://subdomain.example.com"
    spider = CewlerSpider(Console(), url, file_words=None)
    mw = OnlyChildrenSubdomainAndSameDomainSpiderMiddleware(stats=None)
    pattern = mw.get_host_regex(spider)
    assert pattern.match("example.com") == None
    assert pattern.match("roysolberg.com") == None
    assert pattern.match("2example.com") == None
    assert pattern.match("other.example.com") == None
    assert pattern.match("subdomain.example.com") != None
    assert pattern.match("sub.subdomain.example.com") != None


def test_AnyParentAndSisterAndSubdomainMiddleware():
    url = "https://example.com"
    spider = CewlerSpider(Console(), url, file_words=None)
    mw = AnyParentAndSisterAndSubdomainMiddleware(stats=None)
    pattern = mw.get_host_regex(spider)
    assert pattern.match("example.com") != None
    assert pattern.match("roysolberg.com") == None
    assert pattern.match("2example.com") == None
    assert pattern.match("other.example.com") != None
    assert pattern.match("subdomain.example.com") != None
    assert pattern.match("sub.subdomain.example.com") != None
    assert pattern.match("www.example.com") != None

    url = "http://subdomain.example.com"
    spider = CewlerSpider(Console(), url, file_words=None)
    mw = AnyParentAndSisterAndSubdomainMiddleware(stats=None)
    pattern = mw.get_host_regex(spider)
    assert pattern.match("example.com") != None
    assert pattern.match("roysolberg.com") == None
    assert pattern.match("2example.com") == None
    assert pattern.match("other.example.com") != None
    assert pattern.match("subdomain.example.com") != None
    assert pattern.match("sub.subdomain.example.com") != None

    url = "https://google.co.uk"
    spider = CewlerSpider(Console(), url, file_words=None)
    mw = AnyParentAndSisterAndSubdomainMiddleware(stats=None)
    pattern = mw.get_host_regex(spider)
    assert pattern.match("google.co.uk") != None
    assert pattern.match("bing.co.uk") == None
    assert pattern.match("2google.co.uk") == None
    assert pattern.match("subdomain.google.co.uk") != None
    assert pattern.match("sub.subdomain.google.co.uk") != None

    url = "https://supersub.google.co.uk"
    spider = CewlerSpider(Console(), url, file_words=None)
    mw = AnyParentAndSisterAndSubdomainMiddleware(stats=None)
    pattern = mw.get_host_regex(spider)
    assert pattern.match("google.co.uk") != None
    assert pattern.match("bing.co.uk") == None
    assert pattern.match("2google.co.uk") == None
    assert pattern.match("subdomain.google.co.uk") != None
    assert pattern.match("sub.subdomain.google.co.uk") != None


if __name__ == "__main__":
    test_OnlyExactSameDomainSpiderMiddleware()
    test_OnlyChildrenSubdomainAndSameDomainSpiderMiddleware()
    test_AnyParentAndSisterAndSubdomainMiddleware()
    print("Everything passed")
