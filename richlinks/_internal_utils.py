import re

# TODO move most template stuff here


def do_template(template, variable_dict):
    for key, value in variable_dict.items():
        regex = r'\*\|'+re.escape(key)+r'\|\*'
        template = re.sub(regex, value, template)

    # remove any unclaimed *|_|* tags
    regex = r'\*\|.*?\|\*'
    template = re.sub(regex, "", template)

    return template
