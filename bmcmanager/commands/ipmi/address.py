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


def ipmi_address_arguments(parser):
    parser.add_argument(
        '--address-type', choices=['ipv4', 'mac'], required=True,
        help='address type')
    parser.add_argument(
        '--scheme', choices=['http', 'https', ''], default='https',
        help='scheme to prepend to the IPMI address')
    parser.add_argument(
        '--domain', help='domain name to append, only with address type "mac"')


class Get(BMCManagerServerGetCommand):
    """
    print IPMI address
    """
    oob_method = 'get_ipmi_address'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        ipmi_address_arguments(parser)
        return parser


class Refresh(BMCManagerServerCommand):
    """
    refresh IPMI address on DCIM
    """
    oob_method = 'refresh_ipmi_address'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        ipmi_address_arguments(parser)
        return parser
