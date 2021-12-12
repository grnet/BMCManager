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
import logging
import os

from oslo_config import cfg
from stevedore.extension import ExtensionManager


LOG = logging.getLogger(__name__)

CONF = cfg.ConfigOpts()

DEFAULT_OPTIONS = [
    cfg.ListOpt(name="available_dcims", default=[]),
    cfg.StrOpt(name="default_dcim"),
    cfg.StrOpt(name="fallback_oob", default="base"),
    cfg.DictOpt(name="oob_overrides", default={}),
]

CONF.register_opts(DEFAULT_OPTIONS)

DCIM_OPTIONS = [
    cfg.StrOpt(name="type", choices=ExtensionManager("bmcmanager.dcim").names()),
    # NetBox
    cfg.URIOpt(name="netbox_url", schemes=["http", "https"]),
    cfg.StrOpt(name="netbox_api_token", secret=True),
    cfg.IntOpt(name="netbox_api_timeout", default=10),
    cfg.StrOpt(name="netbox_session_key", secret=True),
    cfg.StrOpt(name="netbox_credentials_secret"),
    cfg.ListOpt(name="netbox_device_type_ids", item_type=int),
    # MaaS
    cfg.URIOpt(name="maas_api_url", schemes=["http", "https"]),
    cfg.StrOpt(name="maas_api_key", secret=True),
    cfg.URIOpt(name="maas_ui_url", schemes=["http", "https"]),
    # Local
    cfg.HostAddressOpt(name="local_ipmi_address"),
]

OOB_OPTIONS = [
    cfg.StrOpt("username"),
    cfg.StrOpt("password", secret=True),
    cfg.StrOpt("http_share"),
    cfg.StrOpt("nfs_share"),
    cfg.IntOpt("expected_psus", default=1, min=0),
    cfg.DictOpt("expected_firmware_versions", default={}),
]


def load_config(args: argparse.Namespace, OOBS):
    """
    Load configuration
    """

    if args.config_file:
        config_files = [args.config_file]
    else:
        config_files = [
            *cfg.find_config_files(project="bmcmanager"),
            os.path.expanduser("~/.config/bmcmanager.conf"),
            "bmcmanager.conf",
            "/etc/bmcmanager.conf",
            os.path.expandvars("$XDG_CONFIG_HOME/bmcmanager.conf"),
            os.path.expandvars("$XDG_CONFIG_HOME/.config/bmcmanager.conf"),
            os.path.expandvars("$SNAP_COMMON/bmcmanager.conf"),
            os.path.expandvars("$SNAP_COMMON/bmcmanager.conf"),
        ]
        config_files = [c for c in config_files if os.path.exists(c)]

    LOG.debug("Attempt to load configuration from %s", config_files)

    CONF(args=[], project="bmcmanager", default_config_files=config_files)

    # Dynamically register dcim groups
    for dcim_name in CONF.available_dcims:
        CONF.register_opts(DCIM_OPTIONS, group=dcim_name)

    # Setup OOB overrides
    for oob_name, oob_target in CONF.oob_overrides.items():
        OOBS[oob_name] = OOBS[oob_target]

    # Dynamically register OOB groups
    for oob_name in OOBS.keys():
        CONF.register_opts(OOB_OPTIONS, group=oob_name)

    if args.debug_config:
        CONF.log_opt_values(LOG, logging.DEBUG)

    return CONF
