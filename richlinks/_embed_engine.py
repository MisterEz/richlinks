# avoid using apis for now -- avoid additional setup, faster
# these requests are really low traffic so it's not too impolite
import re
from . import _fetch


# Can this be embeded
def evaluate_embeds(url, settings):
    return url.domain in settings["embed_vars"]


def do_embed(url, embed_rules, response, settings):
    embed_vars = settings["embed_vars"][url.domain]
    if '_regex' in embed_vars:
        pattern = embed_vars['_regex']
        matches = re.match(pattern, url)
        
    return None
