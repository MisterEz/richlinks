import os
import urllib.request
from urllib.error import URLError, HTTPError
import shutil
import time
import binascii
import gzip
import zlib
from io import BytesIO
import struct


from .url import *
from ._website_engine import *


class Website():
    def __init__(self, url, website_variables, content_type="website"):
        self.website_variables = website_variables
        self.url = url
        self.content_type = content_type


def get_response(url, request_type, compress=True):
    # TODO Critical -- forbid local domains -- forbid internal ips
    useragent = ('RichLinks/0.01')

    request = urllib.request.Request(url.full_url)
    if compress:
        request.add_header("Accept-Encoding", ', '.join(('gzip', 'deflate')))
    request.add_header("Accept", '*/*')
    request.add_header("User-Agent", useragent)

    if request_type == "head":
        request.get_method = lambda: 'HEAD'

    try:
        response = urllib.request.urlopen(request, None, 5)
    except URLError as e:
        if hasattr(e, 'reason'):
            print(url.full_url, ' -- We failed to reach a server: Reason: ',
                  e.reason)
            return None
        elif hasattr(e, 'code'):
            print(url.full_url, ' -- The server fucked up: Error code: ',
                  e.code)
            return None

    # https://github.com/kurtmckee/feedparser/blob/develop/feedparser/http.py
    result = {}
    result['headers'] = dict((k.lower(), v)
                             for k, v in response.headers.items())

    result['url'] = response.geturl()
    data = response.read()

    if not data:
        return result

    # decompress gzip or zlib
    if 'content-encoding' in result['headers']:
        if 'gzip' in result['headers']['content-encoding']:
            try:
                data = gzip.GzipFile(fileobj=BytesIO(data)).read()
            except (EOFError, IOError, struct.error):
                # try again without compression
                return get_response(url, request_type, False)
        elif 'deflate' in result['headers']['content-encoding']:
            try:
                data = zlib.decompress(data)
            except zlib.error:
                # try again without compression
                return get_response(url, request_type, False)

    result['data'] = data

    return result


def do_fetch(url, settings):
    if type(url) is str:
        try:
            url = Url(url)
        except AssertionError:
            return None

    head_response = get_response(url, "head")

    if not head_response:
        return None

    # save the new url -- forget the old one
    url = Url(head_response['url'])

    # print(head_response['url'])
    # print(head_response['headers'])

    # CHECK MAXIMUM SIZE
    # this isn't 100% fool proof, double check down the line
    if ('content-length' in head_response['headers'] and
            int(head_response['headers']['content-length']) >
            settings["fetch"]["max_content_length"]):
        # Content too large
        print("content too large")
        return None

    # ===================================================================
    # MEDIA ENGINE -- image/png image/jpg video/mp4
    media_rules = evaluate_media_rules(url, head_response, settings)

    if (media_rules is not None):
        img_path = download_img(url, settings)
        if img_path is not None:
            return get_media(url, media_rules, img_path, settings)

    # ===================================================================
    # WEBSITE PREVIEW ENGINE -- xkcd.com, wikipedia.org -- general rules
    website_rules = evaluate_website_rules(url, head_response,
                                           settings["website_vars"],
                                           settings["priority_website_vars"])

    if (website_rules is not None):

        if requires_download(website_rules):
            full_response = get_response(url, "full")
            url = Url(full_response['url'])
            variables = parse_variables(website_rules, url, full_response,
                                        settings)
        else:
            full_response = None
            variables = get_easy_variables(website_rules, url, settings)

        if variables:
            website = Website(url, variables)
            return website  # return website
        else:
            print("no variables?")
            return None

    return None


def download_img(url, settings, path=None):
    if type(url) is str:
        try:
            url = Url(url)
        except AssertionError:
            return None

    if path is None:
        path = settings["images"]["full"]["save_location"]

    response = get_response(url, "full", False)

    if (not response):
        print("no download_img response")
        return None

    if 'content-type' not in response['headers']:
        return None  # this actually happens sometimes wtf

    accepted_mime_types = settings['media']['accepted_mime_types']

    # validate image & remember file extension
    mime_type = response['headers']['content-type'].split(';')[0].lower()

    if (mime_type in accepted_mime_types):
        extension = accepted_mime_types[mime_type]
    else:
        print(response['headers']['content-type'])
        return None

    # prevent users guessing image urls from timings
    bytes = os.urandom(8)
    url_token = binascii.hexlify(bytes).decode()

    filename = str(int(time.time())) + "_" + url_token
    filename += "." + extension
    file_path = os.path.join(path, filename)

    raw_img = open(file_path, 'wb')
    raw_img.write(response['data'])
    return file_path
