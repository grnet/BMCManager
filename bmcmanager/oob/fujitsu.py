# Copyright (C) 2020  GRNET S.A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import re
from subprocess import Popen
from urllib import error as urlerror
from urllib import request
import tempfile

from bs4 import BeautifulSoup

from bmcmanager.oob.base import OobBase


class Fujitsu(OobBase):
    def _get_realm(self):
        """Do an unauthenticated request to get the realm for auth."""
        opener = request.build_opener()
        request.install_opener(opener)
        try:
            request.urlopen(self.oob_info['ipmi'])
        except urlerror.HTTPError as err:
            header = err.headers.get('WWW-Authenticate')
            m = re.match(r'Digest realm="([@\w\s-]+)",', header)
            realm = m.groups()[0]
        return realm

    def _install_auth(self):
        """Setup digest auth"""
        realm = self._get_realm()

        uri = self.oob_info['ipmi']
        username = self.username
        password = self.password

        auth_handler = request.HTTPDigestAuthHandler()
        auth_handler.add_password(realm=realm,
                                  uri=uri, user=username, passwd=password)
        opener = request.build_opener(auth_handler)
        request.install_opener(opener)

    def _find_avr_url(self):
        """Parse the main page to find the URL for JWS"""
        url = self.oob_info['ipmi']

        req = request.Request(url)
        data = request.urlopen(req).read()
        soup = BeautifulSoup(data)
        jnlp_desc = [u'Video Redirection (JWS)']
        links = soup.find_all('a', href=True)
        for link in links:
            if link.contents == jnlp_desc:
                return url + '/' + link['href']

    def _save_tmp_jnlp(self):
        """Fetch the XML jnlp file and save in tmp"""
        avr_url = self._find_avr_url()
        resource = request.urlopen(request.Request(avr_url))
        xml_data = resource.read().decode('utf-8')
        _, tmppath = tempfile.mkstemp()
        with open(tmppath, 'w') as tmpfile:
            tmpfile.write(xml_data)
        return tmppath

    def console(self):
        self._install_auth()
        avr_file = self._save_tmp_jnlp()
        Popen(['/usr/bin/javaws', avr_file])
