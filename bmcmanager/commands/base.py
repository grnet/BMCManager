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
import json
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

README = 'https://github.com/grnet/BMCManager/blob/master/README.md'


def int_in_range_argument(itt):
    """
    argparse integer in range
    """
    def argparse_type(value):
        ivalue = int(value)
        if ivalue not in itt:
            msg = '{} out of valid range [{}..{}]'.format(value, min(itt), max(itt))
            raise argparse.ArgumentTypeError(msg)
        return ivalue

    return argparse_type


def json_argument(arg):
    """
    argparse json argument type
    """
    try:
        return json.loads(arg)
    except json.JSONDecodeError as e:
        raise argparse.ArgumentTypeError('invalid JSON') from e


def base_arguments(parser):
    """
    Base bmcmanager arguments
    """
    parser.add_argument(
        '--config-file',
        help='configuration file path',
        default=''
    )


def server_arguments(parser):
    """
    Add server selection arguments
    """
    parser.add_argument(
        'server',
        help='server name'
    )
    parser.add_argument(
        '-d', '--dcim',
        help='name of DCIM to use',
        choices=['netbox'],
        default='netbox',
    )
    parser.add_argument(
        '-t', '--type',
        help='unit type',
        choices=['name', 'rack', 'rack-unit', 'serial'],
        default='search'
    )


def get_dcim(args, config):
    """
    Get a configured DCIM from arguments and configuration
    """
    if args.dcim not in DCIMS:
        raise RuntimeError(
            'Unsupported DCIM "{}", see {}'.format(args.dcim, README))
    if args.dcim not in config:
        raise RuntimeError(
            'No configuration for DCIM "{}", see {}'.format(args.dcim, README))
    return DCIMS[args.dcim](args, config[args.dcim])


def get_oob_config(config, dcim, oob_info, get_secret=True):
    """
    Get configuration for an OOB
    """
    oob_name = oob_info['oob'].lower()
    cfg = {}
    try:
        oob_params = config[oob_name]
    except KeyError:
        raise BMCManagerError('Invalid OOB name {}'.format(oob_name))

    if get_secret and dcim.supports_secrets() and 'credentials' in oob_params:
        secret = dcim.get_secret(oob_params['credentials'], oob_info)
        cfg['username'] = secret['name']
        cfg['password'] = secret['plaintext']
    else:
        cfg['username'] = oob_params['username']
        cfg['password'] = oob_params['password']

    cfg['username'] = os.getenv('BMCMANAGER_USERNAME', cfg['username'])
    cfg['password'] = os.getenv('BMCMANAGER_PASSWORD', cfg['password'])

    cfg['nfs_share'] = os.getenv(
        'BMCMANAGER_NFS_SHARE', oob_params.get('nfs_share'))
    cfg['http_share'] = os.getenv(
        'BMCMANAGER_HTTP_SHARE', oob_params.get('http_share'))

    cfg['oob_params'] = oob_params
    return cfg


def bmcmanager_take_action(cmd, parsed_args):
    cmd.parsed_args = parsed_args
    cmd.config = get_config(parsed_args.config_file)
    dcim = get_dcim(parsed_args, cmd.config)

    for oob_info in dcim.get_oobs():
        oob_config = get_oob_config(cmd.config, dcim, oob_info)
        log.debug('Creating OOB object for {}'.format(oob_info['oob']))
        try:
            oob = OOBS.get(oob_info['oob'])(parsed_args, dcim, oob_config, oob_info)
        except KeyError:
            raise BMCManagerError('Invalid OOB {}'.format(oob_info['oob']))

        try:
            if hasattr(cmd, 'oob_method'):
                return getattr(oob, cmd.oob_method)()
            else:
                return cmd.action(oob)
        except Exception as e:
            log.exception('Unhandled exception: {}'.format(e))
    else:
        log.fatal('No servers found for "{}"'.format(parsed_args.server))
        return [], []


class BMCManagerServerCommand(Command):
    """
    base command for working with a server
    """
    dcim_fetch_secrets = True

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        base_arguments(parser)
        server_arguments(parser)
        return parser

    def take_action(self, parsed_args):
        bmcmanager_take_action(self, parsed_args)
        sys.exit(exitcode.get())

    def action(self, oob):
        raise NotImplementedError


class BMCManagerServerGetCommand(ShowOne):
    """
    base command for retrieving information for a server
    """
    dcim_fetch_secrets = True

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        base_arguments(parser)
        server_arguments(parser)
        return parser

    def take_action(self, parsed_args):
        return bmcmanager_take_action(self, parsed_args)

    def action(self, oob):
        raise NotImplementedError


class BMCManagerServerListCommand(Lister):
    """
    base command for retrieving a list of information for a server
    """
    dcim_fetch_secrets = True

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        base_arguments(parser)
        server_arguments(parser)
        return parser

    def take_action(self, parsed_args):
        return bmcmanager_take_action(self, parsed_args)

    def action(self, oob):
        raise NotImplementedError
