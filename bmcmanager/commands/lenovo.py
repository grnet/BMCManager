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

from cliff.lister import Lister

from bmcmanager.commands.base import BMCManagerServerListCommand, json_argument

LENOVO_RPC_COLUMNS = ['name', 'description', 'response_object']

LENOVO_RPCS = [
    [
        "getactivedircfg",
        "Active Directory auth configuration",
        "WEBVAR_JSONVAR_GETLDAPCFG",
    ],
    [
        "getallcpuinfo",
        "Connected CPUs",
        "WEBVAR_JSONVAR_INVENTORYGETALLCPUINFO",
    ],
    [
        "getalldimminfo",
        "Connected DIMMs",
        "WEBVAR_JSONVAR_INVENTORYGETALLDIMMINFO",
    ],
    [
        "getalllancfg",
        "Get network information for IPMI interfaces",
        "WEBVAR_JSONVAR_GETALLNETWORKCFG",
    ],
    [
        "getallpefcfg",
        "Event Filters",
        "WEBVAR_JSONVAR_HL_GETPEFTABLE",
    ],
    [
        "getallsensors",
        "Get status of all IPMI sensors",
        "WEBVAR_JSONVAR_HL_GETALLSENSORS",
    ],
    [
        "getalluserinfo",
        "IPMI users",
        "WEBVAR_JSONVAR_HL_GETALLUSERINFO",
    ],
    [
        "getanalysedsel",
        "Retrieve SEL, with OEM entries decoded.",
        "WEBVAR_JSONVAR_HL_GETANALYSEDSEL",
    ],
    [
        "getauditlog",
        "Audit log (connections)",
        "WEBVAR_JSONVAR_GETAUDITLOG",
    ],
    [
        "getdatetime",
        "Get Server Time",
        "WEBVAR_JSONVAR_GETDATETIME",
    ],
    [
        "getfruinfo",
        "Fetch all FRU devices",
        "WEBVAR_JSONVAR_HL_GETALLFRUINFO",
    ],
    [
        "gethddinfo",
        "Connected Disks",
        "WEBVAR_JSONVAR_GETINVDRIVEINFO",
    ],
    [
        "gethealthledinfo",
        "Get health LED status",
        "WEBVAR_JSONVAR_GETHEALTHLEDINFO",
    ],
    [
        "getimageinfo",
        "Firmware versions",
        "WEBVAR_JSONVAR_GETIMAGEINFO",
    ],
    [
        "getldapcfg",
        "LDAP auth configuration",
        "WEBVAR_JSONVAR_GETLDAPCFG",
    ],
    [
        "getsysteminfo",
        "BIOS version, Serial number, Model",
        "WEBVAR_JSONVAR_GETSYSTEMINFO",
    ],
    [
        "getuidled",
        "Get identify LED status",
        "WEBVAR_JSONVAR_HL_LED_IDENTIFY_STATE",
    ],
    [
        "hoststatus",
        "Host health",
        "WEBVAR_JSONVAR_HL_SYSTEM_STATE",
    ],
]


class Do(BMCManagerServerListCommand):
    """
    execute an RPC call [Lenovo]
    """
    oob_method = 'lenovo_rpc'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--rpc', required=True,
            help='name of RPC to execute, see `bmcmanager lenovo rpc list`')
        parser.add_argument('--params', type=json_argument, default={})
        return parser


class List(Lister):
    """
    print known RPC calls [Lenovo]
    """
    def take_action(self, parsed_args):
        return LENOVO_RPC_COLUMNS, LENOVO_RPCS
