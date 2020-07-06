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

import configparser
import os
import sys

from bmcmanager.logs import log


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

        log.debug('Loaded config from {}'.format(which))

    except configparser.ParsingError as e:
        log.error('Invalid configuration file: {}'.format(e))
        sys.exit(1)

    return format_config(config)
