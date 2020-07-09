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

from bmcmanager.commands.base import BMCManagerServerCommand, BMCManagerServerListCommand


class Get(BMCManagerServerListCommand):
    """
    print system event logs
    """
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--analysed', action='store_true', default=False,
            help='decode OEM specific fields')
        return parser

    def action(self, oob):
        if self.parsed_args.analysed:
            return oob.ipmi_logs_analysed()
        else:
            return oob.ipmi_logs()


class Clear(BMCManagerServerCommand):
    """
    clear system event logs
    """
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--from-firmware-upgrades', action='store_true', default=False,
            help='clear logs from firmware upgrades only')
        return parser

    def action(self, oob):
        if self.parsed_args.from_firmware_upgrades:
            oob.clear_firmware_upgrade_logs()
        else:
            oob.clear_ipmi_logs()
