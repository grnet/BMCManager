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

import socket

from bmcmanager.dcim.base import DcimBase


class Local(DcimBase):
    """
    Local DCIM class.
    """

    def get_oobs(self):
        return [
            {
                "asset_tag": "",
                "ipmi": "",
                "oob": "unknown",
                "info": {
                    "id": socket.gethostname(),
                    "name": socket.gethostname(),
                    "display_name": socket.gethostname(),
                    "serial": "N/A",
                    "ipmi": "",
                    "manufacturer": "unknown",
                    "device_type": "",
                    "bios": "",
                    "tsm": "",
                    "psu": "",
                    "site": "",
                    "status": "up",
                },
                "identifier": socket.gethostname(),
                "custom_fields": {},
            }
        ]

    def oob_url(self):
        raise NotImplementedError("oob_url is not available")

    def supports_secrets(self):
        return False

    def set_custom_fields(self, oob_info, custom_fields):
        return False

    def format_ipmitool_credentials(self, host, username, password):
        # TODO: host, username, password should not be an argument
        return []

    def format_freeipmi_credentials(self, host, username, password):
        # TODO: host, username, password should not be an argument
        return []
