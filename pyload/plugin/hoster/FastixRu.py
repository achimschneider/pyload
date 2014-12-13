# -*- coding: utf-8 -*-

import re

from random import randrange
from urllib import unquote

from pyload.utils import json_loads
from pyload.plugin.Hoster import Hoster


class FastixRu(Hoster):
    __name    = "FastixRu"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'http://(?:www\.)?fastix\.(ru|it)/file/(?P<ID>\w{24})'

    __description = """Fastix hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Massimo Rosamilia", "max@spiritix.eu")]


    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if name.endswith("..."):  # incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)
        return name


    def setup(self):
        self.chunkLimit = 3
        self.resumeDownload = True


    def process(self, pyfile):
        if re.match(self.__pattern, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Fastix")
            self.fail(_("No Fastix account provided"))
        else:
            self.logDebug("Old URL: %s" % pyfile.url)
            api_key = self.account.getAccountData(self.user)
            api_key = api_key['api']

            page = self.load("http://fastix.ru/api_v2/",
                             get={'apikey': api_key, 'sub': "getdirectlink", 'link': pyfile.url})
            data = json_loads(page)

            self.logDebug("Json data", data)

            if "error\":true" in page:
                self.offline()
            else:
                new_url = data['downloadlink']

        if new_url != pyfile.url:
            self.logDebug("New URL: %s" % new_url)

        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown"):
            #only use when name wasnt already set
            pyfile.name = self.getFilename(new_url)

        self.download(new_url, disposition=True)

        check = self.checkDownload({"error": "<title>An error occurred while processing your request</title>",
                                    "empty": re.compile(r"^$")})

        if check == "error":
            self.retry(wait_time=60, reason=_("An error occurred while generating link"))
        elif check == "empty":
            self.retry(wait_time=60, reason=_("Downloaded File was empty"))