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

import argparse
import os
import sys
import urllib.request
from subprocess import call, CalledProcessError

from cliff.lister import Lister

from bmcmanager.commands.base import (
    BMCManagerServerCommand,
    BMCManagerServerListCommand,
    int_in_range_argument
)
from bmcmanager.logs import log
from bmcmanager.firmwares import firmware_fetchers


class Get(BMCManagerServerListCommand):
    """
    print server firmware versions
    """
    oob_method = 'get_firmware'


class Refresh(BMCManagerServerCommand):
    """
    update server firmware information on DCIM
    """
    oob_method = 'refresh_firmware'


class Check(BMCManagerServerCommand):
    """
    check server firmware version [Nagios]
    """
    oob_method = 'check_firmware'
    dcim_fetch_secrets = False


class UpgradeRPC(BMCManagerServerCommand):
    """
    perform firmware upgrade using RPC
    """
    oob_method = 'firmware_upgrade_rpc'
    all_stages = range(1, 11)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--timeout', type=int, default=60,
            help='advanced; seconds before failing because of timeout')
        parser.add_argument(
            '--handle', type=int, default=None,
            help='advanced; Use this handle for upgrade [Lenovo]')
        parser.add_argument(
            '--bundle', required=True, type=argparse.FileType('rb'),
            help='Bundle file to use for firmware upgrade')
        parser.add_argument(
            '--stages', nargs='+', default=self.all_stages,
            type=int_in_range_argument(self.all_stages),
            help='advanced; Only perform specific upgrade stages [Lenovo]')

        return parser


class UpgradeOsput(BMCManagerServerCommand):
    """
    perform firmware upgrade using osput [Lenovo]
    """
    oob_method = 'firmware_upgrade_osput'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--osput', type=str, default='osput',
            help='override path to the `osput` executable [lenovo]')
        parser.add_argument(
            '--bundle', type=str, required=True,
            help='bundle file to use for firmware upgrade')
        return parser


class Latest(Lister):
    """
    print and download latest firmware version bundles
    """
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'model', choices=firmware_fetchers.keys(),
            help='server model for which to look for new firwmare')
        parser.add_argument(
            '--download-to',
            help='download available firmware files to this location')
        parser.add_argument(
            '--innoextract', action='store_true',
            help='extract `.exe` files using innoextract')
        return parser

    def _execute_cmd(self, command):
        log.debug('Executing {}'.format(' '.join(command)))
        try:
            call(command)
        except CalledProcessError as e:
            raise RuntimeError('Command {} failed: {}'.format(
                ' '.join(command), str(e)))

    def take_action(self, parsed_args):
        try:
            fetcher = firmware_fetchers[parsed_args.model]

        except KeyError as e:
            log.error('Unsupported device type: {}'.format(e))
            sys.exit(-1)

        result, downloads = fetcher().get()

        columns = ['component', 'name', 'version', 'date']
        values = [[item[col] for col in columns] for item in result]

        if parsed_args.download_to is None:
            return columns, values

        try:
            os.makedirs(parsed_args.download_to, exist_ok=True)
        except OSError as e:
            log.error('Could not create download directory: {}'.format(e))
            sys.exit(-1)

        for url in downloads:
            name = url[url.rfind('/') + 1:]
            file_name = os.path.join(parsed_args.download_to, name)
            log.info('Downloading {} to {}'.format(url, file_name))
            try:
                with open(file_name, 'wb') as fout:
                    fout.write(urllib.request.urlopen(url).read())
            except (urllib.error.URLError, OSError) as e:
                log.error('Failed: {}'.format(e))

            if parsed_args.innoextract and name.endswith('.exe'):
                log.info('Extracting with innoextract')
                self._execute_cmd([
                    'innoextract', file_name, '-d', parsed_args.download_to])

        return columns, values
