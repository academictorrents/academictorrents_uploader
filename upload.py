#!/usr/bin/python3
import sys
from base64 import b64encode
from py3createtorrent import main as maketorrent
from os.path import basename
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import re

if len(sys.argv)!=9:
    print("Usage: ./upload.py <filename_or_directory> <api_key> <name> <authors> <descr> <category> <tags> <urllist>")
    print("Put api_key in quotes!")
    sys.exit()

# create the torrent
torrent_args = sys.argv[0:2]
torrent_args.append('http://academictorrents.com/announce.php')
maketorrent(torrent_args)
torrentname = basename(sys.argv[1]) + ".torrent"

# get base64 of torrent
f = open(torrentname, 'rb')
b64_torrent = b64encode(f.read())
f.close()

# extract cookie args
matches = re.match("uid=(.*)&pass=(.*)", sys.argv[2])

post_params = {
    'uid' : matches.group(1),
    'pass' : matches.group(2),
    'name' : sys.argv[3],
    'authors' : sys.argv[4],
    'descr' : sys.argv[5],
    'category' : sys.argv[6],
    'tags' : sys.argv[7],
    'urllist' : sys.argv[8],
    'file' : b64_torrent
}

data = urlencode(post_params).encode('utf-8')
req = Request('http://academictorrents.com/api/paper', data)
response = urlopen(req)
the_page = response.read()
