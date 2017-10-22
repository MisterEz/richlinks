"""
richlinks.urls
~~~~~~~~~~~~~
This module contains the url parsing and processing.
"""

import re
from ._internal_utils import do_template
from . import _settings

# import template engine #TODO template engine


class Url():
    final_url = None

    def __init__(self, url, protocol=None, domain=None, path=None, span=None):
        if protocol is None:
            matches = find_url_matches(url)
            assert matches is not None

            self.full_url = matches[0]['match']
            self.protocol = matches[0]['protocol']
            self.domain = matches[0]['domain']
            self.path = matches[0]['path']
            self.span = matches[0]['span']

        else:
            self.full_url = url
            self.protocol = protocol
            self.domain = domain
            self.path = path
            self.span = span

    def __str__(self):
        return self.full_url


def find_url_matches(user_string):
    """Finds urls in a string

    returns a list of dictionaries with keys as follows
        matches[0]['protocol'] #protocol of url (http:// or https://)
        matches[0]['domain'] #domain of url (eg. sub.google.com)
        matches[0]['match']  #the found url (eg. http://google.com/asd?parm=3)
        matches[0]['']  #tuple of start and end (eg. (0, 18))

    :param user_string: sanitized input to check for urls

    """

    # unit tests
    # https://regex101.com/r/RoaTIC/4
    # ftp & ip & unicode fail for now.
    # & the classic (https://google.com/thing/) fails of course

    regex = re.compile(
        r'(https?:\/\/)'  # [1] protcol https:// || http://
        r'(www\.)?'       # [2] www. or nothing
        r'([-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b)'  # [3] domain
        r'([/:][-a-zA-Z0-9@:%_\+\-,\*.~#?!&//=\(\)]*)?',  # [4] trailing
        re.IGNORECASE)

    matches = re.finditer(regex, user_string)

    # consider urllib.parse.urlparse

    matches_output = []
    for index, match in enumerate(matches):

        matches_output.append({
            'match':    match.group(0),
            'protocol': match.group(1),
            'domain':   match.group(3),
            'path':        match.group(4),
            'span':        match.span()
        })

    if not matches_output:
        return None

    return matches_output


def replace_urls(user_string, return_urls=False, settings=None):

    """Finds urls and replaces them with html links to that url.

    based off user templates

    returns user message with html
        https://google.com ->
            <a href="https://google.com">https://google.com</a>

    :param user_string: sanitized input to check for urls

    """
    if settings is None:
        template = _settings.default_templates()["url"]
    else:
        template = settings["templates"]["url"]

    matches = find_url_matches(user_string)

    if not matches:
        if return_urls:
            return (user_string, None)
        else:
            return user_string

    split_string = []

    # first slice starts at 0
    slice_start = 0

    if return_urls:
        urls = []

    for match in matches:

        # slice ends before the match
        slice_end = match['span'][0]
        split_string.append(user_string[slice_start:slice_end])
        # TODO template this

        html_link = do_template(template, {'URL': match['match']})
        split_string.append(html_link)

        slice_start = match['span'][1]

        if return_urls:
            url = Url(match['match'], match['protocol'], match['domain'],
                      match['path'],  match['span'])
            urls.append(url)

    # final slice segment
    split_string.append(user_string[slice_start:])

    # merge split string
    replaced_user_string = ''.join(split_string)

    if return_urls:
        return (replaced_user_string, urls)
    else:
        return replaced_user_string
