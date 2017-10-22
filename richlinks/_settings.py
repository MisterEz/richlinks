import tempfile


def pretty_print(settings, depth=0):
    for key, value in settings.items():
        print('\t' * depth + key + ": { ")
        if isinstance(value, dict):
            pretty_print(value, depth+1)

        elif isinstance(value, list):
            print('\t' * (depth + 1) + "[")
            for subval in value:
                print('\t' * (depth + 2) + str(subval))
            print('\t' * (depth + 1) + "]")
        elif isinstance(value, str):
            print('\t' * (depth + 1) + '"' + value + '"')
        else:
            print('\t' * (depth + 1) + str(value))
        print('\t' * depth + "}\n")


def default_templates():
    default_templates = {
        "website": {

            # ======= FULL =========
            "full": """
                <div class="rl_full_website rl_preview">
                    <div class="rl_full_content">
                        <div class="rl_image">
                            <a class="rl_image_link rl_external_link"
                                    href="*|URL|*" target="_blank">
                                <img src="*|IMG:CROP_THUMB(400x167)|*"
                                     alt="*|title|*">
                            </a>
                        </div>
                    </div>
                    <div class="rl_full_header">
                        <div class="rl_full_title">
                            *|title|*
                        </div>
                        <div class="rl_full_desc">
                            *|description|*
                        </div>
                        <div class="rl_full_url">
                            <a class="rl_external_link" href="*|URL|*"
                                target="_blank">*|DOMAIN|*</a>
                        </div>
                    </div>
                </div>
            """,

            # ======= COMPACT =========
            "compact":  """
                <div class="rl_compact rl_preview">
                    <div class="rl_compact_thumb rl_image">
                        <a class="rl_external_link" href="*|URL|*"
                                target="_blank">
                            <img src="*|IMG:CROP_THUMB(100x100)|*"
                                 alt="*|title|* Thumbnail">
                        </a>
                    </div>
                    <div class="rl_compact_title">
                        <a class="rl_external_link" href="*|URL|*"
                            target="_blank">*|title|*</a>
                    </div>
                    <div class="rl_compact_desc">
                        *|description|*
                    </div>
                    <div class="rl_compact_url">
                        <a class="rl_external_link" href="*|URL|*"
                                target="_blank">*|DOMAIN|*</a>
                    </div>
                </div>
            """
        },
        "image": {
            "full": """
                <div class="rl_full_image rl_preview">
                    <div class="rl_image">
                        <a class="rl_image_link rl_external_link"
                                href="*|URL|*" target="_blank">
                            <img src="*|IMG:THUMB(400x300)|*"
                                alt="*|DOMAIN|* IMAGE"  title="*|TITLETEXT|*">
                        </a>
                    </div>
                </div>
            """,
            "full+desc": """
                <div class="rl_full_image rl_full_image_plus_desc rl_preview">
                    <div class="rl_full_title">
                        *|title|*
                    </div>
                    <div class="rl_full_desc">
                        *|description|*
                    </div>
                    <div class="rl_image">
                        <a class="rl_image_link rl_external_link"
                                href="*|URL|*" target="_blank">
                            <img src="*|IMG:THUMB(400x300)|*"
                                alt="*|DOMAIN|* IMAGE"  title="*|TITLETEXT|*">
                        </a>
                    </div>
                </div>
            """,
            "crop+desc": """
                <div class="rl_full_image rl_full_image_plus_desc rl_preview">
                    <div class="rl_full_title">
                        *|title|*
                    </div>
                    <div class="rl_full_desc">
                        *|description|*
                    </div>
                    <div class="rl_image">
                        <a class="rl_image_link rl_external_link"
                                href="*|URL|*" target="_blank">
                            <img src="*|IMG:CROP_THUMB(400x300)|*"
                                alt="*|DOMAIN|* IMAGE"  title="*|TITLETEXT|*">
                        </a>
                    </div>
                </div>
            """
        },
        'embed': {
            # # old url parsing way, fast but dirty
            # 'vimeo': """
            # <div class="rl_iframe rl_16_9_responsive_iframe">
            #     <iframe width="640" height="360" frameborder="0"
            #         webkitallowfullscreen="" mozallowfullscreen=""
            #         allowfullscreen=""
            #         src="https://player.vimeo.com/video/*|URLREGEX(0)|*?color=949494&amp;title=0&amp;byline=0&amp;portrait=0"></iframe>
            # </div>
            # """,
            'html': """
               <div class="rl_preview rl_html rl_*|DOMAIN_CSS|* rl_html_*|type|*">
                    *|html|*
               </div>
            """,
            'responsive_html': """
               <div class="rl_preview rl_html rl_*|DOMAIN_CSS|* rl_html_*|type|*">
                    <div class="rl_responsive_iframe_container"
                         style="*|RESPONSIVE_PADDING|*">
                        *|html|*
                    </div>
               </div>
            """
        },
        "url": "<a href='*|URL|*' target='_blank'>*|URL|*</a>"
        # "media":{
        #     "img": ???
        # }
        # "embed":{
        #     "generic": default_templates["embed"]["generic"]
        # }
    }
    return default_templates


def default_website_variables():
    website_variables = {
        'general': {
            'title': [
                {'selector': 'meta[property="og:title"]',
                    'from': 'attr:content', 'type': 'text'},
                {'selector': 'title',
                    'from': 'string', 'type': 'text'},
                {'selector': 'meta[name="twitter:title"]',
                    'from': 'attr:content', 'type': 'text'},
                {'selector': 'h1', 'from': 'string', 'type': 'text'}
            ],
            'IMG': [
                {'selector': 'meta[property="og:image:secure_url"]',
                    'from': 'attr:content', 'type': 'img'},
                {'selector': 'meta[property="og:image"]',
                    'from': 'attr:content', 'type': 'img'},
                {'selector': 'meta[name="twitter:image"]',
                    'from': 'attr:content', 'type': 'img'},
                {'selector': 'img', 'from': 'attr:src', 'type': 'img'}
            ],
            'description': [
                {'selector': 'meta[property="og:description"]',
                    'from': 'attr:content', 'type': 'desc'},
                {'selector': 'meta[name="description"]',
                    'from': 'attr:content', 'type': 'desc'},
                {'selector': 'meta[name="twitter:image"]',
                    'from': 'attr:content', 'type': 'desc'},
                {'selector': 'article p',
                    'from': 'string', 'type': 'desc', 'strength': 'weak'},
                {'selector': 'main p',
                    'from': 'string', 'type': 'desc', 'strength': 'weak'},
                {'special':  'GET_TEXT', 'type': 'desc'}
            ]
        },
        #  # this works but i want to demostrate without for now
        # 'xkcd.com': {
        #     '_inherits': 'general',
        #     '_template': 'image/full+desc',
        #     'IMG': [
        #         {'selector': '#comic > img',  'from': 'attr:src',
        #             'type': 'img',
        #             'direct_link_img': True,
        #             'link_to_page': True,
        #             'main': True}
        #     ],
        #     'TITLETEXT': [
        #         {'selector': '#comic > img',  'from': 'attr:title',
        #          'type': 'text'}
        #     ]
        # },
        'imgur.com': {
            '_inherits': 'general',
            '_template': 'image/full',
            'IMG': [
                {'selector': '.post-image img',  'from': 'attr:src',
                    'type': 'img',
                    'direct_link_img': True,
                    'main': True}
            ]
        },
        'instagram.com': {
            '_inherits': 'general',
            '_template': 'image/full+desc',
            '_oembed': 'https://api.instagram.com/oembed'
        },
        'commons.wikimedia.org': {
            '_inherits': 'general',
            '_template': 'image/full',
            'IMG': [
                {'selector': '.fullImageLink img',  'from': 'attr:src',
                    'type': 'img',
                    'direct_link_img': True,
                    'main': True}
            ],
            'DESC': [
                {'selector': '.description',  'from': 'string',
                 'type': 'text'}
            ]
        },
        #  'vimeo.com': {
        #     '_template': 'embed/vimeo',
        #     '_urlregex': r"^https?:\/\/(?:www.)?vimeo\.com/(\d+)/?$"
        # },
        'youtube.com': {
            '_inherits': 'general',
            '_oembed': 'http://www.youtube.com/oembed',
            '_template': 'embed/responsive_html'
        },
        'vimeo.com': {
            '_inherits': 'general',
            '_oembed': 'https://vimeo.com/api/oembed.json',
            '_template': 'embed/responsive_html'
        },
        'streamable.com': {  # broken atm
            '_inherits': 'general',
            '_oembed': 'https://api.streamable.com/oembed.json',
            '_template': 'embed/responsive_html'
        },
        'flickr.com': {
            '_subrules': [
                (r"^(https?:\/\/(?:www.)?flickr\.com/photos/.*)$", {
                    '_inherits': 'general',
                    '_oembed': 'http://www.flickr.com/services/oembed/',
                    '_template': 'image/full'
                }),
                (r"^.*?$", {  # Failsafe -- general case
                    '_inherits': 'general'})
            ]
        },
        'kickstarter.com': {
            '_subrules': [
                (r"^(https?:\/\/(?:www.)?kickstarter\.com/projects/.*)$", {
                    '_inherits': 'general',
                    '_oembed': 'http://www.kickstarter.com/services/oembed'
                }),
                (r"^.*?$", {  # Failsafe -- general case
                    '_inherits': 'general'})
            ]
        },
        'ted.com': {
            '_subrules': [
                (r"^(https?:\/\/(?:www.)?ted\.com/talks/.*)$", {
                    '_inherits': 'general',
                    '_oembed': 'https://www.ted.com/services/v1/oembed.json',
                    '_template': 'embed/responsive_html'
                }),
                (r"^.*?$", {  # Failsafe -- general case
                    '_inherits': 'general'})
            ]
        },
        'twitch.tv': {   # twitch oembed api broken atm
            '_inherits': 'general',
            '_oembed': 'https://api.twitch.tv/v4/oembed',
            '_template': 'embed/responsive_html'
        },
        'go.twitch.tv': {  # twitch oembed api broken atm
            '_inherits': 'twitch.tv'
        },
        'clips.twitch.tv': {   # clips work fine though
            '_inherits': 'twitch.tv'
        },
        'gfycat.com': {   # clips work fine though
            '_inherits': 'general',
            '_oembed': 'https://api.gfycat.com/v1/oembed',
            '_template': 'embed/html'
        },
        'giphy.com': {
            '_inherits': 'general',
            '_oembed': 'http://giphy.com/services/oembed',
            '_template': 'images/full'
        },
        'media.giphy.com':
        {
            '_inherits': 'media.giphy.com'
        },
        'twitter.com': {  # twitter has really shitty oembed
                          # might have to do HTML+ sepcial css to fix it
            '_subrules': [
                (r"^(https?:\/\/(?:www.)?twitter\.com/.*?/status/.*)$", {
                    '_inherits': 'general',
                    '_oembed': 'https://publish.twitter.com/oembed',
                    '_oembed_schemes': ['https://twitter.com/*/status/*'],
                    '_template': 'embed/html'
                }),
                (r"^.*?$", {  # Failsafe -- general case
                    '_inherits': 'general',
                    'IMG': [
                        {'selector': '.ProfileAvatar-image',
                            'from': 'attr:src',
                            'type': 'img',
                            'direct_link_img': True,
                            'link_to_page': True}
                    ],
                    'description': [
                        {'selector': '.ProfileHeaderCard-bio',
                            'from': 'string',
                            'type': 'text'}
                    ]
                })
            ]
        },
        'facebook.com': {
            # oembed not working because of bug upstream in python-oembed
            # no good oembed libraries -- should make own
            '_subrules': [
                (r"^(https?:\/\/(?:www.)?facebook\.com/.*?/posts/.*)$", {
                    '_inherits': 'general',
                    '_oembed': 'https://www.facebook.com/plugins/post/oembed.json/',
                    '_oembed_schemes': ['https://www.facebook.com/*/posts/*']
                }),
                (r"^(https?:\/\/(?:www.)?facebook\.com/.*?/videos/.*)$", {
                    '_inherits': 'general',
                    '_oembed': 'https://www.facebook.com/plugins/video/oembed.json/',
                    '_oembed_schemes': ['https://www.facebook.com/*/videos/*'],
                    '_template': 'embed/responsive_html'
                }),
                (r"^.*?$", {  # Failsafe -- general case
                    '_inherits': 'general'
                })
            ]
        },
        'soundcloud.com': {
            '_inherits': 'general',
            '_oembed': 'https://soundcloud.com/oembed',
            '_template': 'embed/html'
        }
    }
    return website_variables


def default_settings():
    #  nested dictionary for settings. Usage:
    #  quality = default_settings["images"]["full"]["quality"]

    default_settings = {}

    # ========================================
    #  Security
    # ========================================
    default_settings["security"] = {
        # Define what isn't "external", these domains will be considered safe
        "internal_domains": None,  # ["example.com", "www.example.com"]

        # TODO check IPv6 space as well, Encforce these values
        "blocked_ip_space": ["localhost", "127.0.0.1", "192.168/16",
                             "10/8", "72.16/12"],

        # Safe domains skip rehosting images from own_domains, IMGUR, ETC.
        "skip_sanitize_safe_domains": False
    }

    # ========================================
    #  General
    # ========================================
    default_settings["general"] = {
        # Optional, for help in retreiving url of thumbnail & rehosted imgs
        "domain":  None,   # https://example.com/
        "webroot": None,    # /var/www/html/
        "search_tags": ['meta', 'p', 'img', 'div', 'title']
    }

    default_settings["media"] = {
        "accepted_mime_types": {
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/png": "png",
            "image/gif": "gif"
        },
        "safe_domains": [
            "imgur.com",
            "i.imgur.com"
        ]
    }

    # ========================================
    #  Download rules
    # ========================================
    default_settings["fetch"] = {
        "max_content_length": 10000000  # 10 mb
    }

    # ========================================
    #  Images
    # ========================================
    default_settings["images"] = {
        "full": {
            "save_location":  tempfile.gettempdir(),
            "quality":        85,
            "max_dimensions": (1920, 1080),
            "max_size":       1000000
        },
        "thumb": {
            "save_location":  tempfile.gettempdir(),
            "quality":        70,
        }
    }

    # ========================================
    #  HTML Templates
    # ========================================
    default_settings["templates"] = default_templates()

    # ========================================
    #  Web Scraping definitions
    # ========================================
    default_settings["website_vars"] = default_website_variables()
    default_settings["priority_website_vars"] = {}

    return default_settings
