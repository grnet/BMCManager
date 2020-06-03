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
import json
import logging
import os
import re
from subprocess import Popen, check_output, CalledProcessError, call
import sys
import urllib.request
import urllib.error

import paramiko

from bmcmanager.interactive import posix_shell
from bmcmanager.utils import firmware
from bmcmanager import nagios
from bmcmanager.firmwares import firmware_fetchers

if sys.platform == 'darwin':
    BROWSER_OPEN = 'open'
else:
    BROWSER_OPEN = 'xdg-open'

# Column indexes for ipmi-sel output
SEL_ID, SEL_DATE, SEL_TIME, SEL_NAME, SEL_TYPE, SEL_STATE, SEL_EVENT = range(7)

# Column indexes for ipmi-sensors output
SSR_ID, SSR_NAME, SSR_TYPE, SSR_STATE, SSR_VALUE, SSR_UNIT, _, SSR_CRITL, \
    SSR_WARNL, SSR_WARNH, SSR_CRITH, _, SSR_DESC = range(13)


class OobBase(object):
    URL_LOGIN = '/rpc/WEBSES/create.asp'
    URL_VNC = '/Java/jviewer.jnlp?EXTRNIP={}&JNLPSTR=JViewer'

    # All oobs inherit this class
    # Defines the interface for oobs
    # and implements basic functionality.
    def __init__(self, command, oob_info, command_args, username=None,
                 password=None, wait=False, force=False, http_share=None,
                 nfs_share=None, oob_params=None, dcim=None):
        self.command = command
        self.oob_info = oob_info
        self.command_args = command_args
        self.username = username
        self.password = password
        self.wait = wait
        self.force = force
        self.nfs_share = nfs_share
        self.http_share = http_share
        self.oob_params = oob_params
        self.dcim = dcim

    def _print(self, msg):
        sys.stdout.write('{}:\n{}\n'.format(self.oob_info['identifier'], msg))

    def info(self):
        logging.info('Executing info')
        info = self.oob_info['info']

        info_str = ''
        for key, val in info.items():
            info_str += ('{}:{}\n'.format(key.replace('_', ' ').upper(), val))

        self._print(info_str[:-1])

    def _execute_popen(self, command):
        logging.info('Executing {}'.format(' '.join(command)))
        try:
            Popen(command)
        except:
            raise OobError('Could not open browser {}'.format(
                ' '.join(command)))

    def open(self):
        self._execute_popen([BROWSER_OPEN, self.oob_info['ipmi']])

    def ssh(self):
        status_command = ['chassis', 'power', 'status']
        if self.wait:
            if 'off' in self._execute(status_command, output=True):
                logging.info('Waiting for machine to turn on...')

            while (1):
                if 'off' not in self._execute(status_command, output=True):
                    break

        host = self.oob_info['asset_tag']
        if not host:
            raise OobError('Cannot perform ssh without an asset tag')
        call(['ssh', host])

    def _get_ipmi_tool_prefix(self):
        host = self.oob_info['ipmi'].replace('https://', '')
        return ['ipmitool', '-U', self.username, '-P', self.password,
                '-I', 'lanplus', '-H', host]

    # command is an array
    def _execute(self, command, output=False):
        if not self.oob_info['ipmi']:
            logging.warn('No IPMI field for {}'.format(self.oob_info['oob']))
            return ''

        prefix = self._get_ipmi_tool_prefix()
        command = prefix + command

        return self._execute_cmd(command, output)

    # command is an array
    def _execute_cmd(self, command, output=False):
        logging.info('Executing {}'.format(' '.join(command)))
        try:
            if output:
                return check_output(command).decode('utf-8')

            call(command)
        except CalledProcessError as e:
            raise OobError('Command {} failed: {}'.format(
                ' '.join(command), str(e)))
        except UnicodeError as e:
            raise OobError('Decoding output of {} failed: {}'.format(
                ' '.join(command), str(e)))

    def identify(self):
        if len(self.command_args) != 1:
            raise OobError('Wrong number of args')

        try:
            int(self.command_args[0])
        except ValueError:
            raise OobError('Argument not an int')

        self._print(self._execute(
            ['chassis', 'identify', self.command_args[0]],
            output=True
        ).strip())

    def status(self):
        self._print(self._execute(
            ['chassis', 'status'],
            output=True
        ).strip())

    def power_status(self):
        self._print(self._execute(
            ['chassis', 'power', 'status'],
            output=True
        ).strip())

    def power_on(self):
        self._execute(['chassis', 'power', 'on'])

    def power_off(self):
        cmd = ['chassis', 'power']
        if self.force:
            cmd.append('off')
        else:
            cmd.append('soft')
        self._execute(cmd)
        if self.wait:
            while 1:
                stdout = self._execute(
                    ['chassis', 'power', 'status'], output=True)
                if 'off' in stdout:
                    break

    def power_cycle(self):
        self._execute(['chassis', 'power', 'cycle'])

    def power_reset(self):
        self._execute(['chassis', 'power', 'reset'])

    def boot_pxe(self):
        self._execute(['chassis', 'bootdev', 'pxe'])

    def boot_local(self):
        self._execute(['chassis', 'bootdev', 'disk'])

    def ipmi_reset(self):
        cmd = ['mc', 'reset']
        if self.force:
            cmd.append('cold')
        else:
            cmd.append('warm')

        self._execute(cmd)

    def _ipmi_logs_cmd(self, args=[]):
        return ['sel', 'list', *args]

    def ipmi_logs(self):
        self._print(self._execute(self._ipmi_logs_cmd(), output=True).strip())

    def clear_ipmi_logs(self):
        self._print(self._execute(['sel', 'clear'], output=True).strip())

    def console(self):
        raise NotImplementedError('console')

    def diagnostics(self):
        raise NotImplementedError('diagnostics')

    def autoupdate(self):
        raise NotImplementedError('autoupdate')

    def upgrade(self):
        raise NotImplementedError('upgrade')

    def idrac_info(self):
        raise NotImplementedError('idrac-info')

    def remove_autoupdate(self):
        raise NotImplementedError('remove-autoupdate')

    def flush_jobs(self):
        raise NotImplementedError('flush-jobs')

    def pdisks_status(self):
        raise NotImplementedError('pdisks-status')

    def storage_status(self):
        raise NotImplementedError('storage-status')

    def controllers_status(self):
        raise NotImplementedError('controllers-status')

    def system_ram(self):
        raise NotImplementedError('system-ram')

    def lock_power_switch(self):
        raise NotImplementedError('lock-power-switch')

    def unlock_power_switch(self):
        raise NotImplementedError('unlock-power-switch')

    def _ipmi_sensors_cmd(self, host, username, password, args=[]):
        if os.getenv('XDG_CACHE_HOME'):
            cache_dir_arg = '--sdr-cache-dir=$XDG_CACHE_HOME'
            args = [*args, os.path.expandvars(cache_dir_arg)]

        return [
            'ipmi-sensors', '-h', host,
            '-u', username, '-p', password, '-l', 'user',
            '--quiet-cache', '--sdr-cache-recreate',
            '--interpret-oem-data', '--output-sensor-state',
            '--ignore-not-available-sensors',
            '--driver-type=LAN_2_0',
            '--output-sensor-thresholds',
            *args]

    def _ipmi_sel_cmd(self, host, username, password, args=[]):
        return [
            'ipmi-sel', '-h', host,
            '-u', username, '-p', password, '-l', 'user',
            '--driver-type=LAN_2_0',
            '--output-event-state',
            '--interpret-oem-data',
            '--entity-sensor-names',
            '--sensor-types=all',
            '--ignore-sdr-cache',
            *args
        ]

    def _ipmi_dcmi_cmd(self, host, username, password, args=[]):
        return [
            'ipmi-dcmi', '-h', host,
            '-u', username, '-p', password, '-l', 'user',
            '--driver-type=LAN_2_0',
            '--get-system-power-statistics',
            *args
        ]

    def ipmi_sensors(self):
        host = self.oob_info['ipmi'].replace('https://', '')
        cmd = self._ipmi_sensors_cmd(host, self.username, self.password)
        self._execute_cmd(cmd)

    def _format_sensor(self, sensor):
        return '- ' + ' | '.join([sensor[x] for x in [
            SSR_ID, SSR_TYPE, SSR_NAME, SSR_VALUE, SSR_UNIT, SSR_DESC
        ]])

    def __clear_na(self, x):
        return '' if x == 'N/A' else x

    def _format_sensor_perfdata(self, sensor):
        if sensor[SSR_VALUE] == 'N/A':
            return ''

        warning = ''
        warning_low = self.__clear_na(sensor[SSR_WARNL])
        warning_high = self.__clear_na(sensor[SSR_WARNH])
        if warning_low or warning_high:
            warning = '{}:{}'.format(warning_low, warning_high)

        critical = ''
        critical_low = self.__clear_na(sensor[SSR_CRITL])
        critical_high = self.__clear_na(sensor[SSR_CRITH])
        if critical_low or critical_high:
            critical = '{}:{}'.format(critical_low, critical_high)

        result = "'{}'={}".format(sensor[SSR_NAME], sensor[SSR_VALUE])
        if warning or critical:
            result = '{};{};{}'.format(result, warning, critical)

        return result

    def _format_sel(self, sel):
        return '- ' + ' | '.join([sel[x] for x in [
            SEL_ID, SEL_DATE, SEL_TIME, SEL_TYPE, SEL_NAME, SEL_EVENT
        ]])

    def _get_sel_errors(self, host):
        cmd = self._ipmi_sel_cmd(host, self.username, self.password)
        logs = self._execute_cmd(cmd, output=True)
        for line in reversed(logs.split('\n')[1:-1]):
            split = list(map(lambda x: x.strip(), line.split('|')))
            if split[SEL_STATE] != 'Nominal':
                yield split

    def _sel_is_firmware_upgrade(self, line):
        checks = {
            SEL_DATE: 'PostInit',
            SEL_TIME: 'PostInit',
            SEL_TYPE: 'Version Change',
        }
        return all(line[k] == v for k, v in checks.items())

    def check_ipmi(self):
        pre = '{} IPMI Status'.format(self.oob_info['identifier'])
        try:
            host = self.oob_info['ipmi'].replace('https://', '')
        except:
            nagios.result(nagios.UNKNOWN, 'No IPMI information', pre=pre)
            return

        perfdata = []
        cmd = self._ipmi_dcmi_cmd(host, self.username, self.password)
        dcmi_output = self._execute_cmd(cmd, output=True)
        match = re.findall(r'Current Power\s*:\s*(\d+)', dcmi_output)
        if match:
            perfdata.append("'Current Power'={}".format(match[0]))

        sel_errors = list(self._get_sel_errors(host))

        cmd = self._ipmi_sensors_cmd(host, self.username, self.password)
        sensors = self._execute_cmd(cmd, output=True)
        sensor_warnings = []
        sensor_errors = []
        for line in sensors.split('\n')[1:-1]:
            split = list(map(lambda x: x.strip(), line.split('|')))

            data = self._format_sensor_perfdata(split)
            if data:
                perfdata.append(data)

            if split[SSR_STATE] in ['Nominal', 'N/A']:
                continue
            elif split[SSR_STATE] == 'Warning':
                sensor_warnings.append(split)
            else:
                sensor_errors.append(split)

        status, msg, lines = nagios.OK, [], []
        if sensor_warnings:
            status = nagios.WARNING
            msg.append('{} sensors warning'.format(len(sensor_warnings)))
            lines.extend([
                'Warning sensors:',
                *map(lambda x: self._format_sensor(x), sensor_warnings)])
        if sensor_errors:
            status = nagios.CRITICAL
            msg.append('{} sensors critical'.format(len(sensor_errors)))
            lines.extend([
                'Critical sensors:',
                *map(lambda x: self._format_sensor(x), sensor_errors)])
        if sel_errors:
            status = nagios.CRITICAL
            msg.append('{} SEL entries'.format(len(sel_errors)))
            sel_entries_header = 'SEL entries:'

            # cap number of SEL entries returned
            if len(sel_errors) > 10:
                sel_entries_header += ' (showing latest 10/{})'.format(
                    len(sel_errors))
                sel_errors = sel_errors[:10]

            lines.extend([
                sel_entries_header,
                *map(lambda x: self._format_sel(x), sel_errors)])

        perfdata = [' '.join(perfdata)]
        nagios.result(status, msg or 'SEL, Sensors OK', lines, perfdata, pre)

    def creds(self):
        parser = argparse.ArgumentParser('bmcmanager creds')
        parser.add_argument(
            '--ipmi-field',
            choices=['username', 'password', 'hostname', 'all'],
            default='all')

        args = parser.parse_args(self.command_args)

        ipmi = (self.oob_info['ipmi'] or '').replace('https://', '')
        if args.ipmi_field == 'hostname':
            print(ipmi)
        elif args.ipmi_field == 'username':
            print(self.username)
        elif args.ipmi_field == 'password':
            print(self.password)
        else:
            self._print('\n'.join([
                'IPMI:{}'.format(ipmi),
                'USERNAME:{}'.format(self.username),
                'PASSWORD:{}'.format(self.password),
            ]))

    def ipmi_ssh(self):
        port = 22
        hostname = self.oob_info['ipmi'].replace('https://', '')
        username = self.username
        password = self.password

        if self.command_args:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=hostname, port=port,
                           username=username, password=password)
            _, out, err = client.exec_command(' '.join(self.command_args))
            print(out.read().decode())
            if err:
                print(err.read().decode(), file=sys.stderr)
        else:
            client = paramiko.Transport((hostname, port))
            client.connect(username=username, password=password)
            session = client.open_channel(kind='session')
            session.get_pty()
            session.invoke_shell()
            posix_shell(session)

        client.close()

    def check_firmware(self):
        pre = '{} Firmware versions'.format(self.oob_info['identifier'])
        state, msg = firmware.check_firmware(
            self.oob_info['custom_fields'], self.oob_params)

        nagios.result(state, msg, pre=pre)

    def check_ram(self):
        raise NotImplementedError('check-ram')

    def check_disks(self):
        raise NotImplementedError('check-disks')

    def get_disks(self):
        raise NotImplementedError('get-disks')

    def refresh_firmware(self):
        raise NotImplementedError('refresh-firmware')

    def ipmi_logs_analysed(self):
        raise NotImplementedError('ipmi-logs-analysed')

    def get_secrets(self):
        if not self.dcim.supports_secrets():
            self._print('secrets not supported')

        self._print('\n'.join(
            map(str, self.dcim.get_secrets(self.oob_info['info']))))

    def set_secret(self):
        if not self.dcim.supports_secrets():
            self._print('secrets not supported')

        parser = argparse.ArgumentParser()
        parser.add_argument('--secret-role', type=str, required=True)
        parser.add_argument('--secret-name', type=str, required=True)
        parser.add_argument('--secret-plaintext', type=str, required=True)
        args = parser.parse_args(self.command_args)

        r = self.dcim.set_secret(
            args.secret_role,
            self.oob_info['info'],
            args.secret_name,
            args.secret_plaintext)

        if r.status_code >= 300:
            self._print('Error {}'.format(r.text))

    def set_ipmi_password(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--secret-role', type=str, required=False)
        parser.add_argument('--new-password', type=str, required=True)
        args = parser.parse_args(self.command_args)

        stdout = self._execute(['user', 'list'], output=True).split('\n')
        header = stdout[0]
        name_start = header.find('Name')
        found = False
        for line in stdout[1:]:
            uid = line[:name_start].strip()
            username = line[name_start:line.find(' ', name_start)]

            if username == self.username:
                found = True
                logging.debug('ID of user {} is {}'.format(username, uid))
                break

        if not found:
            self._print('User {} not found'.format(self.username))
            return

        self._print(self._execute([
            'user', 'set', 'password', uid, args.new_password], output=True))

        if args.secret_role is not None:
            self._print('Updating {} NetBox secret'.format(args.secret_role))
            r = self.dcim.set_secret(args.secret_role, self.oob_info['info'],
                                     username, args.new_password)
            if r.status_code >= 300:
                logging.critical('Setting NetBox secret failed')
                logging.critical('Error {}:\n{}'.format(r.status_code, r.text))
            else:
                self._print('Successfully updated secret')

    def get_firmware(self):
        raise NotImplementedError('get-firmware')

    def check_firmware_updates(self):
        parser = argparse.ArgumentParser('check-firmware-updates')
        parser.add_argument('--download-to', type=str)
        parser.add_argument('--innoextract', action='store_true')

        args = parser.parse_args(self.command_args)

        try:
            fetcher = firmware_fetchers[self.oob_info['info']['device_type']]

        except KeyError as e:
            logging.error('Unsupported device type: {}'.format(e))
            sys.exit(-1)

        firmwares, downloads = fetcher(self.oob_params).get()

        if args.download_to is None:
            print(json.dumps(firmwares, indent=2))
            return

        try:
            os.makedirs(args.download_to, exist_ok=True)
        except OSError as e:
            logging.error('Could not create download directory: {}'.format(e))
            sys.exit(-1)

        for url in downloads:
            name = url[url.rfind('/') + 1:]
            file_name = os.path.join(args.download_to, name)
            logging.info('Downloading {} to {}'.format(url, file_name))
            try:
                with open(file_name, 'wb') as fout:
                    fout.write(urllib.request.urlopen(url).read())
            except (urllib.error.URLError, OSError) as e:
                logging.error('Failed: {}'.format(e))

            if args.innoextract and name.endswith('.exe'):
                logging.info('Extracting with innoextract')
                self._execute_cmd([
                    'innoextract', file_name, '-d', args.download_to])

    def firmware_upgrade(self):
        raise NotImplementedError('firmware-upgrade')

    def lenovo_rpc(self):
        raise NotImplementedError('lenovo-rpc')

    def clear_firmware_upgrade_logs(self):
        host = self.oob_info['ipmi'].replace('https://', '')

        sel_errors = self._get_sel_errors(host)
        if all(self._sel_is_firmware_upgrade(err) for err in sel_errors):
            self.clear_ipmi_logs()

    def _get_ipmi_address(self, cmd_args):
        parser = argparse.ArgumentParser('bmcmanager refresh-ipmi-address')
        parser.add_argument(
            '--type', choices=['ipv4', 'macaddress'], required=True)
        parser.add_argument(
            '--scheme', choices=['http', 'https', ''], default='https')
        parser.add_argument(
            '--domain', help='Domain name, only with type "macaddress"')
        args = parser.parse_args(cmd_args)

        regex = {
            'ipv4': r'^IP Address\s*:\s*(?P<addr>\d+(\.\d+){3})',
            'macaddress':
                r'MAC Address\s*:\s*(?P<addr>[a-f0-9]{2}(\:[a-f0-9]{2}){5})',
        }.get(args.type)

        if regex is None:
            logging.error('Unknown IPMI address type: {}'.format(args.type))
            return ''

        stdout = self._execute(['lan', 'print'], output=True)

        m = next(re.finditer(regex, stdout, re.MULTILINE), None)
        if m is None:
            logging.error('No IPMI address found')
            return

        addr = m.group('addr')
        if args.type == 'macaddress':
            addr = addr.replace(':', '').upper()
            if args.domain:
                addr = '{}.{}'.format(addr, args.domain.lstrip('.'))
        if args.scheme:
            addr = '{}://{}'.format(args.scheme, addr)

        return addr

    def refresh_ipmi_address(self):
        addr = self._get_ipmi_address(self.command_args)
        custom_fields = {'IPMI': addr}
        logging.info('Patching custom fields: {}'.format(custom_fields))
        if not self.dcim.set_custom_fields(self.oob_info, custom_fields):
            logging.error('Failed to refresh IPMI')

    def get_ipmi_address(self):
        addr = self._get_ipmi_address(self.command_args)
        self._print(addr)


class OobError(Exception):
    pass
