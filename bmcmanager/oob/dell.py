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
import sys
import time
import paramiko

from subprocess import Popen

from bmcmanager.oob.base import OobBase
from bmcmanager.logs import log


class Dell(OobBase):
    def console(self):
        ipmi_host = self.oob_info['ipmi']
        try:
            Popen(['moob', '-u', '{}'.format(self.username),
                   '-p', '{}'.format(self.password),
                   '-m', ipmi_host.replace('https://', '')])
        except OSError:
            print('Please run "gem install moob"')
            sys.exit(10)

    def _ssh(self, command):
        # performs command using ssh
        # returns decoded output

        nbytes = 4096
        port = 22
        hostname = self.oob_info['ipmi'].replace('https://', '')
        username = self.username
        password = self.password

        client = paramiko.Transport((hostname, port))
        client.connect(username=username, password=password)
        stdout_data = []
        stderr_data = []
        session = client.open_channel(kind='session')
        session.exec_command(command)
        while True:
            if session.recv_ready():
                stdout_data.append(session.recv(nbytes))
            if session.recv_stderr_ready():
                stderr_data.append(session.recv_stderr(nbytes))
            if session.exit_status_ready():
                break
        output = b''.join(stdout_data)
        session.close()
        client.close()

        return output.decode('utf-8')

    def _find_jid(self, output):
        try:
            return re.search(r'JID_.*', output).group(0)
        except AttributeError:
            print('No Job ID found.\nCommand output: ', output)
            sys.exit(10)

    def _confirm_job(self, jid):
        try:
            re.search(r'Job completed successfully', jid).group(0)
        except AttributeError:
            print('Job did not complete successfully.\nCommand output: ', jid)
            sys.exit(10)

    def diagnostics(self):
        jobqueue_view = 'racadm jobqueue view -i {}'
        output = self._ssh('racadm techsupreport collect')
        jid = self._find_jid(output)
        log.info('Sleeping for 3 minutes to collect the TSR report')
        time.sleep(180)
        view_output = self._ssh(jobqueue_view.format(jid))
        self._confirm_job(view_output)
        output = self._ssh('racadm techsupreport export -l {}'.format(
            self.nfs_share))
        jid = self._find_jid(output)
        view_output = self._ssh(jobqueue_view.format(jid))
        self._confirm_job(view_output)

    def autoupdate(self):
        enable_updates_output = self._ssh(
            'racadm set lifecycleController.lcattributes.AutoUpdate Enabled')
        schedule_updates_output = self._ssh(
            'racadm autoupdatescheduler create -l {} '
            '-f grnet_1.00_Catalog.xml -a 0 -time 08:30 '
            '-dom * -wom * -dow * -rp 1'.format(self.http_share))
        print(enable_updates_output)
        print(schedule_updates_output)

    def upgrade(self):
        http_addr = self.http_share.strip('http:/')
        self._ssh('racadm update -f {} -e {} -t HTTP -a FALSE'.format(
            'grnet_1.00_Catalog.xml', http_addr))

    def idrac_info(self):
        firm_info = 'racadm get idrac.info'
        bios_info = 'racadm get bios.sysinformation'
        print(self._ssh(firm_info))
        print(self._ssh(bios_info))

    def clear_autoupdate(self):
        clear_command = 'racadm autoupdatescheduler clear'
        print(self._ssh(clear_command))

    def flush_jobs(self):
        flush_command = 'racadm jobqueue delete --all'
        print(self._ssh(flush_command))

    def pdisks_status(self):
        pdisks_status_command = 'racadm storage get pdisks -o'
        print(self._ssh(pdisks_status_command))

    def storage_status(self):
        storage_status_command = 'racadm storage get status'
        print(self._ssh(storage_status_command))

    def controllers_status(self):
        controllers_status_command = 'racadm storage get controllers -o'
        print(self._ssh(controllers_status_command))
