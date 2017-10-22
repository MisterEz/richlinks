from . import url
from . import _fetch
from . import _website_engine
from . import _settings


class Richlinks():
    """Provides the api and stores the settings"""

    def __init__(self):
        self.settings = _settings.default_settings()

    def fetch(self, url):
        return _fetch.do_fetch(url, self.settings)

    def get_html(self, website, template="full"):
        return _website_engine.make_html(website, template, self.settings)

    def replace_urls(self, user_string):
        return url.replace_urls(user_string, True, self.settings)

    def get_settings(self):
        return self.settings

    def print_settings(self):
        _settings.pretty_print(self.settings)
