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

from maas.client.bones import SessionAPI

from bmcmanager.logs import log
from bmcmanager.dcim.base import DcimBase, DcimError


class MaaS(DcimBase):
    def __init__(self, args, config):
        super(MaaS, self).__init__(args, config)
        self._session = None

        if not self.dcim_params['api_url']:
            raise DcimError('MaaS API URL is not set, see README.md')
        if not self.dcim_params['api_key']:
            raise DcimError('MaaS API Key is not set, see README.md')

        self.api_url = self.dcim_params['api_url']
        self.api_key = self.dcim_params['api_key']

    def session(self) -> SessionAPI:
        """
        Return a sessions to the MaaS server. Subsequent calls reuse the same
        connection
        """
        if self._session:
            return self._session

        log.info(f'Connecting to {self.api_url}')
        _, self._session = SessionAPI.connect(self.api_url, apikey=self.api_key)

        return self._session

    def get_oobs(self):
        for machine in self.session().Machines.read(hostname=[self.identifier]):
            power = self.session().Machine.power_parameters(system_id=machine['system_id'])
            yield {
                'asset_tag': '',
                'ipmi': power['power_address'],
                'oob': machine['hardware_info']['mainboard_vendor'].lower(),
                'info': {
                    'id': machine['system_id'],
                    'name': machine['hostname'],
                    'display_name': machine['hostname'],
                    'serial': machine['hardware_info']['system_serial'],
                    'ipmi': power['power_address'],
                    'manufacturer': machine['hardware_info']['mainboard_vendor'],
                    'device_type': machine['hardware_info']['mainboard_product'],
                    'bios': machine['owner_data'].get('BIOS', ''),
                    'tsm': machine['owner_data'].get('TSM', ''),
                    'psu': machine['owner_data'].get('PSU', ''),
                    'site': machine['domain']['name'],
                    'status': machine['status_name'],
                },
                'identifier': machine['hostname'],
                'custom_fields': machine['owner_data'],
            }

    def get_secret(self, role, oob_info):
        power = self.session().Machine.power_parameters(system_id=oob_info['info']['id'])
        return {
            'name': power['power_user'],
            'plaintext': power['power_pass'],
        }

    def set_custom_fields(self, oob_info, custom_fields):
        raise DcimError('not support by MaaS DCIM')

    def oob_url(self, oob_info):
        if not self.dcim_params.get('ui_url'):
            raise DcimError('MaaS UI URL is not set, see README.md')
        return '{}/MAAS/l/machine/{}'.format(
            self.dcim_params['ui_url'], oob_info['info']['id'])
