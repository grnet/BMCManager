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


class DcimBase(object):
    """
    Base DCIM class
    """
    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.identifier = args.server
        self.dcim_params = config
        self.api_url = config['api_url']
        self.is_rack = self.args.type == 'rack'
        self.is_rack_unit = self.args.type == 'rack-unit'
        self.is_serial = self.args.type == 'serial'

    def get_info(self):
        raise NotImplementedError('get_info not implemented')

    def get_oobs(self):
        raise NotImplementedError('get_oobs not implemented')

    def oob_url(self):
        raise NotImplementedError

    def supports_secrets(self):
        return getattr(self, 'get_secret') is not None

    def set_custom_fields(self, oob_info, custom_fields):
        return False


class DcimError(Exception):
    pass
