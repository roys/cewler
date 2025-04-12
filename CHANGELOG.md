# Changelog
Changelog for _cewler_.

List of changes, newest changes first.
('+' = new feature, '-' = removed feature, '*' = changed feature)

## Version 1.3.1
 \+ Added support for application/json (always enabled, no flags)
## Version 1.3.0
 \+ Added support for `<iframe>` and `<frame>`.
 \* Changed default User-Agent to `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36`.
 \* Fixed warnings in Python 3.12+. 
 \* Library upgrades and belonging adjustments.
## Version 1.2.0
 \+ Added support for extracting text from PDF files. Example command: `cewler --include-pdf https://example.com`.  
## Version 1.1.2
 \* Fix for [#1](https://github.com/roys/cewler/issues/1): Specified `Twisted` version needed for `Scrapy`.  
 \* Cleaned up code structure a bit.
## Version 1.1.1
 \* Improved parsing of text by HTML unquoting it (and not only HTML unescaping named and numeric character references).
## Version 1.1.0
 \+ Added support for all kinds of meta-tags in the form `<meta name="some-key" content="content-to-be-scraped">`.  
 \+ Added support for scraping e-mail addresses. They will always be added to the wordlist, but they can also be stored in separate file using `cewler --output-emails emails.txt https://example.com`.  
 \+ Adding `http://` to start URL if there's no `://` in the URL.  
## Version 1.0.9
 \* Improved screen output.  
## Version 1.0.8
 \+ Added support for storing parsed URLs. Example command: `cewler --output-urls urls.txt https://example.com`.  
 \+ Added support for crawling JavaScript via both external files and tags. Example command: `cewler --include-js https://example.com`.  
 \+ Added support for crawling CSS via both external files and tags. Example command: `cewler --include-css https://example.com`.  
## Version 1.0.7
 \+ Added crawling of error pages.  
 \+ Added crawling of HTML comments.  
## Version 1.0.6
 \+ Initial release.  
