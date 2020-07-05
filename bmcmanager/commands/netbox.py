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


class ListSecrets(BMCManagerServerListCommand):
    """
    List available secrets from NetBox
    """
    dcim_fetch_secrets = False
    oob_method = 'get_secrets'


class SetSecret(BMCManagerServerCommand):
    """
    Set a secret on NetBox
    """
    dcim_fetch_secrets = False
    oob_method = 'set_secret'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('--secret-role', type=str, required=True)
        parser.add_argument('--secret-name', type=str, required=True)
        parser.add_argument('--secret-plaintext', type=str, required=True)
        return parser
