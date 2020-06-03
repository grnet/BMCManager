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
import configparser
import logging
import os
import sys

from bmcmanager.bmcmanager import BMCManager


def setup_logging(verbosity):
    level_list = [logging.WARN, logging.INFO, logging.DEBUG]
    if len(level_list) < verbosity - 1:
        print('Invalid verbosity')
        sys.exit(1)

    level = level_list[verbosity]
    logging.basicConfig(level=level)


def format_config(config):
    # Recursive function that converts a
    # configparser.ConfigParser object into a dict
    # this basically recursivelly calls dict() on every subdict
    # TODO: refactor
    keys = dict(config).keys()
    formatted = {}
    for k in keys:
        formatted[k.lower()] = config[k]
        if not type(config[k]) == str:
            formatted[k.lower()] = format_config(config[k])
    return formatted


def get_config(config_path):
    try:
        extra_paths = []
        if os.getenv('SNAP_COMMON'):
            extra_paths.extend([os.path.expandvars('$SNAP_COMMON/bmcmanager')])

        if os.getenv('XDG_CONFIG_HOME'):
            extra_paths.extend([
                os.path.expandvars('$XDG_CONFIG_HOME/.config/bmcmanager'),
                os.path.expandvars('$XDG_CONFIG_HOME/bmcmanager')])

        config = configparser.ConfigParser()
        which = config.read([
            config_path,
            os.getenv('BMCMANAGER_CONFIG', ''),
            os.path.expanduser('~/.config/bmcmanager'),
            '/etc/bmcmanager',
            *extra_paths,
        ])

        logging.debug('Loaded config from {}'.format(which))

    except configparser.ParsingError as e:
        print('Invalid configuration file: {}'.format(e))
        sys.exit(1)

    return format_config(config)


def get_environment_variables():
    # Read environment variables regarding
    # whatever the config file might include
    env_vars = {}
    if os.environ.get('BMCMANAGER_USERNAME', None):
        env_vars['username'] = os.environ['BMCMANAGER_USERNAME']

    if os.environ.get('BMCMANAGER_PASSWORD', None):
        env_vars['password'] = os.environ['BMCMANAGER_PASSWORD']

    if os.environ.get('BMCMANAGER_NFS_SHARE', None):
        env_vars['nfs_share'] = os.environ['BMCMANAGER_NFS_SHARE']

    if os.environ.get('BMCMANAGER_HTTP_SHARE', None):
        env_vars['http_share'] = os.environ['BMCMANAGER_http_SHARE']

    return env_vars


def main():
    # 1. Configuration:
    #   - If config file exists, use it
    #   - If system-wide config file exists, use it
    #   - Else if environment variables exist use those
    #   - Else if command line arguments exist, use those
    #   - Else prompt the user for variables
    # 2. Initialize a BMCManager object
    # 3. call bmcm.run()
    parser = argparse.ArgumentParser(epilog='Available commands: {}'.format(
        ', '.join(sorted(BMCManager.COMMANDS))))
    parser.add_argument(
        'command',
        help='Command which will be executed'
    )
    parser.add_argument(
        'identifier',
        help='Identifier for the machine which the command will be executed',
        default=None
    )
    parser.add_argument(
        '-c',
        '--config',
        action='store',
        help='Configuration file path',
        default=''
    )
    parser.add_argument(
        '-u',
        '--username',
        action='store',
        help='IPMI username',
        default=None
    )
    parser.add_argument(
        '-p',
        '--password',
        action='store_true',
        help='IPMI password',
        default=None
    )
    parser.add_argument(
        '-f',
        '--force',
        action='store_true',
        help='Force',
        default=None
    )
    parser.add_argument(
        '-w',
        '--wait',
        action='store_true',
        help='Wait',
        default=None
    )
    parser.add_argument(
        '-d',
        '--dcim',
        help='DCIM name',
        default='netbox'
    )
    parser.add_argument(
        '-r',
        '--rack',
        help='Rack name',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '-a',
        '--rack-unit',
        help='Rack unit',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '-s',
        '--serial',
        help='Serial name',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help='Sets logging to INFO for -v and DEBUG for -vv',
        action='count',
        default=0
    )
    args, command_args = parser.parse_known_args()

    if len([x for x in [args.serial, args.rack, args.rack_unit] if x]) > 1:
        print('Cannot use rack, rack unit and serial flags concurrently')
        sys.exit(1)

    setup_logging(args.verbose)
    config = get_config(args.config)
    env_vars = get_environment_variables()

    bmcm = BMCManager(args.command, args.identifier, args.rack, args.rack_unit,
                      args.serial, command_args, args, config, env_vars)
    bmcm.run()


if __name__ == '__main__':
    main()
