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

from bmcmanager.commands.base import BMCManagerServerCommand, BMCManagerServerGetCommand


class SSH(BMCManagerServerCommand):
    """
    connect to server with SSH
    """
    oob_method = 'ssh'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--wait', action='store_true', default=False,
            help='wait for server to turn on before starting SSH shell')
        return parser


class FlushJobs(BMCManagerServerCommand):
    """
    flush server pending jobs
    """
    oob_method = 'flush_jobs'


class Identify(BMCManagerServerCommand):
    """
    turn server identifier LED on/off
    """
    oob_method = 'identify'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--on', nargs='?', type=int, default=15,
            help='turn on identifier LED')
        group.add_argument(
            '--off', action='store_true', default=False,
            help='turn off identifier LED')
        return parser


class Diagnostics(BMCManagerServerCommand):
    """
    print server diagnostics
    """
    oob_method = 'diagnostics'


class Info(BMCManagerServerGetCommand):
    """
    print server info
    """
    oob_method = 'info'


class Upgrade(BMCManagerServerCommand):
    """
    upgrade server
    """
    oob_method = 'upgrade'


class IdracInfo(BMCManagerServerCommand):
    """
    print idrac info
    """
    oob_method = 'idrac_info'
