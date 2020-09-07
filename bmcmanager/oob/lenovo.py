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


from datetime import datetime, timedelta
import re
from subprocess import Popen
import sys
import tempfile
import time
import urllib3

import paramiko
import requests

from bmcmanager.oob.base import OobBase
from bmcmanager.logs import log
from bmcmanager import nagios

from bmcmanager.utils.firmware import version_tuple

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DISK_TYPE = {
    0: 'HDD',
    1: 'SSD',
}

DISK_INTERFACE = {
    2: 'SAS'
}

DISK_SPEED = {
    3: '6.0Gb/s',
    4: '12.0Gb/s',
}

DISK_STATE = {
    0: 'active',
}

# RPC DEV_TYPE --> osput Device ID
DEV_ID = {
    1: 'TSM',
    2: 'BIOS',
    4: 'PSU',
    5: 'RAID',
    6: 'Mezz',

    201: 'TDM',
    202: 'LG_WIND',
    203: 'LG_LIND',
    205: 'LG_DIAG',

    # Not reported by osput
    204: 'LG_WORK',
    3: 'LG_CPLD_000',
}


class Lenovo(OobBase):
    def _get_console_cookies(self):
        return {'Cookie': 'Language=EN; SessionExpired=true;'}

    def _get_console_headers(self):
        return {'Content-type': 'text/plain'}

    def _get_console_data(self):
        return {
            'WEBVAR_PASSWORD': str(self.password),
            'WEBVAR_USERNAME': str(self.username)
        }

    def _parse_response(self, text):
        """
        Parse response and return (list of results, retryable)
        """
        try:
            start = text.find('[')
            end = text.rfind(']')
            results = eval(text[start:end + 1])

            # drop empty '{}' objects from list of responses
            return [r for r in results if r], False

        except (SyntaxError, TypeError, ValueError):
            if 'session_expired.html' in text:
                log.critical('Failed due to expired session')
                return [], True
            else:
                log.critical('Could not parse response text')
                log.debug('Response was:\n{}'.format(text))
                return [], False

    def _connect(self):
        ipmi_host = self.oob_info['ipmi']
        url = ipmi_host + self.URL_LOGIN

        cookies = self._get_console_cookies()
        headers = self._get_console_headers()
        data = self._get_console_data()

        self._session = requests.session()

        for count in range(5):
            text = self._post(url, data, cookies, headers).text
            parsed, retryable = self._parse_response(text)
            if not parsed and retryable and count < 4:
                log.info('Will retry after {} seconds'.format(count))
                time.sleep(count)
            else:
                break

        if not parsed:
            log.error('Failed to create session')
            sys.exit(10)

        session_token = parsed[0]['SESSION_COOKIE']
        if session_token == 'Failure_Session_Creation':
            log.error('Probably reached session limit')
            sys.exit(10)

        CSRF_token = parsed[0]['CSRFTOKEN']

        self.session_token = {'SessionCookie': session_token}
        self.CSRF_token = {'CSRFTOKEN': CSRF_token}

    def _post(self, url, data, cookies, headers):
        return self._session.post(
            url,
            data=data,
            cookies=cookies,
            headers=headers,
            verify=False,
            timeout=60
        )

    def console(self):

        self._connect()

        ipmi = self.oob_info['ipmi']
        url = ipmi + self.URL_VNC.format(ipmi.replace('https://', ''))
        answer = self._post(
            url, None, self.session_token, self.CSRF_token).text

        _, myjviewer = tempfile.mkstemp()
        m = '\n<argument>-title</argument>\n<argument>{}</argument>'
        m = m.format(self.oob_info['identifier'])
        to_repl = '<argument>35</argument>'
        answer = answer.replace(to_repl, to_repl + m)

        with open(myjviewer, 'w') as f:
            f.write(answer)

        cmd = ['/usr/bin/javaws', myjviewer]
        try:
            if self.parsed_args.print_cmd:
                print(' '.join(cmd))
            else:
                Popen(cmd)
        except Exception as e:
            sys.stderr.write('Could not open Java console. {}\n'.format(e))
            sys.exit(10)

    def _system_ram(self):
        port = 22
        hostname = self.oob_info['ipmi'].replace('https://', '')
        username = self.username
        password = self.password

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=hostname, port=port,
                       username=username, password=password)
        _, stdout, stderr = client.exec_command('show admin1/hdwr1/memory1')
        output = stdout.read().decode()

        match = re.findall(r'NumberOfBlocks=(\d+)', output, re.MULTILINE)
        try:
            return int(match[0]) // 1024 // 1024
        except:
            return 0

    def system_ram(self):
        return ('ram_gb',), (self._system_ram(),)

    def check_ram(self):
        pre = '{} installed RAM'.format(self.oob_info['identifier'])
        expected = self.parsed_args.expected

        ram = self._system_ram()
        if (expected is None and ram > 0) \
                or (expected is not None and ram == expected):
            nagios.result(nagios.OK, '{}GB'.format(str(ram)), pre=pre)
        elif expected is None:
            nagios.result(nagios.UNKNOWN, 'Failed to read RAM')
        elif ram < expected:
            nagios.result(nagios.CRITICAL, '{}GB, expected {}GB'.format(
                str(ram), str(expected)), pre=pre)
        elif ram > expected:
            nagios.result(nagios.WARNING, '{}GB, expected {}GB'.format(
                str(ram), str(expected)), pre=pre)

    def lock_power_switch(self):
        self._execute(['raw', '0x00', '0x0a', '0x01'])

    def unlock_power_switch(self):
        self._execute(['raw', '0x00', '0x0a', '0x00'])

    def _get_rpc(self, rpc, item='', params=None):
        if not hasattr(self, 'CSRF_token'):
            self._connect()

        ipmi_host = self.oob_info['ipmi']
        url = ipmi_host + '/rpc/{}.asp'.format(rpc)
        response = self._post(url, params, self.session_token, self.CSRF_token)

        if response.status_code != 200:
            log.critical('Cannot retrieve {}, error {}'.format(
                item, response.status_code))
            return []

        resp, _ = self._parse_response(response.text)
        return resp

    def _get_disks(self):
        return self._get_rpc('gethddinfo', 'disks')

    def _get_sel(self):
        res = self._get_rpc('getanalysedsel', 'SEL', params={
            'WEBVAR_END_RECORD': 65535
        })
        for r in res:
            r['TimeStamp'] = str(
                datetime.utcfromtimestamp(r.get('TimeStamp', 0)))

        return res

    def get_disks(self):
        disks = self._get_disks()
        columns = ['index', 'ctrl', 'slot', 'size_gb', 'type', 'state',
                   'interface', 'speed', 'vendor']
        values = [[
            disk['DRIVE_INDEX'],
            disk['CONTROLLER_INDEX'],
            disk['SLOT_NUMBER'],
            disk['SIZE'] // 1024,
            DISK_TYPE.get(disk['MEDIA_TYPE'], 'N/A'),
            DISK_STATE.get(disk['DEVICE_STATE'], 'unknown'),
            DISK_INTERFACE.get(disk['INTF_TYPE'], 'unknown'),
            DISK_SPEED.get(disk['LINK_SPEED'], 'unknown'),
            disk['VENDOR_ID'],
        ] for disk in disks]

        return columns, values

    def ipmi_logs_analysed(self):
        sel = self._get_sel()
        if not sel:
            return (None, None)

        columns = sel[0].keys()
        values = [[line[col] for col in columns] for line in sel]

        return columns, values

    def _format_disk(self, disk):
        return ' | '.join(map(str, [
            disk['DRIVE_INDEX'],
            'ctrl{}'.format(disk['CONTROLLER_INDEX']),
            'slot{}'.format(disk['SLOT_NUMBER']),
            '{}gb'.format(disk['SIZE'] // 1024),
            DISK_TYPE.get(disk['MEDIA_TYPE'], 'N/A'),
            DISK_STATE.get(disk['DEVICE_STATE'], 'unknown'),
            DISK_INTERFACE.get(disk['INTF_TYPE'], 'unknown'),
            DISK_SPEED.get(disk['LINK_SPEED'], 'unknown'),
            disk['VENDOR_ID'],
        ]))

    def check_disks(self):
        pre = '{} disks'.format(self.oob_info['identifier'])
        expected = self.parsed_args.expected

        disks = self._get_disks()
        disks_ok, disks_crit = [], []
        for d in disks:
            if d['DEVICE_STATE'] != 0 or d['SIZE'] <= 0:
                disks_crit.append(d)
            else:
                disks_ok.append(d)

        status, msg, lines = nagios.OK, [], []
        if disks_crit:
            status = nagios.CRITICAL
            lines.append('{} disks CRITICAL:'.format(len(disks_crit)))
            lines.extend(
                map(lambda d: '- {}'.format(self._format_disk(d)), disks_crit))
            msg.append('{} disks CRITICAL'.format(len(disks_crit)))

        msg.append('{} disks OK'.format(len(disks_ok)))
        if expected is not None and len(disks_ok) != expected:
            msg.append('expected {}'.format(expected))
            status = max(status, nagios.WARNING)

            lines.append('{} disks OK:'.format(len(disks_ok)))
            lines.extend(
                map(lambda d: '- {}'.format(self._format_disk(d)), disks_ok))
            if len(disks_ok) < expected:
                status = max(status, nagios.CRITICAL)

        nagios.result(status, msg, lines, pre=pre)

    def _get_image_info(self):
        return self._get_rpc('getimageinfo', 'firmware versions')

    def _format_fw(self, fw):
        return '- ' + ' | '.join([
            DEV_ID.get(fw['DEV_TYPE'], 'unknown'),
            fw['CURIMG_VER'],
        ])

    def get_firmware(self):
        firmwares = self._get_image_info()
        if not firmwares:
            return (None, None)

        columns = firmwares[0].keys()
        values = [[f[col] for col in columns] for f in firmwares]

        return columns, values

    def refresh_firmware(self):
        custom_fields = {}
        firmwares = self._get_image_info()

        psus = []
        for firmware in firmwares:
            device_id = DEV_ID[firmware['DEV_TYPE']]
            version = firmware['CURIMG_VER']
            if device_id == 'BIOS':
                custom_fields['BIOS'] = version
            elif device_id == 'TSM':
                custom_fields['TSM'] = version
            elif device_id == 'PSU':
                psus.append('{}/{}: {}'.format(
                    firmware['SLOT_NO'], firmware['DEV_IDENTIFIER'], version))

        custom_fields['PSU'] = ', '.join(sorted(psus))

        log.info('Patching custom fields: {}'.format(custom_fields))
        if not self.dcim.set_custom_fields(self.oob_info, custom_fields):
            log.error('Failed to refresh DCIM firmware versions')

    def _matching(self, d1, d2):
        return d1['DEV_IDENTIFIER'] == d2['DEV_IDENTIFIER']

    def firmware_upgrade_osput(self):
        ipmi = self.oob_info['ipmi'].replace('https://', '')
        return self._execute_cmd([
            self.parsed_args.osput,
            '-H', ipmi,
            '-u', self.username,
            '-p', self.password,
            '-f', self.parsed_args.bundle,
            '-c', 'update'])

    def firmware_upgrade_rpc(self):
        args = self.parsed_args
        handle = None

        if 1 in args.stages:
            log.info('Enter FW update mode')
            r = self._get_rpc('getenterfwupdatemode', params={'FWUPMODE': 1})
            log.debug(r)
            if r and 'HANDLE' in r[0]:
                handle = r[0]['HANDLE']
                log.info('Enter FW update mode: OK')
            else:
                log.fatal('Cannot enter FW update mode')
                sys.exit(-1)

        log.info('Update session handle: {}'.format(handle))

        if 2 in args.stages:
            handle = handle or args.handle
            log.info('Rearm firmware update timer')
            r = self._get_rpc('rearmfwupdatetimer', params={'SESSION_ID': handle})
            log.debug(r)

            if r[0]['NEWSESSIONID'] == handle:
                log.info('Rearm firmware update timer: OK')

        if 3 in args.stages:
            handle = handle or args.handle
            if not hasattr(self, 'CSRF_token'):
                self._connect()

            log.info('Uploading firmware bundle')

            ipmi = self.oob_info['ipmi']
            url = ipmi + '/file_upload_firmware.html'
            r = requests.post(
                url,
                verify=False,
                cookies=self.session_token,
                headers=self.CSRF_token,
                files={
                    'bundle?FWUPSessionid={}'.format(handle): args.bundle
                })

            log.debug(r.status_code)
            if r.status_code == 200:
                log.info('Uploading firmware bundle: OK')

        if 4 in args.stages:
            log.info('Get Bundle Upload Status')
            r = self._get_rpc('getbundleupldstatus')
            log.debug(r)

            if r == []:
                log.info('Get Bundle Upload Status: OK')

        if 5 in args.stages:
            log.info('Validate Bundle')
            r = self._get_rpc('validatebundle', params={'BUNDLENAME': 'bundle_bkp.bdl'})
            log.debug(r)
            if r[0]['STATUS'] == 0:
                log.info('Validate Bundle: OK')

        if 6 in args.stages:
            log.info('Replace Bundle')
            r = self._get_rpc('replacebundlebkp')
            log.debug(r)
            if r[0]['STATUS'] == 0:
                log.info('Replace Bundle: OK')

        if 7 in args.stages:
            log.info('Checking for new firmware')
            r = self._get_rpc('getimageinfo')
            log.debug(r)

            def has_update(x):
                new, cur = x['NEWIMG_VER'], x['CURIMG_VER']
                try:
                    return version_tuple(new) > version_tuple(cur)
                except (TypeError, ValueError):
                    return new > cur

            to_update = next(filter(has_update, r), None)
            if to_update is None:
                log.info('No updates available')
                return
            else:
                log.info('Available update: {}'.format(to_update))

        if 8 in args.stages and to_update:
            handle = handle or args.handle
            log.info('Choose component update')
            r = self._get_rpc('setupdatecomp', params={
                'UPDATE_FLAG': to_update['DEV_TYPE'],
                'UPDATE_CNT': 1,
                'FW_DEVICE_TYPE': to_update['DEV_TYPE'],
                'SLOT_NO': to_update['SLOT_NO'],
                'DEV_IDENTIFIER': to_update['DEV_IDENTIFIER'],
                'SESSION_ID': handle,
            })
            log.debug(r)
            if r == []:
                log.info('Choose component update: OK')

        log.info('Firmware upgrade process started')

        if 9 in args.stages:
            begin = datetime.utcnow()
            while datetime.utcnow() < begin + timedelta(minutes=args.timeout):
                try:
                    r = self._get_rpc('getcompupdatestatus')
                    log.debug(r)
                    dev = next((
                        x for x in r if self._matching(x, to_update)), None)
                    log.debug(dev)
                    progress = (dev or {}).get('UPDATE_PERCENTAGE')
                    if progress is None:
                        log.info('Update in progress')
                    else:
                        log.info('Update progress: {}%'.format(progress))
                        if progress == 100:
                            log.info('Update complete!')
                            break
                except (ConnectionResetError, BrokenPipeError):
                    log.info('Update in progress')

                time.sleep(10)

        if 10 in args.stages:
            handle = handle or args.handle
            log.info('Exit FW update mode')
            r = self._get_rpc('getexitfwupdatemode', params={
                'MODE': 0, 'RNDNO': handle
            })
            log.debug(r)
            if r == []:
                log.info('Exit FW update mode: OK')

        log.info('Done!')

    def lenovo_rpc(self):
        args = self.parsed_args
        response = self._get_rpc(args.rpc, 'RPC call', args.params)

        if not response:
            return (None, None)

        columns = list(response[0].keys())
        values = [[r[col] for col in columns] for r in response]

        return columns, values
