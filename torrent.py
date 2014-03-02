#!/usr/bin/env python3
"""
Copyright (C) 2010-2013 Robert Nitsch
Licensed according to GPL v3.
"""

import datetime
import hashlib
import math
import optparse
import os
import re
import sys
import time

from py3bencode import bencode

__all__ = ['calculate_piece_length',
           'get_files_in_directory',
           'sha1_20',
           'split_path']

# #############
# CONFIGURATION

# do not touch anything below this line unless you know what you're doing!


VERSION =   '0.9.5'

# Note:
#  Kilobyte = kB  = 1000 Bytes
#  Kibibyte = KiB = 1024 Bytes  << used by py3createtorrent
KIB = 2**10
MIB = KIB * KIB


def sha1_20(data):
    """Return the first 20 bytes of the given data's SHA-1 hash."""
    m = hashlib.sha1()
    m.update(data)
    return m.digest()[:20]

def create_single_file_info(file, piece_length, include_md5=True):
    """
    Return dictionary with the following keys:
      - pieces: concatenated 20-byte-sha1-hashes
      - name:   basename of the file
      - length: size of the file in bytes
      - md5sum: md5sum of the file (unless disabled via include_md5)

    @see:   BitTorrent Metainfo Specification.
    @note:  md5 hashes in torrents are actually optional
    """
    assert os.path.isfile(file), "not a file"

    # Total byte count.
    length = 0

    # Concatenated 20byte sha1-hashes of all the file's pieces.
    pieces = bytearray()

    md5 = hashlib.md5() if include_md5 else None

    with open(file, "rb") as fh:
        while True:
            piece_data = fh.read(piece_length)

            _len = len(piece_data)
            if _len == 0:
                break

            if include_md5:
                md5.update(piece_data)

            length += _len

            pieces += sha1_20(piece_data)

    assert length > 0, "empty file"

    info =  {
            'pieces': pieces,
            'name':   os.path.basename(file),
            'length': length,
            
            }

    if include_md5:
        info['md5sum'] = md5.hexdigest()

    return info

def create_multi_file_info(directory,
                           files,
                           piece_length,
                           include_md5=True):
    """
    Return dictionary with the following keys:
      - pieces: concatenated 20-byte-sha1-hashes
      - name:   basename of the directory (default name of all torrents)
      - files:  a list of dictionaries with the following keys:
        - length: size of the file in bytes
        - md5sum: md5 sum of the file (unless disabled via include_md5)
        - path:   path to the file, relative to the initial directory,
                  given as list.
                  Examples:
                  -> ["dir1", "dir2", "file.ext"]
                  -> ["just_in_the_initial_directory_itself.ext"]

    @see:   BitTorrent Metainfo Specification.
    @note:  md5 hashes in torrents are actually optional
    """
    assert os.path.isdir(directory), "not a directory"

    # Concatenated 20byte sha1-hashes of all the torrent's pieces.
    info_pieces = bytearray()

    #
    info_files = []

    # This bytearray will be used for the calculation of info_pieces.
    # At some point, every file's data will be written into data. Consecutive
    # files will be written into data as a continuous stream, as required
    # by info_pieces' BitTorrent specification.
    data = bytearray()

    for file in files:
        path = os.path.join(directory, file)

        # File's byte count.
        length = 0

        # File's md5sum.
        md5 = hashlib.md5() if include_md5 else None

        with open(path, "rb") as fh:
            while True:
                filedata = fh.read(piece_length)

                if len(filedata) == 0:
                    break

                length += len(filedata)

                data += filedata

                if len(data) >= piece_length:
                    info_pieces  +=  sha1_20(data[:piece_length])
                    data          =  data[piece_length:]

                if include_md5:
                    md5.update(filedata)

        # Build the current file's dictionary.
        fdict = {
                'length': length,
                'path':   split_path(file)
                }

        if include_md5:
            fdict['md5sum'] = md5.hexdigest()

        info_files.append(fdict)

    # Don't forget to hash the last piece.
    # (Probably the piece that has not reached the regular piece size.)
    if len(data) > 0:
        info_pieces += sha1_20(data)

    # Build the final dictionary.
    info = {
           'pieces': info_pieces,
           'name':   os.path.basename(directory.strip("/\\")),
           'files':  info_files
           }

    return info

def get_files_in_directory(directory,
                           excluded_paths=set(),
                           relative_to=None,
                           excluded_regexps=set()):
    """
    Return a list containing the paths to all files in the given directory.

    Paths in excluded_paths are skipped. These should be os.path.normcase()-d.
    Of course, the initial directory cannot be excluded.
    Paths matching any of the regular expressions in excluded_regexps are
    skipped, too. The regexps must be compiled by the caller.
    In both cases, absolute paths are used for matching.

    The paths may be returned relative to a specific directory. By default,
    this is the initial directory itself.

    Please note: Only paths to files are returned!
    
    @param excluded_regexps: A set or frozenset of compiled regular expressions.
    """
    # Argument validation:
    if not isinstance(directory, str):
        raise TypeError("directory must be instance of: str")

    if not isinstance(excluded_paths, (set, frozenset)):
        raise TypeError("excluded_paths must be instance of: set or frozenset")

    if relative_to is not None:
        if not isinstance(relative_to, str):
            raise TypeError("relative_to must be instance of: str")

        if not os.path.isdir(relative_to):
            raise ValueError("relative_to: '%s' is not a valid directory" %
                             (relative_to))

    if not isinstance(excluded_regexps, (set, frozenset)):
        raise TypeError("excluded_regexps must be instance of: set or frozenset")

    # Helper function:
    def _get_files_in_directory(directory,
                                files,
                                excluded_paths=set(),
                                relative_to=None,
                                excluded_regexps=set(),
                                processed_paths=set()):
        # Improve consistency across platforms.
        # Note:
        listdir = os.listdir(directory)
        listdir.sort(key=str.lower)

        processed_paths.add(os.path.normcase(os.path.realpath(directory)))

        for node in listdir:
            path = os.path.join(directory, node)

            if os.path.normcase(path) in excluded_paths:
                continue

            regexp_match = False
            for regexp in excluded_regexps:
                if regexp.search(path):
                    regexp_match = True
                    break
            if regexp_match:
                continue

            if os.path.normcase(os.path.realpath(path)) in processed_paths:
                print("Warning: skipping symlink '%s', because it's target "
                      "has already been processed." % path, file=sys.stderr)
                continue
            processed_paths.add(os.path.normcase(os.path.realpath(path)))

            if os.path.isfile(path):
                if relative_to:
                    path = os.path.relpath(path, relative_to)
                files.append(path)
            elif os.path.isdir(path):
                _get_files_in_directory(path,
                                        files,
                                        excluded_paths=excluded_paths,
                                        relative_to=relative_to,
                                        excluded_regexps=excluded_regexps,
                                        processed_paths=processed_paths)
            else:
                assert False, "not a valid node: '%s'" % node

        return files

    # Final preparations:
    directory = os.path.abspath(directory)

    if not relative_to:
        relative_to = directory

    # Now do the main work.
    files = _get_files_in_directory(directory,
                                    list(),
                                    excluded_paths=excluded_paths,
                                    relative_to=relative_to,
                                    excluded_regexps=excluded_regexps)

    return files

def split_path(path):
    """
    Return a list containing all of a path's components.

    Paths containing relative components get resolved first.

    >>> split_path("this/./is/a/very/../fucked\\path/file.ext")
    ['this', 'is', 'a', 'fucked', 'path', 'file.ext']
    """
    if not isinstance(path, str):
        raise TypeError("path must be instance of: str")

    parts = []

    path = os.path.normpath(path)

    head = path

    while len(head) != 0:
        (head, tail) = os.path.split(head)
        parts.insert(0, tail)

    return parts

def remove_duplicates(old_list):
    """
    Remove any duplicates in old_list, preserving the order of its
    elements.

    Thus, for all duplicate entries only the first entry is kept in
    the list.
    """
    new_list = list()
    added_items = set()

    for item in old_list:
        if item in added_items:
            continue

        added_items.add(item)
        new_list.append(item)

    return new_list

def replace_in_list(old_list, replacements):
    """
    Replace specific items in a list.

    Note that one element may be replaced by multiple new elements.
    However, this also makes it impossible to replace an item with a
    list.

    Example given:
    >>> replace_in_list(['dont',
                         'replace',
                         'us',
                         'replace me'],
                        {'replace me': ['you',
                                        'are',
                                        'welcome']})
    ['dont', 'replace', 'us', 'you', 'are', 'welcome']
    """
    new_list = list()

    replacements_from = set(replacements.keys())

    for item in old_list:
        if item in replacements_from:
            new_item = replacements[item]

            if isinstance(new_item, list):
                new_list.extend(new_item)
            else:
                new_list.append(new_item)
        else:
            new_list.append(item)

    return new_list

def calculate_piece_length(size):
    """
    Calculate a reasonable piece length for the given torrent size.

    Proceeding:
    1. Start with 256 KIB.
    2. While piece count > 2000: double piece length.
    3. While piece count < 8:    use half the piece length.

    However, enforce these bounds:
    - minimum piece length = 16 KiB.
    - maximum piece length =  1 MiB.
    """
    if not isinstance(size, int):
        raise TypeError("size must be instance of: int")

    if size <= 0:
        raise ValueError("size must be greater than 0 (given: %d)" % size)

    if size < 16 * KIB:
        return 16 * KIB

    piece_length = 256 * KIB

    while size / piece_length > 2000:
        piece_length *= 2

    while size / piece_length < 8:
        piece_length /= 2

    # Ensure that: 16 KIB <= piece_length <= 1 * MIB
    piece_length = max(min(piece_length, 1 * MIB), 16 * KIB)

    return int(piece_length)

def make_torrent(node):
    # CALCULATE/SET THE FOLLOWING METAINFO DATA:
    # - info
    #   - pieces (concatenated 20 byte sha1 hashes of all the data)
    #   - files (if multiple files)
    #   - length and md5sum (if single file)
    #   - name (may be overwritten in the next section by the --name option)

    node = os.path.abspath(node)
    # Validate the given path.
    if not os.path.isfile(node) and not os.path.isdir(node):
        raise Exception("'%s' neither is a file nor a directory." % node)

    # Get the torrent's files and / or calculate its size.
    if os.path.isfile(node):
        torrent_size = os.path.getsize(node)
    else:
        torrent_files = get_files_in_directory(node)
        torrent_size = sum([os.path.getsize(os.path.join(node, file))
                            for file in torrent_files])

    # Torrents for 0 byte data can't be created.
    if torrent_size == 0:
        raise Exception("No data for torrent.")

    piece_length = calculate_piece_length(torrent_size)

    # Do the main work now.
    # -> prepare the metainfo dictionary.
    if os.path.isfile(node):
        info = create_single_file_info(node, piece_length)
    else:
        info = create_multi_file_info(node, torrent_files, piece_length)
    info['piece length'] = piece_length

    # Finish sub-dict "info".

    # Construct outer metainfo dict, which contains the torrent's whole
    # information.
    metainfo =  {
        'info': info,
        'announce': 'http://academictorrents.com/announce.php',
        'creation date': int(time.time()),
        'created by': '',
    }

    # ###################################################
    # BENCODE METAINFO DICTIONARY AND WRITE TORRENT FILE:
    # - properly handle KeyboardInterrups while writing the file

    # Use current directory.
    output_path = metainfo['info']['name'] + ".torrent"

    # Actually write the torrent file now.
    try:
        with open(output_path, "wb") as fh:
            fh.write(bencode(metainfo))
    except IOError as exc:
        print("IOError: " + str(exc), file=sys.stderr)
        print("Could not write the torrent file. Check torrent name and your "
              "privileges.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        # Properly handle KeyboardInterrupts.
        # todo: open()'s context manager may already do this on his own?
        if os.path.exists(output_path):
            os.remove(output_path)
    return output_path
