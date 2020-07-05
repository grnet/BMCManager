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


import re

from bmcmanager import nagios


def version_tuple(version_str):
    """converts '1.2.3' --> (1, 2, 3)."""
    return tuple(int(x) for x in version_str.split('.'))


def check_version_strings(version_value, expected_version, version_check=True):
    try:
        version = version_tuple(version_value)

    except (TypeError, ValueError, AttributeError):
        return nagios.CRITICAL, 'invalid data'

    try:
        target_version = version_tuple(expected_version)

    except (TypeError, ValueError, AttributeError):
        return nagios.CRITICAL, 'missing config'

    if version >= target_version:
        return nagios.OK, 'ok: {}'.format(version_value)
    else:
        msg = 'have {}, expected {}'.format(version_value, expected_version)
        if version[0] < target_version[0]:
            status = nagios.CRITICAL
        else:
            status = nagios.WARNING

        if not version_check:
            status = nagios.OK
        return status, msg


def psu_checks(all_psu_versions, version_dict):
    try:
        psu_info = all_psu_versions.split(', ')
    except (ValueError, TypeError, AttributeError):
        return {
            'psu': (nagios.CRITICAL, 'invalid data')
        }

    results = {}
    for psu in psu_info:
        m = re.match(
            r'^(?P<psu_slot>\d+)\/(?P<psu_type>\w*)'
            r':\s(?P<psu_version>\d+\.\d+\.\d+)$',
            psu)

        if not m or not m.groupdict():
            results['psu'] = nagios.CRITICAL, 'invalid data'
            continue

        psu_info_dict = m.groupdict()
        psu_slot = psu_info_dict['psu_slot']
        psu_type = psu_info_dict['psu_type']

        version_str = psu_info_dict['psu_version']
        target_version_str = version_dict.get('psu_{}'.format(
            psu_type.lower()))
        res, msg = check_version_strings(
            version_str, target_version_str, version_check=False)

        results['psu-{}'.format(psu_slot)] = res, '{}, {}'.format(
            msg, psu_type)

    return results


def check_firmware(custom_fields, oob_params):
    result, msg = nagios.OK, []

    psus = psu_checks(custom_fields['PSU'], oob_params['oob_params'])
    checks = {
        'bios': check_version_strings(
            custom_fields['BIOS'], oob_params['oob_params'].get('bios')),
        'tsm': check_version_strings(
            custom_fields['TSM'], oob_params['oob_params'].get('tsm')),
        **psus,
    }

    for check, check_data in checks.items():
        state, text = check_data
        msg.append('{} ({})'.format(check.upper(), text))
        result = max(state, result)

    try:
        expected_psus = int(oob_params['oob_params']['expected_psus'])
        if expected_psus != len(psus):
            msg.append('{} PSUs present (expected {})'.format(
                len(psus), expected_psus))
            result = max(state, nagios.CRITICAL)

    except (TypeError, ValueError, KeyError):
        pass

    return result, msg
