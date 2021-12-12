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
import json
import os
import sys

from cliff.command import Command
from cliff.show import ShowOne
from cliff.lister import Lister
from stevedore.driver import DriverManager

from bmcmanager.config import load_config, CONF

from bmcmanager.dcim import DCIMS
from bmcmanager.oob import OOBS
from bmcmanager.errors import BMCManagerError
from bmcmanager import exitcode

LOG = logging.getLogger(__name__)

README = "https://github.com/grnet/BMCManager/blob/master/README.md"


def int_in_range_argument(itt):
    """
    argparse integer in range
    """

    def argparse_type(value):
        ivalue = int(value)
        if ivalue not in itt:
            msg = "{} out of valid range [{}..{}]".format(value, min(itt), max(itt))
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
        raise argparse.ArgumentTypeError("invalid JSON") from e


def base_arguments(parser):
    """
    Base bmcmanager arguments
    """
    parser.add_argument("--config-file", help="configuration file path", default="")
    parser.add_argument(
        "--debug-config", help="print loaded configuration options", action="store_true"
    )


def server_arguments(parser):
    """
    Add server selection arguments
    """
    parser.add_argument("server", help="server name")
    parser.add_argument(
        "-d",
        "--dcim",
        help="name of DCIM to use",
    )
    parser.add_argument(
        "-t",
        "--type",
        help="unit type",
        choices=["name", "rack", "rack-unit", "serial"],
        default="search",
    )


def get_dcim(args, config):
    """
    Get a configured DCIM from arguments and configuration
    """
    dcim_name = args.dcim or config.default_dcim
    if not dcim_name:
        raise ValueError("DCIM name not specified, see {}".format(README))

    if dcim_name not in config.available_dcims:
        raise ValueError("DCIM {} not configured, see {}".format(dcim_name, README))

    dcim_config = config[dcim_name]
    if not dcim_config.type:
        raise ValueError("DCIM type not specified, possible values {}".format(DCIMS))

    Class = DriverManager("bmcmanager.dcim", dcim_config.type).driver
    return Class(args, dcim_config)


def get_oob_config(config, dcim, oob_info, get_secret=True):
    """
    Get configuration for an OOB
    """
    oob_name = oob_info["oob"].lower()
    oob_params = config[oob_name]

    if get_secret and dcim.supports_secrets() and "credentials" in oob_params:
        secret = dcim.get_secret(oob_params["credentials"], oob_info)
        if secret["name"]:
            oob_params.username = secret["name"]
        if secret["plaintext"]:
            oob_params.password = secret["plaintext"]

    return oob_params


def bmcmanager_take_action(cmd, parsed_args):
    cmd.parsed_args = parsed_args
    cmd.config = load_config(parsed_args.config_file)
    dcim = get_dcim(parsed_args, cmd.config)

    idx = None
    for idx, oob_info in enumerate(dcim.get_oobs()):
        LOG.debug("Creating OOB object for %s", oob_info["oob"])

        if oob_info["oob"] not in OOBS:
            LOG.info("OOB class %s not supported", oob_info["oob"])
            LOG.info("Falling back to OOB class %s", CONF.fallback_oob)
            oob_info["oob"] = CONF.fallback_oob

        if oob_info["oob"] not in CONF._groups:
            LOG.error("OOB %s not found in configuration file", oob_info["oob"])
            sys.exit(-1)

        oob_config = get_oob_config(cmd.config, dcim, oob_info)
        oob = OOBS.get(oob_info["oob"])(parsed_args, dcim, oob_config, oob_info)

        try:
            if hasattr(cmd, "oob_method"):
                return getattr(oob, cmd.oob_method)()
            else:
                return cmd.action(oob)
        except Exception as e:
            LOG.exception("Unhandled exception: %s", e)

    if idx is None:
        LOG.fatal("No servers found for '%s'", parsed_args.server)
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
