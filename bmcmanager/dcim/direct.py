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


from bmcmanager.dcim.base import DcimBase


class Direct(DcimBase):
    def __init__(self, args, config):
        super(Direct, self).__init__(args, config)

        self.identifier
        self.username = self.config.get('username')
        self.password = self.config.get('password')

        self.info = {
            'ipmi': self.identifier,
            'identifier': self.identifier,
            'info': {},
            'oob': self.config.get('oob')
        }

    def get_info(self):
        return self.info

    def get_oobs(self):
        return [{
            'asset_tag': 'unknown',
            'ipmi': self.identifier,
            'oob': self.config.get('oob'),
            'info': {
                'ipmi': self.identifier,
            },
            'identifier': self.identifier,
            'custom_fields': {},
        }]

    def set_custom_fields(self, oob_info, custom_fields):
        return False

    def oob_url(self, oob_info):
        return oob_info['ipmi']
