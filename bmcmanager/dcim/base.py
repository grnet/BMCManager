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
    # All dcims inherit this class
    # Defines the interface for dcims
    # and implements basic functionality
    def __init__(self, identifier, is_rack, is_rack_unit, is_serial,
                 dcim_params):
        self.identifier = identifier
        self.dcim_params = dcim_params
        self.api_url = self.dcim_params['api_url']
        self.is_rack = is_rack
        self.is_rack_unit = is_rack_unit
        self.is_serial = is_serial

    def get_info(self):
        raise NotImplementedError('get_info not implemented')

    def get_oobs(self):
        raise NotImplementedError('get_oobs not implemented')

    def supports_secrets(self):
        return getattr(self, 'get_secret') is not None

    def set_custom_fields(self, oob_info, custom_fields):
        return False


class DcimError(Exception):
    pass
