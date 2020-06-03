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


import logging
import sys

from getpass import getpass

from bmcmanager.dcim.netbox import Netbox
from bmcmanager.oob.lenovo import Lenovo
from bmcmanager.oob.dell import Dell
from bmcmanager.oob.fujitsu import Fujitsu
from bmcmanager import exitcode


def get_password():
    return getpass('Please provide an IPMI password: ')


def get_username():
    return input('Please provide an IPMI username: ')


class BMCManager:
    COMMANDS = [
        'autoupdate',
        'boot-local',
        'boot-pxe',
        'check-disks',
        'check-firmware',
        'check-firmware-updates',
        'check-ipmi',
        'check-ram',
        'clear-autoupdate',
        'clear-firmware-upgrade-logs',
        'clear-ipmi-logs',
        'console',
        'controllers-status',
        'creds',
        'diagnostics',
        'firmware-upgrade',
        'flush-jobs',
        'get-disks',
        'get-firmware',
        'get-ipmi-address',
        'get-secrets',
        'idrac-info',
        'info',
        'ipmi-logs-analysed',
        'ipmi-logs',
        'ipmi-reset',
        'ipmi-sensors',
        'ipmi-ssh',
        'lenovo-rpc',
        'lock-power-switch',
        'open',
        'pdisks-status',
        'power-cycle',
        'power-off',
        'power-on',
        'power-reset',
        'power-status',
        'refresh-firmware',
        'refresh-ipmi-address',
        'set-ipmi-password',
        'set-secret',
        'ssh',
        'status',
        'storage-status',
        'system-ram',
        'unlock-power-switch',
        'upgrade',
    ]

    def __init__(self, command, identifier, rack, rack_unit, serial,
                 command_args, args, config, env_vars):
        if command not in self.COMMANDS:
            raise BMCManagerError('Invalid command')
        self.command = command
        self.identifier = identifier
        self.rack = rack
        self.rack_unit = rack_unit
        self.serial = serial
        self.args = args
        self.config = config
        self.env_vars = env_vars
        self.command_args = command_args

    def _dcim_table(self):
        return {
            'netbox': Netbox
        }

    def _oobs_table(self):
        return {
            'lenovo': Lenovo,
            'dell': Dell,
            'dell-inc': Dell,
            'fujitsu': Fujitsu
        }

    def _config_table(self):
        return {
            'lenovo': 'lenovo',
            'dell': 'dell',
            'dell-inc': 'dell',
            'fujitsu': 'fujitsu'
        }

    def _get_dcim(self):
        dcim = self.args.dcim.lower()
        dcim_params = self.config[dcim]
        try:
            dcim_class = self._dcim_table()[dcim]
            return dcim_class(self.identifier, self.rack, self.rack_unit,
                              self.serial, dcim_params)
        except KeyError:
            raise BMCManagerError('Not a valid DCIM')

    def _get_oob_params(self, oob, oob_info):
        config = {}
        try:
            oob_params = self.config[self._config_table()[oob.lower()]]
        except KeyError:
            raise BMCManagerError('Invalid OOB name {}'.format(oob))

        dcim = self._get_dcim()
        env_vars = self.env_vars

        if dcim.supports_secrets() and oob_params.get('credentials'):
            secret = dcim.get_secret(oob_params['credentials'], oob_info)
            config['username'] = secret['name']
            config['password'] = secret['plaintext']

        if config.get('username') is None:
            if self.args.username:
                config['username'] = self.args.username
            elif env_vars.get('username', None):
                config['username'] = env_vars['username']
            elif oob_params.get('username', None):
                config['username'] = oob_params['username']
            else:
                config['username'] = get_username()

        if config.get('password') is None:
            if self.args.password and self.args.password is not True:
                config['password'] = self.args.password
            elif self.args.password:
                config['password'] = get_password()
            elif oob_params.get('password', None):
                config['password'] = oob_params['password']
            else:
                config['password'] = get_password()

        config['nfs_share'] = None
        if env_vars.get('nfs_share', None):
            config['nfs_share'] = env_vars['nfs_share']
        elif oob_params.get('nfs_share', None):
            config['nfs_share'] = oob_params['nfs_share']

        config['http_share'] = None
        if env_vars.get('http_share', None):
            config['http_share'] = env_vars['http_share']
        elif oob_params.get('http_share', None):
            config['http_share'] = oob_params['http_share']

        config['oob_params'] = dict(oob_params)
        return config

    def _execute_command(self, dcim):
        for oob_info in dcim.get_oobs():
            oob = oob_info['oob']
            params = self._get_oob_params(oob, oob_info['info'])
            logging.info('Initiating OOB object for OOB {}'.format(oob))
            try:
                oob_obj = self._oobs_table()[oob](
                    self.command,
                    oob_info,
                    self.command_args,
                    username=params['username'],
                    password=params['password'],
                    nfs_share=params['nfs_share'],
                    http_share=params['http_share'],
                    force=self.args.force,
                    wait=self.args.wait,
                    oob_params=params['oob_params'],
                    dcim=dcim,
                )
            except KeyError:
                raise BMCManagerError('Not a valid OOB {}'.format(oob))
            command = self.command.replace('-', '_')
            logging.info('Executing command {} on OOB {}'.format(command, oob))

            try:
                getattr(oob_obj, command)()
            except Exception as e:
                logging.exception('Unhandled exception: {}'.format(e))

    def run(self):
        # Controller.
        # Needs to find the correct dcim and the correct oob
        logging.info('Initiating DCIM object')
        dcim = self._get_dcim()
        logging.info('Executing command')
        self._execute_command(dcim)
        logging.info('Done')

        sys.exit(exitcode.get())


class BMCManagerError(Exception):
    pass
