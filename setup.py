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
            print('{}: No such file or directory. Please refer to README.md '
                  'for installing missing package dependencies.'.format(exe))
            sys.exit(-1)


def setup_package():
    setup(
        name='bmcmanager',
        version=get_version(),
        description='bmcmanager tool - CloudEng Team fork',
        long_description=get_file('README.md'),
        url='',
        packages=find_packages(),
        entry_points={
            'console_scripts': [
                'bmcmanager=bmcmanager.__main__:main',
                'bmcm=bmcmanager.__main__:main',
            ],
        },
        install_requires=[
            'bs4',
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
