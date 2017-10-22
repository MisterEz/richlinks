from pathlib import Path
import re
import warnings
from bs4 import BeautifulSoup, SoupStrainer

from lxml.html.clean import clean_html
from urllib.parse import urljoin
import html
import time
import json

import oembed


from . import _fetch
from . import _internal_utils
from . import _image
from .url import *


def evaluate_website_rules(url, request, webrules_dict,
                           priority_webrules_dict):

    if url.domain in priority_webrules_dict:
        rules = priority_webrules_dict[url.domain]

    elif url.domain in webrules_dict:
        rules = webrules_dict[url.domain]

    elif '_general' in priority_webrules_dict:
        rules = priority_webrules_dict['_general']

    else:
        rules = webrules_dict['general']

    if '_subrules' in rules:
        has_subrule = False
        for subrule in rules['_subrules']:
            pattern = subrule[0]
            if re.match(pattern, url.full_url):
                has_subrule = True
                rules = subrule[1]
                break

        if not has_subrule:
            return None

    while '_inherits' in rules:
        child_rules = rules.copy()

        # search for the base rules
        if (child_rules['_inherits'] in priority_webrules_dict):
            rules = priority_webrules_dict[child_rules['_inherits']].copy()

        elif (child_rules['_inherits'] in webrules_dict):
            rules = webrules_dict[child_rules['_inherits']].copy()

        else:
            # not found
            child_rules.pop('_inherits', None)
            break

        child_rules.pop('_inherits', None)
        # combine the new and old rules
        for key in child_rules:
            if key in rules:
                # merge rules
                rules[key] = child_rules[key] + rules[key]
            else:
                rules[key] = child_rules[key]

    return rules


# move to utils
def rehosted_url(file_path, settings):
    domain = settings["general"]["domain"]
    webroot = settings["general"]["webroot"]

    # TODO test this on symbolic links
    webroot = Path(webroot)
    file_path = Path(file_path)
    if not domain.endswith("/"):
        domain += "/"

    # check file is in webroot
    if (webroot in file_path.parents):
        ass_end = file_path.relative_to(webroot)
        rehosted_url = domain + str(ass_end)
        return rehosted_url

    return None


# a better man would rename value here
def sanitize_img(value, settings):
    if value["content"][:2] == "//":
        protocol = website_variables["PROTOCOL"]['content'][:-2]
        value["content"] = protocol + value["content"]

    # download img for thumb or rehost
    value["path"] = _fetch.download_img(value["content"], settings)
    if not value["path"]:
        # failed to rehost, so it's not safe to use
        print("failed to download: ", value["content"])
        return None

    # check if we should rehost
    if (not settings["security"]["skip_sanitize_safe_domains"] and
            ("safe" not in value)):
        # optionally save rehosted url
        if (settings["general"]["domain"] and
                settings["general"]["webroot"]):
            value["content"] = rehosted_url(value["path"], settings)
        else:
            value["content"] = None

    return value


def sanitize_website_variables(website_variables, settings):
    # TODO use normalize_full_img

    for key, value in website_variables.items():
        # strip any html tags
        if "content" not in value or not value["content"]:
            continue

        if (value['type'] != "img" and value['type'] != "url"):
            value['content'] = html.escape(value['content'])
        else:
            value['content'] = html.unescape(value['content'])

        value['content'] = value['content'].replace("\n", "")
        value['content'] = value['content'].rstrip()

        # img download
        if (value["type"] == "img"):
            value = sanitize_img(value, settings)

    return website_variables


def get_easy_variables(website_rules, url, settings):
    website_variables = {}
    website_variables["URL"] = {
        'content':  url.full_url,
        'strength': 'high',
        'type': 'attr'
    }
    website_variables["DOMAIN"] = {
        'content':  url.domain,
        'strength': 'high',
        'type': 'text'
    }
    website_variables["DOMAIN_CSS"] = {
        'content':  url.domain.replace('.', '_'),
        'strength': 'high',
        'type': 'text'
    }
    website_variables["PROTOCOL"] = {
        'content':  url.protocol,
        'strength': 'high',
        'type': 'text'
    }
    if '_template' in website_rules:
        website_variables['_template'] = website_rules['_template']

    if '_urlregex' in website_rules:
        pattern = website_rules['_urlregex']
        match = re.search(pattern, url.full_url)
        print(pattern, url.full_url)
        if match:
            for index, group in enumerate(match.groups()):
                if not group:
                    continue
                key = "URLREGEX("+str(index)+")"
                website_variables[key] = {
                    'content': group,
                    'type': 'text'
                }
        else:
            print("no match")
            return None

    if '_oembed' in website_rules:
        consumer = oembed.OEmbedConsumer()

        if '_oembed_schemes' in website_rules:
            schemes = website_rules['_oembed_schemes']
        else:
            schemes = 'http://*/' + url.domain + '/*'

        endpoint = oembed.OEmbedEndpoint(website_rules['_oembed'], schemes)
        consumer.addEndpoint(endpoint)

        try:
            response = consumer.embed(url.full_url)
        except:
            response = None
            print('no oembed for URL:', url.full_url)

        if response:
            for key, value in response.getData().items():
                website_variables[key] = {
                    'content': str(value),
                    'type': 'text',
                    'strength': 'high'
                }
            if 'width' in website_variables and 'height' in website_variables:
                try:
                    height = int(website_variables['height']['content'])
                    width = int(website_variables['width']['content'])
                except ValueError:
                    # sometimes these are null
                    pass
                else:
                    prcnt_ratio = (height/width)*100
                    prcnt_ratio = str(round(prcnt_ratio, 2))
                    website_variables['RESPONSIVE_PADDING'] = {
                        'content': 'padding-bottom: ' + prcnt_ratio + '%;',
                        'type': 'text',
                        'strength': 'high'
                    }
        else:
            # no response so remove overwritting template
            if '_template' in website_variables:
                del website_variables["_template"]
                del website_rules["_template"]

    return website_variables


def parse_variables(website_rules, url, response, settings):

    website_variables = {}
    easy_website_vars = get_easy_variables(website_rules, url, settings)

    print(easy_website_vars)
    # we have a weird relationship with images -- might need to fix that
    if ('url' in easy_website_vars and 'type' in easy_website_vars and
            easy_website_vars['type']['content'] == 'photo'):
        easy_website_vars['IMG'] = easy_website_vars['url']
        easy_website_vars['IMG']['type'] = 'img'
        easy_website_vars['IMG'] = sanitize_img(easy_website_vars['IMG'],
                                                settings)
    elif 'thumbnail_url' in easy_website_vars:
        easy_website_vars['IMG'] = easy_website_vars['thumbnail_url']
        easy_website_vars['IMG']['type'] = 'img'
        easy_website_vars['IMG'] = sanitize_img(easy_website_vars['IMG'],
                                                settings)

    # check if we got all the tags from easy..()
    unclaimed_tags = False
    for key, rule_array in website_rules.items():
        if key not in easy_website_vars:
            if key[:1] is not '_' and key is not 'description':
                # shitty hack so help me
                # speeds up oembeds 500%
                # TODO this more intelligently
                unclaimed_tags = True
                print(key, " not claimed by easy")
                break

    if not unclaimed_tags:
        return easy_website_vars

    # TODO rewrite using lxml insead of BeautifulSoup :(
    search_tags = settings["general"]["search_tags"]
    strainer = SoupStrainer(search_tags)
    soup = BeautifulSoup(response['data'], 'lxml', parse_only=strainer)

    for script in soup(['script', 'style']):
        script.decompose()

    # for each rules -- try each until sucess -- save to new dict
    for key, rule_array in website_rules.items():
        if key[:1] == "_":
            website_variables[key] = rule_array
            continue
        if key in easy_website_vars or key in website_variables:
            print("passed ", key, " because it was done")
            continue
        for rule in rule_array:
            if 'special' in rule:
                if rule['special'] == 'GET_TEXT':
                    website_variables[key] = {
                        'content': soup.get_text(" ")[:1024],
                        'type': rule['type'],
                        'strength': 'weak'}
                    break

            if ('selector' not in rule or
                    'from' not in rule):
                continue

            try:
                element = soup.select_one(rule['selector'])
            except:
                print("ERROR bad rule:", rule['selector'])
                raise

            if element is None:
                if 'main' in rule:
                    return None
                continue

            strength = "high"
            if "strength" in rule:
                strength = rule["strength"]

            if rule['from'] == 'string':
                if not element.string:
                    if 'main' in rule:
                        return None
                    continue

                if rule['type'] == "img" or rule['type'] == "url":
                    content = urljoin(url.full_url, "element.string")
                else:
                    content = element.string

                website_variables[key] = {
                    'content': content,
                    'type': rule['type'],
                    'strength': strength}

                break
            elif rule['from'][:5] == 'attr:':
                if (rule['from'][5:] not in element.attrs or
                        not element[rule['from'][5:]]):

                    if 'main' in rule:
                        return None
                    continue

                if rule['type'] == "img" or rule['type'] == "url":
                    content = urljoin(url.full_url, element[rule['from'][5:]])
                else:
                    content = element[rule['from'][5:]]

                website_variables[key] = {
                    'content': content,
                    'type': rule['type'],
                    'strength': strength}

                break

    website_variables = sanitize_website_variables(website_variables, settings)

    merged_vars = {**easy_website_vars, **website_variables}

    return merged_vars


def do_web_template(template, web_vars):
    for key, value in web_vars.items():
        if key[:1] == "_" or not value:
            continue
        content = value["content"]
        regex = r'\*\|'+re.escape(key)+r'\|\*'
        template = re.sub(regex, content, template)

    # remove any unclaimed *|_|* tags
    regex = r'\*\|.*?\|\*'
    template = re.sub(regex, "", template)

    return template


def find_thumbs(template):
    regex = r"\*\|((.*?)\:(CROP_)?THUMB\((\d+)x(\d+)\))\|\*"
    thumb_matches = re.findall(regex, template)
    thumbs = {}
    for match in thumb_matches:
        # *|MAIN_THUMB:THUMB(200x100)|*
        # becomes {"MAIN_THUMB=THUMB(100x100)": {
        #       "name": "MAIN_THUMB"
        #       "dimensions": (100, 100),
        #       "crop": False
        # }

        if match[2].upper() == "CROP_":
            crop = True
        else:
            crop = False

        thumbs[match[0]] = {
            "name": match[1],
            "dimensions": (int(match[3]), int(match[4])),
            "crop": crop
        }

    return thumbs


def make_html(website, template, settings):
    url = website.url
    web_vars = website.website_variables

    if template not in settings["templates"]["website"]:
        warnings.simplefilter('No such website template', UserWarning)
        return None

    if ("_template" in web_vars and web_vars["_template"]):
        template_parts = web_vars["_template"].split('/')
        template = settings['templates'][template_parts[0]][template_parts[1]]
    else:
        template = settings["templates"]["website"][template]

    thumbs = find_thumbs(template)

    for key, thumb in thumbs.items():
            if thumb["name"] in web_vars and web_vars[thumb["name"]]:
                img_path = web_vars[thumb["name"]]["path"]
                thumb_info = _image.make_thumb(img_path,
                                               thumb["dimensions"], settings,
                                               thumb["crop"])
                
                if not thumb_info:
                    print("thumb failed")
                    continue

                thumb_path = thumb_info[0]
                thumb_size = thumb_info[1]

                thumb_url = rehosted_url(thumb_path, settings)

                # save the thumb as a web var
                web_vars[key] = {
                    'strength': 'high',
                    'type': 'img',
                    'path': thumb_path,
                    'content': thumb_url
                }

                # also make the dimension function keys
                if ":THUMB(" in key:
                    width_key = key.replace(':THUMB(', ":THUMB_WIDTH(")
                    web_vars[width_key] = {
                        'strength': 'high',
                        'type': 'text',
                        'content': str(thumb_size[0])
                    }

                    height_key = key.replace(':THUMB(', ":THUMB_HEIGHT(")
                    web_vars[height_key] = {
                        'strength': 'high',
                        'type': 'text',
                        'content': str(thumb_size[1])
                    }

    print("Make html: ", web_vars)
    html = do_web_template(template, web_vars)

    return html


def evaluate_media_rules(url, response, settings):
    rules = {
        "safe": False,
        "mime_type": None
    }
    if (response['headers']['content-type']
            in settings["media"]["accepted_mime_types"]):
        if url.domain in settings["media"]["safe_domains"]:
            rules["safe"] = True

        rules["mime_type"] = response['headers']['content-type']

    else:
        return None

    return rules


def get_media(url, rules, img_path, settings):
    # only do images for now

    if rules["safe"]:
        img_url = url.full_url
    else:
        if not _image.normalize_full_img(img_path, settings):
            print("failed to normalize")
            return None

        img_url = rehosted_url(img_path, settings)

    media_vars = {}

    media_vars["URL"] = {
        'content':  img_url,
        'strength': 'high',
        'type': 'attr'
    }
    media_vars["DOMAIN"] = {
        'content':  url.domain,
        'strength': 'high',
        'type': 'text'
    }
    media_vars["PROTOCOL"] = {
        'content':  url.protocol,
        'strength': 'high',
        'type': 'text'
    }
    media_vars["IMG"] = {
        'content': img_url,
        'strength': 'high',
        'type': 'attr',
        'path': img_path
    }
    media_vars["_template"] = 'image/full'

    return _fetch.Website(url, media_vars, "media")


def requires_download(web_rules):
    for key, value in web_rules.items():
        if key[:1] is not '_':
            return True
    return False
