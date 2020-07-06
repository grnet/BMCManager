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


class PowerOn(BMCManagerServerCommand):
    """
    Power on server
    """
    oob_method = 'power_on'


class PowerOff(BMCManagerServerCommand):
    """
    Power off server
    """
    oob_method = 'power_off'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('--force', action='store_true', default=False)
        parser.add_argument('--wait', action='store_true', default=False)
        return parser


class PowerCycle(BMCManagerServerCommand):
    """
    Power cycle server
    """
    oob_method = 'power_cycle'


class PowerReset(BMCManagerServerCommand):
    """
    Power reset
    """
    oob_method = 'power_reset'


class PowerStatus(BMCManagerServerCommand):
    """
    Get server power status
    """
    oob_method = 'power_status'


class LockSwitch(BMCManagerServerCommand):
    """
    Lock power switch
    """
    oob_method = 'lock_power_switch'


class UnlockSwitch(BMCManagerServerCommand):
    """
    Unlock power switch
    """
    oob_method = 'unlock_power_switch'
