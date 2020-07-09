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
    get_dcim, get_config, BMCManagerServerListCommand)


class List(BMCManagerServerListCommand):
    """
    print list of available servers
    """
    columns = [
        'id', 'name', 'site', 'serial', 'manufacturer', 'device_type', 'status']

    def take_action(self, parsed_args):
        dcim = get_dcim(parsed_args, get_config(parsed_args.config_file))
        values = [[o['info'][col] for col in self.columns] for o in dcim.get_oobs()]

        return self.columns, values
