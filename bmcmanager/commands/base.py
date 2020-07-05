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

import os
import sys

from cliff.command import Command
from cliff.show import ShowOne
from cliff.lister import Lister

from bmcmanager.config import get_config
from bmcmanager.dcim import DCIMS
from bmcmanager.oob import OOBS
from bmcmanager.errors import BMCManagerError
from bmcmanager.logs import log
from bmcmanager import exitcode


def base_arguments(parser):
    """
    Base bmcmanager arguments
    """
    parser.add_argument(
        '--config',
        help='Configuration file path',
        default=''
    )


def server_arguments(parser):
    """
    Add server selection arguments
    """
    parser.add_argument(
        'server',
        help='Server name'
    )
    parser.add_argument(
        '-d', '--dcim',
        help='DCIM name',
        choices=['netbox'],
        default='netbox'
    )
    parser.add_argument(
        '-t', '--type',
        help='Server type',
        choices=['name', 'rack', 'rack-unit', 'serial'],
        default='search'
    )


def get_dcim(args, config):
    """
    Get a configured DCIM from arguments and configuration
    """
    return DCIMS[args.dcim](args, config[args.dcim])


def get_oob_config(config, dcim, oob_info):
    """
    Get configuration for an OOB
    """
    oob_name = oob_info['oob'].lower()
    oob_config = {}
    try:
        oob_params = config[oob_name]
    except KeyError:
        raise BMCManagerError('Invalid OOB name {}'.format(oob_name))

    if dcim.supports_secrets() and 'credentials' in oob_params:
        secret = dcim.get_secret(oob_params['credentials'], oob_info)
        oob_config['username'] = secret['name']
        oob_config['password'] = secret['plaintext']
    else:
        oob_config['username'] = oob_params['username']
        oob_config['password'] = oob_params['password']

    oob_config['nfs_share'] = os.getenv(
        'BMCMANAGER_NFS_SHARE', oob_params.get('nfs_share'))
    oob_config['http_share'] = os.getenv(
        'BMCMANAGER_HTTP_SHARE', oob_params.get('http_share'))

    oob_config['oob_params'] = oob_params
    return oob_config


class BMCManagerServerCommand(Command):
    """
    Base command for working with a server
    """
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        base_arguments(parser)
        server_arguments(parser)
        return parser

    def take_action(self, parsed_args):
        self.parsed_args = parsed_args
        self.config = get_config(parsed_args.config)
        dcim = get_dcim(parsed_args, self.config)

        for oob_info in dcim.get_oobs():
            oob_config = get_oob_config(self.config, dcim, oob_info)
            log.debug('Creating OOB object for {}'.format(oob_info['oob']))
            try:
                oob = OOBS.get(oob_info['oob'])(parsed_args, dcim, oob_config, oob_info)
            except KeyError:
                raise BMCManagerError('Invalid OOB {}'.format(oob_info['oob']))

            try:
                if hasattr(self, 'oob_method'):
                    getattr(oob, self.oob_method)()
                else:
                    self.action(oob)

                sys.exit(exitcode.get())
            except Exception as e:
                log.exception('Unhandled exception: {}'.format(e))

    def action(self, oob):
        raise NotImplementedError


class BMCManagerServerGetCommand(ShowOne):
    """
    Base command for retrieving information for a server
    """
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        base_arguments(parser)
        server_arguments(parser)
        return parser

    def take_action(self, parsed_args):
        self.parsed_args = parsed_args
        self.config = get_config(parsed_args.config)
        dcim = get_dcim(parsed_args, self.config)

        for oob_info in dcim.get_oobs():
            oob_config = get_oob_config(self.config, dcim, oob_info)
            log.debug('Creating OOB object for {}'.format(oob_info['oob']))
            try:
                oob = OOBS.get(oob_info['oob'])(parsed_args, dcim, oob_config, oob_info)
            except KeyError:
                raise BMCManagerError('Invalid OOB {}'.format(oob_info['oob']))

            try:
                if hasattr(self, 'oob_method'):
                    return getattr(oob, self.oob_method)()
                else:
                    return self.action(oob)

                sys.exit(exitcode.get())
            except Exception as e:
                log.exception('Unhandled exception: {}'.format(e))

    def action(self, oob):
        raise NotImplementedError


class BMCManagerServerListCommand(Lister):
    """
    Base command for retrieving a list of information for a server
    """
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        base_arguments(parser)
        server_arguments(parser)
        return parser

    def take_action(self, parsed_args):
        self.parsed_args = parsed_args
        self.config = get_config(parsed_args.config)
        dcim = get_dcim(parsed_args, self.config)

        for oob_info in dcim.get_oobs():
            oob_config = get_oob_config(self.config, dcim, oob_info)
            log.debug('Creating OOB object for {}'.format(oob_info['oob']))
            try:
                oob = OOBS.get(oob_info['oob'])(parsed_args, dcim, oob_config, oob_info)
            except KeyError:
                raise BMCManagerError('Invalid OOB {}'.format(oob_info['oob']))

            try:
                if hasattr(self, 'oob_method'):
                    return getattr(oob, self.oob_method)()
                else:
                    return self.action(oob)

                sys.exit(exitcode.get())
            except Exception as e:
                log.exception('Unhandled exception: {}'.format(e))

    def action(self, oob):
        raise NotImplementedError
