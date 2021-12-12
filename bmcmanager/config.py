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
    cfg.ListOpt(
        name="available_dcims",
        default=[],
        help="List of configured DCIMs. For each DCIM, create a new [$dcim] section"
        "and configure options from the `dcim_options` group.",
        sample_default="netbox, maas",
    ),
    cfg.StrOpt(
        name="default_dcim",
        help="Name of DCIM to use when none is specified in the command line",
        sample_default="netbox",
    ),
    cfg.StrOpt(
        name="fallback_oob",
        default="base",
        help="Default OOB implementation to use if manufacturer is not supported.",
        sample_default="base",
    ),
    cfg.DictOpt(
        name="oob_overrides",
        default={},
        help="Mapping of OOB implementation overrides.",
        sample_default="hp:base",
    ),
]

CONF.register_opts(DEFAULT_OPTIONS)

DCIM_OPTIONS = [
    cfg.StrOpt(
        name="type",
        choices=ExtensionManager("bmcmanager.dcim").names(),
        help="Type of DCIM. Depending on the type you choose, configure the "
        "appropriate options below",
        sample_default="netbox",
    ),
    # NetBox
    cfg.URIOpt(
        name="netbox_url",
        schemes=["http", "https"],
        help="Root URL of your NetBox deployment",
        sample_default="https://netbox.example.com/",
    ),
    cfg.StrOpt(
        name="netbox_api_token",
        secret=True,
        help="Token for NetBox API requests. May not be needed if NetBox does "
        "not require authentication for read-only access",
        sample_default="2eaf86dcfec8f43d59a7ae89d337ebb3fe7fe4e3",
    ),
    cfg.IntOpt(
        name="netbox_api_timeout",
        default=10,
        help="Timeout for NetBox API calls (in seconds)",
    ),
    cfg.StrOpt(
        name="netbox_session_key",
        secret=True,
        help="Session Key for retrieving secrets from the NetBox API. This is "
        "needed when using secrets for IPMI credentials",
        sample_default="Se/wfMUmhfq5el3XA8asorsfArQ=",
    ),
    cfg.StrOpt(
        name="netbox_credentials_secret",
        help="Name of secret which contains IPMI credentials for the server",
        sample_default="ipmi-credentials",
    ),
    cfg.ListOpt(
        name="netbox_device_type_ids",
        item_type=int,
        help="Limit requests to specific device type IDs.",
        sample_default="[1, 32]",
    ),
    # MaaS
    cfg.URIOpt(
        name="maas_api_url",
        schemes=["http", "https"],
        help="MaaS API URL",
        sample_default="http://maas:5240/MAAS/api/2.0",
    ),
    cfg.StrOpt(name="maas_api_key", secret=True, help="MaaS API Key"),
    cfg.URIOpt(
        name="maas_ui_url",
        schemes=["http", "https"],
        help="URL of MaaS console.",
        sample_default="http://maas:5240/",
    ),
    # Local
    cfg.HostAddressOpt(
        name="local_ipmi_address",
        help="Specify the IPMI address of the current server",
        sample_default="1.1.1.1",
    ),
]

OOB_OPTIONS = [
    cfg.StrOpt(
        "username",
        help="Default IPMI username. Will be used if no IPMI credentials are found "
        "from the DCIM",
        sample_default="admin",
    ),
    cfg.StrOpt(
        "password",
        secret=True,
        help="Default IPMI username. Will be used if no IPMI credentials are found "
        "from the DCIM",
        sample_default="password",
    ),
    cfg.URIOpt(
        "http_share",
        schemes=["http"],
        help="HTTP Share (currently only used by Dell servers)",
        sample_default="http://10.0.0.1/",
    ),
    cfg.HostAddressOpt(
        "nfs_share", help="NFS Share (currently only used by Dell servers)"
    ),
    cfg.IntOpt(
        "expected_psus",
        default=1,
        min=0,
        help="Number of PSUs expected on the server",
        sample_default=2,
    ),
    cfg.DictOpt(
        "expected_firmware_versions",
        default={},
        help="Mapping of expected firmware versions for this server.",
        sample_default="bios:1.0.0, tsm:1.0.0, psu_$model=1.3.2",
    ),
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


def list_opts():
    return [
        ("", DEFAULT_OPTIONS),
        ("dcim", DCIM_OPTIONS),
        ("oob", OOB_OPTIONS),
    ]
