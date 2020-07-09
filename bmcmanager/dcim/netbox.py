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
import os

import requests

from bmcmanager.logs import log
from bmcmanager.dcim.base import DcimBase, DcimError


class Netbox(DcimBase):
    def __init__(self, args, config):
        super(Netbox, self).__init__(args, config)

        self.timeout = 10
        try:
            timeout = self.dcim_params.get('timeout', self.timeout)
            self.timeout = int(timeout)
        except (TypeError, ValueError):
            log.warning('Ignoring invalid timeout: {}'.format(timeout))

        self.device_type_ids = None
        raw_ids = self.dcim_params.get('device_type_id')
        if raw_ids is not None:
            try:
                # '1, 3,2' --> [1, 2, 3]
                self.device_type_ids = list(
                    map(int, map(str.strip, raw_ids.split(','))))
            except (TypeError, ValueError):
                log.warning('Ignoring invalid device type ids: {}'.format(
                    raw_ids))

        self.info = self._retrieve_info()

    def _get_params(self):
        if self.is_serial:
            return {'serial': self.identifier}
        elif self.is_rack_unit:
            return {'name': self.identifier}
        elif self.is_rack:
            return {'rack_id': self._get_rack_id()}

        params = {'q': self.identifier}
        if self.device_type_ids is not None:
            params['device_type_id'] = self.device_type_ids
        return params

    def _get_rack_id(self):
        log.debug('Querying the Netbox API for rack {}'.format(
            self.identifier))
        url = os.path.join(self.api_url, 'api/dcim/racks/')
        params = {'name': self.identifier}
        json_response = self._do_request(url, params)

        log.debug('Decoding the response')
        # we expect the response to be a json object
        response = json_response.json()
        if len(response['results']) != 1:
            raise DcimError('Did not find valid results for rack {}'.format(
                self.identifier))
        return response['results'][0]['id']

    def _get_headers(self, with_session_key=False):
        headers = {'Accept': 'application/json'}

        token = self.dcim_params.get('netbox_token')
        if token is not None:
            headers.update({'Authorization': 'Token {}'.format(token)})

        if with_session_key:
            session_key = self.dcim_params.get('session_key')
            if session_key is not None:
                headers.update({'X-Session-Key': session_key})

        return headers

    def _do_request(self, url, params, with_session_key=False, method='get'):
        headers = self._get_headers(with_session_key)

        log.debug('HTTP {} {}, {}, {}'.format(
            method.upper(), url, str(params), str(headers)))
        try:
            f = getattr(requests, method)
            return f(url, params=params, headers=headers, timeout=self.timeout)
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError):
            # useful instead of a long exception dump
            sys.stderr.write('Request timed out {}'.format(url))
            exit(1)

    def _retrieve_info(self):
        log.debug('Querying the Netbox API for {}'.format(self.identifier))
        url = os.path.join(self.api_url, 'api/dcim/devices/')
        params = self._get_params()
        params['limit'] = 0
        json_response = self._do_request(url, params)
        log.debug('Decoding the response')
        # we expect the response to be a json object
        return json_response.json()

    def get_short_info(self, result):
        return {
            'id': result['id'],
            'name': result['name'],
            'display_name': result['display_name'],
            'serial': result['serial'],
            'ipmi': result['custom_fields']['IPMI'] or 'unknown-address',
            'manufacturer': result['device_type']['manufacturer']['slug'],
            'device_type': result['device_type']['slug'],
            'bios': result['custom_fields']['BIOS'],
            'tsm': result['custom_fields']['TSM'],
            'psu': result['custom_fields']['PSU'],
            'site': result['site']['name'],
            'status': result['status']['label'],
        }

    def get_info(self):
        return self.info

    def get_oobs(self):
        for result in self.info['results']:
            yield {
                'asset_tag': result['asset_tag'],
                'ipmi': result['custom_fields']['IPMI'],
                'oob': result['device_type']['manufacturer']['slug'],
                'info': self.get_short_info(result),
                'identifier': result['name'],
                'custom_fields': result['custom_fields'],
            }

    def get_secret(self, role, oob_info):
        device = oob_info['info']['name']
        log.debug('Querying secret {} of device {}'.format(role, device))
        response = self._do_request(
            url=os.path.join(self.api_url, 'api/secrets/secrets/'),
            params={'role': role, 'device': device.upper()},
            with_session_key=True)

        try:
            return response.json()['results'][0]

        except (TypeError, KeyError, IndexError):
            log.warning('Did not find secret {} for device {}'.format(
                role, device))
            return {
                'name': None,
                'plaintext': None,
            }

    def _get_secret_role_id(self, role_name):
        log.debug('Searching for id of secret role {}'.format(role_name))
        response = self._do_request(
            url=os.path.join(self.api_url, 'api/secrets/secret-roles/'),
            params={'slug': role_name}
        )

        try:
            return response.json()['results'][0]['id']
        except (TypeError, KeyError, IndexError):
            return None

    def set_secret(self, role_name, oob_info, secret_name, secret_text):
        log.debug('Will upsert secret {} for device {}'.format(
            role_name, oob_info['name']))

        role_id = self._get_secret_role_id(role_name)
        if role_id is None:
            log.critical('unknown role slug {}'.format(role_name))

        url = os.path.join(self.api_url, 'api/secrets/secrets/')
        f = requests.post

        existing_secrets = self.get_secrets(oob_info)
        for s in existing_secrets:
            if s['role'] == role_name and s['name'] == secret_name:
                log.debug('Updating secret with role {} and name {}'.format(
                    role_name, secret_name))
                url = os.path.join(url, '{}/'.format(s['id']))
                f = requests.patch
                break

        return f(
            url=url,
            headers=self._get_headers(with_session_key=True),
            json={
                'device': oob_info['id'],
                'role': role_id,
                'name': secret_name,
                'plaintext': secret_text,
            },
        )

    def _get_secrets(self, oob_info):
        log.debug('Searching for secrets of device {}'.format(
            oob_info['name']))

        response = self._do_request(
            url=os.path.join(self.api_url, 'api/secrets/secrets/'),
            params={
                'device': oob_info['name'],
            },
            with_session_key=True
        )

        return response

    def get_secrets(self, oob_info):
        resp = self._get_secrets(oob_info)
        try:
            return [{
                'id': s['id'],
                'name': s['name'],
                'role': s['role']['slug'],
                'plaintext': s['plaintext'],
            } for s in resp.json()['results']]
        except (KeyError, ValueError, TypeError):
            return []

    def set_custom_fields(self, oob_info, custom_fields):
        return requests.patch(
            url=os.path.join(self.api_url, 'api/dcim/devices/{}/'.format(oob_info['info']['id'])),
            headers=self._get_headers(),
            json={
                'custom_fields': custom_fields,
            },
        ).status_code == 200

    def oob_url(self, oob_info):
        return os.path.join(self.api_url, 'dcim/devices/{}/'.format(oob_info['info']['id']))
