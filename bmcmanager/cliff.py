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

import sys

from cliff.app import App
from cliff.commandmanager import CommandManager


class BMCManagerApp(App):
    def __init__(self):
        super(BMCManagerApp, self).__init__(
            description='BMCManager',
            version='1.0.1',
            command_manager=CommandManager('bmcmanager.entrypoints'),
            deferred_help=True
        )


def main(argv=sys.argv[1:]):
    m = BMCManagerApp()
    return m.run(argv)


if __name__ == '__main__':
    sys.exit(main())
