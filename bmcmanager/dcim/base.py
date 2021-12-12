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

from typing import List

from bmcmanager.config import CONF


class DcimBase(object):
    """
    Base DCIM class
    """

    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.config = CONF[name]
        self.identifier = args.server

    def get_oobs(self):
        raise NotImplementedError("get_oobs not implemented")

    def oob_url(self):
        raise NotImplementedError

    def supports_secrets(self):
        return getattr(self, "get_secret") is not None

    def set_custom_fields(self, oob_info, custom_fields):
        return False

    def format_ipmitool_credentials(self, oob_info) -> List[str]:
        host, username, password = self.get_ipmi_credentials(oob_info)
        return [
            "-H",
            host.replace("https://", ""),
            "-U",
            username,
            "-P",
            password,
            "-I",
            "lanplus",
        ]

    def format_freeipmi_credentials(self, oob_info) -> List[str]:
        host, username, password = self.get_ipmi_credentials(oob_info)
        return [
            "-h",
            host.replace("https://", ""),
            "-u",
            username,
            "-p",
            password,
            "-l",
            "user",
            "--driver-type=LAN_2_0",
        ]

    def get_ipmi_credentials(self, oob_info):
        """
        Return IPMI credentials (or default ones from OOB configuration)
        """
        host, username, password = self.get_ipmi_credentials_from_dcim(oob_info)
        if not host:
            host = oob_info["ipmi"]
        if not username:
            username = CONF[oob_info["oob"].lower()].username
        if not password:
            password = CONF[oob_info["oob"].lower()].password

        return host, username, password

    def get_ipmi_credentials_from_dcim(self, oob_info):
        """
        Return IPMI credentials from DCIM. Subclasses should implement this.
        """
        raise NotImplementedError()


class DcimError(Exception):
    pass
