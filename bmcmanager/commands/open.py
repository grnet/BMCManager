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

from bmcmanager.commands.base import BMCManagerServerCommand


class DCIM(BMCManagerServerCommand):
    """
    open server page on DCIM
    """
    dcim_fetch_secrets = False
    oob_method = 'open_dcim'


class Web(BMCManagerServerCommand):
    """
    open IPMI web interface
    """
    oob_method = 'open'
    dcim_fetch_secrets = False


class Console(BMCManagerServerCommand):
    """
    open console
    """
    oob_method = 'console'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--print-cmd', action='store_true', default=False,
            help='orint the command instead of opening the console')
        return parser
