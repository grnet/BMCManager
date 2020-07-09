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
import re
import sys
from setuptools import setup, find_packages


def get_file(name):
    try:
        with open(name, 'r') as fin:
            return fin.read()
    except OSError:
        return ""


def get_version():
    changelog = get_file('CHANGELOG.md')
    version = next(re.finditer(r'## \[v([\d.]*)\]', changelog), None)
    return version and version.group(1) or 'none'


if not os.getenv('BMCMANAGER_IGNORE_MISSING_BINARIES'):
    for exe in [
        '/usr/bin/ipmitool',
        '/usr/sbin/ipmi-sensors',
        '/usr/sbin/ipmi-sel',
        '/usr/sbin/ipmi-dcmi',
    ]:
        if not os.path.isfile(exe) or not os.access(exe, os.X_OK):
            print('{}: No such file or directory. Please refer to README.md \
for installing missing package dependencies, or set the \
BMCMANAGER_IGNORE_MISSING_BINARIES environment variable'.format(exe))
            sys.exit(-1)


def setup_package():
    setup(
        name='bmcmanager',
        version=get_version(),
        description='bmcmanager tool - CloudEng Team fork',
        long_description=get_file('README.md'),
        long_description_content_type='text/markdown',
        url='https://github.com/grnet/BMCManager.git',
        packages=find_packages(),
        entry_points={
            'console_scripts': [
                'bmcmanager = bmcmanager.cliff:main',
                'bmcm = bmcmanager.cliff:main',
            ],
            'bmcmanager.entrypoints': [
                'open console = bmcmanager.commands.open:Console',
                'open dcim = bmcmanager.commands.open:DCIM',
                'open web = bmcmanager.commands.open:Web',
                'check firmware = bmcmanager.commands.firmware:Check',
                'check sensor = bmcmanager.commands.ipmi.sensor:Check',
                'check disks = bmcmanager.commands.disks:Check',
                'check ram = bmcmanager.commands.ram:Check',
                'disks check = bmcmanager.commands.disks:Check',
                'disks get = bmcmanager.commands.disks:Get',
                'firmware get = bmcmanager.commands.firmware:Get',
                'firmware refresh = bmcmanager.commands.firmware:Refresh',
                'firmware check = bmcmanager.commands.firmware:Check',
                'firmware latest get = bmcmanager.commands.firmware:Latest',
                'firmware upgrade rpc = bmcmanager.commands.firmware:UpgradeRPC',
                'firmware upgrade osput = bmcmanager.commands.firmware:UpgradeOsput',
                'ipmi address get = bmcmanager.commands.ipmi.address:Get',
                'ipmi address refresh = bmcmanager.commands.ipmi.address:Refresh',
                'ipmi credentials get = bmcmanager.commands.ipmi.credentials:Get',
                'ipmi credentials set = bmcmanager.commands.ipmi.credentials:Set',
                'ipmi logs clear = bmcmanager.commands.ipmi.logs:Clear',
                'ipmi logs get = bmcmanager.commands.ipmi.logs:Get',
                'ipmi reset = bmcmanager.commands.ipmi.reset:Reset',
                'ipmi sensor check = bmcmanager.commands.ipmi.sensor:Check',
                'ipmi sensor get = bmcmanager.commands.ipmi.sensor:Get',
                'ipmi ssh = bmcmanager.commands.ipmi.ssh:SSH',
                'ipmi tool = bmcmanager.commands.ipmitool:Run',
                'lenovo rpc do = bmcmanager.commands.lenovo:Do',
                'lenovo rpc list = bmcmanager.commands.lenovo:List',
                'netbox secret list = bmcmanager.commands.netbox:ListSecrets',
                'netbox secret set = bmcmanager.commands.netbox:SetSecret',
                'power cycle = bmcmanager.commands.power:PowerCycle',
                'power off = bmcmanager.commands.power:PowerOff',
                'power on = bmcmanager.commands.power:PowerOn',
                'power reset = bmcmanager.commands.power:PowerReset',
                'power status = bmcmanager.commands.power:PowerStatus',
                'power switch lock = bmcmanager.commands.power:LockSwitch',
                'power switch unlock = bmcmanager.commands.power:UnlockSwitch',
                'ram check = bmcmanager.commands.ram:Check',
                'ram get = bmcmanager.commands.ram:Get',
                'server boot local = bmcmanager.commands.server.boot:Local',
                'server boot pxe = bmcmanager.commands.server.boot:PXE',
                'server status get = bmcmanager.commands.server.status:Get',
                'server status storage = bmcmanager.commands.server.status:Storage',
                'server status controllers = bmcmanager.commands.server.status:Controllers',
                'server status pdisks = bmcmanager.commands.server.status:PDisks',
                'server autoupdate enable = bmcmanager.commands.server.autoupdate:Enable',
                'server autoupdate disable = bmcmanager.commands.server.autoupdate:Disable',
                'server diagnostics = bmcmanager.commands.server.server:Diagnostics',
                'server identify = bmcmanager.commands.server.server:Identify',
                'server info get = bmcmanager.commands.server.server:Info',
                'server info idrac = bmcmanager.commands.server.server:IdracInfo',
                'server upgrade = bmcmanager.commands.server.server:Upgrade',
                'server ssh = bmcmanager.commands.server.server:SSH',
                'server jobs flush = bmcmanager.commands.server.server:FlushJobs',
                'server list = bmcmanager.commands.server.list:List',
            ]
        },
        install_requires=[
            'bs4',
            'cliff',
            'paramiko',
            'requests',
        ],
        classifiers=[
            'Intended Audience :: System Administrators',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Operating System :: OS Independent',
        ],
    )


if __name__ == '__main__':
    setup_package()
