# CeWLeR - Custom Word List generator Redefined
_CeWLeR_ crawls from a specified URL and collects words to create a custom wordlist.

It's a great tool for security testers and bug bounty hunters. The lists can be used for password cracking, subdomain enumeration, directory and file brute forcing, API endpoint discovery, etc. It's good to have an additional target specific wordlist that is different than what everybody else use.

_CeWLeR_ was sort of originally inspired by the really nice tool [CeWL](https://github.com/digininja/CeWL). I had some challenges with _CeWL_ on a site I wanted a wordlist from, but without any Ruby experience I didn't know how to contribute and work around it. So instead I created a custom word list generator in Python to get the job done.

## At a glance
<img src="https://github.com/roys/cewler/blob/main/misc/demo.gif?raw=true" width="800" />

## Features
- Generates custom wordlists by scraping words from web sites
- A lot of options:
  - Output to screen or file
  - Can stay within subdomain, or visit sibling and child subdomains, or visit anything within the same top domain
  - Can stay within a certain depth of a website
  - Speed can be controlled
  - Word length and casing can be configured
  - JavaScript and CSS can be included
  - Crawled URLs can be output to file
  - ++
- Using the excellent [Scrapy](https://scrapy.org) framework for scraping and using the beautiful [rich](https://github.com/Textualize/rich) library for terminal output

## Commands and options
### Quick examples
#### Output to file
Will output to file unless a file is specified.  
`cewler --output wordlist.txt https://example.com`  

#### Control speed and depth
The rate is specified in requests per second. Please play nicely and don't don't break any rules.  
`cewler --output wordlist.txt --rate 5 --depth 2 https://example.com`  

#### Change User-Agent header
The default User-Agent is a common browser.  
`cewler --output wordlist.txt --user-agent "Cewler" https://example.com`  

#### Control casing, word length and characters
Unless specified the words will have mixed case and be of at least 5 in length.  
`cewler --output wordlist.txt --lowercase --min-word-length 2 --without-numbers https://example.com`  

#### Visit all domains - including parent, children and siblings
The default is to just visit exactly the same (sub)domain as specified.  
`cewler --output wordlist.txt -s all https://example.com`  

#### Visit same (sub)domain + any belonging child subdomains
`cewler --output wordlist.txt -s children https://example.com`  

#### Include JavaScript and/or CSS
If you want you can include links from `<script>` and `<link>` tags, plus words from within JavaScript and CSS.  
`cewler --output wordlist.txt --include-js --include-css https://example.com`  

#### Output visited URLs to file
It's also possible to store the crawled files to a file.
`cewler --output wordlist.txt --output-urls urls.txt https://example.com`  

#### Ninja trick 🥷
If it just takes too long to crawl a site you can press `ctrl + c` once(!) and wait while the spider finishes the current requests and then whatever words have been found so far is stored to the output file.

### All options
```
cewler -h
usage: cewler [-h] [-d DEPTH] [-js] [-l] [-m MIN_WORD_LENGTH] [-o OUTPUT] [-ou OUTPUT_URLS] [-r RATE] [-s {all,children,exact}] [--stream] [-u USER_AGENT] [-v] [-w] url

Custom Word List generator Redefined

positional arguments:
  url                   URL to start crawling from

options:
  -h, --help            show this help message and exit
  -d DEPTH, --depth DEPTH
                        directory path depth to crawl, 0 for unlimited (default: 2)
  -css, --include-css   include CSS from external files and <style> tags
  -js, --include-js     include JavaScript from external files and <script> tags
  -l, --lowercase       lowercase all parsed words
  -m MIN_WORD_LENGTH, --min-word-length MIN_WORD_LENGTH
  -o OUTPUT, --output OUTPUT
                        file were to stream and store wordlist instead of screen (default: screen)
  -ou OUTPUT_URLS, --output-urls OUTPUT_URLS
                        file were to stream and store URLs visited (default: not outputted)
  -r RATE, --rate RATE  requests per second (default: 20)
  -s {all,children,exact}, --subdomain_strategy {all,children,exact}
                        allow crawling [all] domains, including children and siblings, only [exact] the same (sub)domain (default), or same domain and any belonging [children]
  --stream              writes to file after each request (may produce duplicates because of threading) (default: false)
  -u USER_AGENT, --user-agent USER_AGENT
                        User-Agent header to send (default: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36)
  -v, --verbose         A bit more detailed output
  -w, --without-numbers
                        ignore words are numbers or contain numbers
```

### Digging into the code
If you want to do some tweaking you yourself you can probably find what you want in [blob/main/src/constants.py](blob/main/src/constants.py) and [blob/main/src/spider.py](blob/main/src/spider.py)

## Installation and upgrade
### Alternative 1 - installing from PyPI
Package homepage: https://pypi.org/project/cewler/

`python3 -m pip install cewler`

#### Upgrade
`python3 -m pip install cewler --upgrade`


### Alternative 2 - installing from GitHub
#### 1. Clone repository
`git clone https://github.com/roys/cewler.git --depth 1`

#### 2. Install dependencies
`python3 -m pip install -r requirements.txt`

#### 3. Shortcut on Un*x based system (optional)
```
cd src/cewler
chmod +x cewler.py
ln -s $(pwd)/cewler.py /usr/local/bin/cewler
cewler -h
```

#### Upgrade
`git pull`


## Pronunciation
_CeWLeR_ is pronounced _"cooler"_.

## License
[Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](LICENSE)
