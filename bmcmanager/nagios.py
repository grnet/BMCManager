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


from bmcmanager import exitcode

OK, WARNING, CRITICAL, UNKNOWN = range(4)
RESULT = {
    OK: 'OK',
    WARNING: 'WARNING',
    CRITICAL: 'CRITICAL',
    UNKNOWN: 'UNKNOWN',
}


def result(status, msg, lines=[], perfdata=[], pre=''):
    if isinstance(msg, list):
        msg = ', '.join(msg)

    print('{} {}: {}'.format(pre, RESULT[status], msg).strip(), end='')
    print(' |' if lines or perfdata else '')

    for line in lines:
        print(line.replace('|', '/'))

    if perfdata:
        print('| ', end='')

    for perf in perfdata:
        print(perf)

    exitcode.update(status)
