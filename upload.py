#!/usr/bin/python3
import sys
import json
from base64 import b64encode
from py3createtorrent import main as maketorrent
from os.path import basename, exists
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import re

if len(sys.argv)!=9:
    print("Usage: ./upload.py <api_key> <filename_or_directory> <name> <authors> <descr> <category> <tags> <urllist>")
    print("Put api_key in quotes!")
    sys.exit()

# create the torrent
torrent_args = sys.argv[0:2]
torrent_args[1] = sys.argv[2]
torrent_args.append('http://academictorrents.com/announce.php')
torrentname = basename(sys.argv[2]) + ".torrent"

# if file exists, we assume torrent already created
if not exists(torrentname):
    maketorrent(torrent_args)

# get base64 of torrent
f = open(torrentname, 'rb')
b64_torrent = b64encode(f.read())
f.close()

# extract cookie args
matches = re.match("uid=(.*);pass=(.*)", sys.argv[1])

if sys.argv[6].lower() == 'dataset':
    category = 6
elif sys.argv[6].lower() == 'paper':
    category = 5
else:
    print("Category must be either 'paper' or 'dataset'")
    exit()

post_params = {
    'uid' : matches.groups()[0],
    'pass' : matches.groups()[1],
    'name' : sys.argv[3],
    'authors' : sys.argv[4],
    'descr' : sys.argv[5],
    'category' : category,
    'tags' : sys.argv[7],
    'urllist' : sys.argv[8],
    'file' : b64_torrent
}

data = urlencode(post_params).encode('utf-8')

req = Request('http://academictorrents.com/api/paper', data)

try:
    response = urlopen(req)
except HTTPError as e:
    print(e)
    response = e

print(response.read())

