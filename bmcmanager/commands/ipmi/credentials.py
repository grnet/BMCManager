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

from bmcmanager.commands.base import (
    BMCManagerServerCommand,
    BMCManagerServerGetCommand
)


class Get(BMCManagerServerGetCommand):
    """
    print IPMI credentials
    """
    oob_method = 'creds'


class Set(BMCManagerServerCommand):
    """
    change user IPMI password
    """
    oob_method = 'set_ipmi_password'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--secret-role', type=str, required=False,
            help='set the password as a NetBox secret with this role')
        parser.add_argument(
            '--new-password', type=str, required=True,
            help='new IPMI password')
        return parser
