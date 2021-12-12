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


from enum import Enum
import logging
import os
import re
import shlex
import subprocess
import sys
from time import sleep

import paramiko

from bmcmanager.interactive import posix_shell
from bmcmanager.utils import firmware
from bmcmanager import nagios

LOG = logging.getLogger(__name__)

if sys.platform == "darwin":
    BROWSER_OPEN = "open"
else:
    BROWSER_OPEN = "xdg-open"


class IPMISelOutput(Enum):
    """
    Column indices for ipmi-sel output.
    """

    ID = 0
    DATE = 1
    TIME = 2
    NAME = 3
    TYPE = 4
    STATE = 5
    EVENT = 6


class IPMISensorsOutput(Enum):
    """
    Column indices for ipmi-sensors output
    """

    ID = 0
    NAME = 1
    TYPE = 2
    STATE = 3
    VALUE = 4
    UNIT = 5
    # UNUSED_1 = 6
    CRITL = 7
    WARNL = 8
    WARNH = 9
    CRITH = 10
    # UNUNSED_2 = 11
    DESC = 12


class OobBase(object):
    """
    Base OOB class
    """

    URL_LOGIN = "/rpc/WEBSES/create.asp"
    URL_VALIDATE = "/rpc/WEBSES/validate.asp"
    URL_VNC = "/Java/jviewer.jnlp?EXTRNIP={}&JNLPSTR=JViewer"

    def __init__(self, parsed_args, dcim, oob_config, oob_info):
        self.parsed_args = parsed_args
        self.oob_info = oob_info
        self.dcim = dcim
        self.oob_config = oob_config
        self.username = self.oob_config["username"]
        self.password = self.oob_config["password"]
        self.nfs_share = self.oob_config["nfs_share"]
        self.http_share = self.oob_config["http_share"]

    def _print(self, msg):
        # TODO: remove this, use normal log messages
        LOG.info("[%s] %s", self.oob_info["identifier"], msg)

    def info(self):
        info = self.oob_info["info"]

        columns = info.keys()
        values = [info[col] for col in columns]

        return columns, values

    def _wait_for_machine_power_status(self, status: str):
        while 1:
            LOG.debug("Waiting for machine status %s", status)
            if status in self._ipmitool(["chassis", "power", "status"]):
                break

            sleep(3)

    def _get_http_ipmi_host(self):
        ipmi_host = self.oob_info["ipmi"]
        if not ipmi_host.startswith("http"):
            ipmi_host = "https://{}".format(ipmi_host)

        return ipmi_host

    def open(self):
        self._check_call([BROWSER_OPEN, self._get_http_ipmi_host()])

    def ssh(self):
        if self.parsed_args.wait:
            self._wait_for_machine_power_status("on")

        # TODO: the asset_tag should not be the primary address of the host
        host = self.oob_info["asset_tag"]
        if not host:
            LOG.fatal("No asset_tag defined for %s", self.oob_info["identifier"])
            return

        self._check_call(["ssh", host])

    # command is an array
    def _ipmitool_cmd(self, command):
        host = self.oob_info["ipmi"].replace("https://", "")
        return [
            "ipmitool",
            *self.dcim.format_ipmitool_credentials(host, self.username, self.password),
            *command,
        ]

    def _ipmitool(self, command):
        return self._check_output(self._ipmitool_cmd(command))

    def _check_call(self, command):
        command = [str(c) for c in command]
        LOG.debug("Executing %s", shlex.join(command))
        return subprocess.check_call(command)

    def _check_output(self, command):
        command = [str(c) for c in command]
        LOG.debug("Executing %s", shlex.join(command))
        return subprocess.check_output(command).decode("utf-8")

    def identify(self):
        if self.parsed_args.off:
            arg = 0
        else:
            arg = self.parsed_args.on or "force"

        self._print(self._ipmitool(["chassis", "identify", str(arg)]).strip())

    def status(self):
        lines = self._ipmitool(["chassis", "status"]).strip().split("\n")
        columns, values = [], []
        for line in lines:
            try:
                key, value = line.split(":")
            except ValueError:
                continue

            columns.append(key.strip())
            values.append(value.strip())

        return columns, values

    def power_status(self):
        self._print(self._ipmitool(["chassis", "power", "status"]).strip())

    def power_on(self):
        self._print(self._ipmitool(["chassis", "power", "on"]).strip())

    def power_off(self):
        cmd = ["chassis", "power"]
        if self.parsed_args.force:
            cmd.append("off")
        else:
            cmd.append("soft")

        self._print(self._ipmitool(cmd))
        if self.parsed_args.wait:
            self._wait_for_machine_power_status("off")

    def power_cycle(self):
        self._print(self._ipmitool(["chassis", "power", "cycle"]))

    def power_reset(self):
        self._print(self._ipmitool(["chassis", "power", "reset"]))

    def boot_pxe(self):
        self._print(self._ipmitool(["chassis", "bootdev", "pxe"]))

    def boot_local(self):
        self._print(self._ipmitool(["chassis", "bootdev", "disk"]))

    def ipmi_reset(self):
        cmd = ["mc", "reset", "cold" if self.parsed_args.force else "warm"]
        self._print(self._ipmitool(cmd))

    def ipmi_logs(self):
        lines = self._ipmitool(["sel", "list"]).strip().split("\n")

        columns = ["id", "date", "time", "name", "event", "state"]
        values = [list(map(str.strip, line.split("|"))) for line in lines]

        return columns, values

    def clear_ipmi_logs(self):
        self._print(self._ipmitool(["sel", "clear"]).strip())

    def console(self):
        raise NotImplementedError("console")

    def diagnostics(self):
        raise NotImplementedError("diagnostics")

    def autoupdate(self):
        raise NotImplementedError("autoupdate")

    def upgrade(self):
        raise NotImplementedError("upgrade")

    def idrac_info(self):
        raise NotImplementedError("idrac-info")

    def remove_autoupdate(self):
        raise NotImplementedError("remove-autoupdate")

    def flush_jobs(self):
        raise NotImplementedError("flush-jobs")

    def pdisks_status(self):
        raise NotImplementedError("pdisks-status")

    def storage_status(self):
        raise NotImplementedError("storage-status")

    def controllers_status(self):
        raise NotImplementedError("controllers-status")

    def system_ram(self):
        raise NotImplementedError("system-ram")

    def factory_reset(self):
        raise NotImplementedError("factory-reset")

    def lock_power_switch(self):
        raise NotImplementedError("lock-power-switch")

    def unlock_power_switch(self):
        raise NotImplementedError("unlock-power-switch")

    def _ipmi_sensors_cmd(self, host, username, password, args=[]):
        if os.getenv("XDG_CACHE_HOME"):
            cache_dir_arg = "--sdr-cache-dir=$XDG_CACHE_HOME"
            args = [*args, os.path.expandvars(cache_dir_arg)]

        return [
            "ipmi-sensors",
            *self.dcim.format_freeipmi_credentials(host, username, password),
            "--quiet-cache",
            "--sdr-cache-recreate",
            "--interpret-oem-data",
            "--output-sensor-state",
            "--ignore-not-available-sensors",
            "--output-sensor-thresholds",
            *args,
        ]

    def _ipmi_sel_cmd(self, host, username, password, args=[]):
        return [
            "ipmi-sel",
            *self.dcim.format_freeipmi_credentials(host, username, password),
            "--output-event-state",
            "--interpret-oem-data",
            "--entity-sensor-names",
            "--sensor-types=all",
            "--ignore-sdr-cache",
            *args,
        ]

    def _ipmi_dcmi_cmd(self, host, username, password, args=[]):
        return [
            "ipmi-dcmi",
            *self.dcim.format_freeipmi_credentials(host, username, password),
            "--get-system-power-statistics",
            *args,
        ]

    def ipmi_sensors(self):
        host = self.oob_info["ipmi"].replace("https://", "")
        cmd = self._ipmi_sensors_cmd(host, self.username, self.password)
        lines = self._check_output(cmd).strip().split("\n")
        columns = list(map(str.strip, lines[0].split("|")))
        values = [list(map(str.strip, line.split("|"))) for line in lines[1:]]

        return (columns, values)

    def _format_sensor(self, sensor):
        return "- " + " | ".join(
            [
                sensor[x]
                for x in [
                    IPMISensorsOutput.ID.value,
                    IPMISensorsOutput.TYPE.value,
                    IPMISensorsOutput.NAME.value,
                    IPMISensorsOutput.VALUE.value,
                    IPMISensorsOutput.UNIT.value,
                    IPMISensorsOutput.DESC.value,
                ]
            ]
        )

    def __clear_na(self, x):
        return "" if x == "N/A" else x

    def _format_sensor_perfdata(self, sensor):
        if sensor[IPMISensorsOutput.VALUE.value] == "N/A":
            return ""

        warning = ""
        warning_low = self.__clear_na(sensor[IPMISensorsOutput.WARNL.value])
        warning_high = self.__clear_na(sensor[IPMISensorsOutput.WARNH.value])
        if warning_low or warning_high:
            warning = "{}:{}".format(warning_low, warning_high)

        critical = ""
        critical_low = self.__clear_na(sensor[IPMISensorsOutput.CRITL.value])
        critical_high = self.__clear_na(sensor[IPMISensorsOutput.CRITH.value])
        if critical_low or critical_high:
            critical = "{}:{}".format(critical_low, critical_high)

        result = "'{}'={}".format(
            sensor[IPMISensorsOutput.NAME.value], sensor[IPMISensorsOutput.VALUE.value]
        )
        if warning or critical:
            result = "{};{};{}".format(result, warning, critical)

        return result

    def _format_sel(self, sel):
        return "- " + " | ".join(
            [
                sel[x]
                for x in [
                    IPMISelOutput.ID.value,
                    IPMISelOutput.DATE.value,
                    IPMISelOutput.TIME.value,
                    IPMISelOutput.TYPE.value,
                    IPMISelOutput.NAME.value,
                    IPMISelOutput.EVENT.value,
                ]
            ]
        )

    def _get_sel_errors(self, host):
        cmd = self._ipmi_sel_cmd(host, self.username, self.password)
        logs = self._check_output(cmd)
        for line in reversed(logs.split("\n")[1:-1]):
            split = list(map(lambda x: x.strip(), line.split("|")))
            if split[IPMISelOutput.STATE.value] != "Nominal":
                yield split

    def _sel_is_firmware_upgrade(self, line):
        checks = {
            IPMISelOutput.DATE.value: "PostInit",
            IPMISelOutput.TIME.value: "PostInit",
            IPMISelOutput.TYPE.value: "Version Change",
        }
        return all(line[k] == v for k, v in checks.items())

    def check_ipmi(self):
        pre = "{} IPMI Status".format(self.oob_info["identifier"])
        try:
            host = self.oob_info["ipmi"].replace("https://", "")
        except:
            nagios.result(nagios.UNKNOWN, "No IPMI information", pre=pre)
            return

        perfdata = []
        cmd = self._ipmi_dcmi_cmd(host, self.username, self.password)
        try:
            dcmi_output = self._check_output(cmd)
        except Exception as e:
            LOG.exception(e)
            nagios.result(nagios.UNKNOWN, "ipmi-dcmi failed", pre=pre)
            return

        match = re.findall(r"Current Power\s*:\s*(\d+)", dcmi_output)
        if match:
            perfdata.append("'Current Power'={}".format(match[0]))

        sel_errors = list(self._get_sel_errors(host))

        cmd = self._ipmi_sensors_cmd(host, self.username, self.password)
        try:
            sensors = self._check_output(cmd)
        except Exception as e:
            LOG.exception(e)
            nagios.result(nagios.UNKNOWN, "ipmi-sensors failed", pre=pre)
            return

        sensor_warnings = []
        sensor_errors = []
        for line in sensors.split("\n")[1:-1]:
            split = list(map(lambda x: x.strip(), line.split("|")))

            data = self._format_sensor_perfdata(split)
            if data:
                perfdata.append(data)

            if split[IPMISensorsOutput.STATE.value] in ["Nominal", "N/A"]:
                continue
            elif split[IPMISensorsOutput.STATE.value] == "Warning":
                sensor_warnings.append(split)
            else:
                sensor_errors.append(split)

        status, msg, lines = nagios.OK, [], []
        if sensor_warnings:
            status = nagios.WARNING
            msg.append("{} sensors warning".format(len(sensor_warnings)))
            lines.extend(
                [
                    "Warning sensors:",
                    *map(lambda x: self._format_sensor(x), sensor_warnings),
                ]
            )
        if sensor_errors:
            status = nagios.CRITICAL
            msg.append("{} sensors critical".format(len(sensor_errors)))
            lines.extend(
                [
                    "Critical sensors:",
                    *map(lambda x: self._format_sensor(x), sensor_errors),
                ]
            )
        if sel_errors:
            status = nagios.CRITICAL
            msg.append("{} SEL entries".format(len(sel_errors)))
            sel_entries_header = "SEL entries:"

            # cap number of SEL entries returned
            if len(sel_errors) > 10:
                sel_entries_header += " (showing latest 10/{})".format(len(sel_errors))
                sel_errors = sel_errors[:10]

            lines.extend(
                [sel_entries_header, *map(lambda x: self._format_sel(x), sel_errors)]
            )

        perfdata = [" ".join(perfdata)]
        nagios.result(status, msg or "SEL, Sensors OK", lines, perfdata, pre)

    def creds(self):
        ipmi = self.oob_info["ipmi"].replace("https://", "")
        columns = ("address", "username", "password")
        values = (ipmi, self.username, self.password)
        return columns, values

    def ipmi_ssh(self):
        port = 22
        hostname = self.oob_info["ipmi"].replace("https://", "")
        username = self.username
        password = self.password

        if self.parsed_args.command:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=hostname, port=port, username=username, password=password
            )
            _, out, err = client.exec_command(" ".join(self.parsed_args.command))
            print(out.read().decode())
            if err:
                print(err.read().decode(), file=sys.stderr)
        else:
            client = paramiko.Transport((hostname, port))
            client.connect(username=username, password=password)
            session = client.open_channel(kind="session")
            session.get_pty()
            session.invoke_shell()
            posix_shell(session)

        client.close()

    def check_firmware(self):
        pre = "{} Firmware versions".format(self.oob_info["identifier"])
        state, msg = firmware.check_firmware(
            self.oob_info["custom_fields"], self.oob_config
        )

        nagios.result(state, msg, pre=pre)

    def check_ram(self):
        raise NotImplementedError("check-ram")

    def check_disks(self):
        raise NotImplementedError("check-disks")

    def get_disks(self):
        raise NotImplementedError("get-disks")

    def refresh_firmware(self):
        raise NotImplementedError("refresh-firmware")

    def ipmi_logs_analysed(self):
        raise NotImplementedError("ipmi-logs-analysed")

    def get_secrets(self):
        if not self.dcim.supports_secrets():
            LOG.fatal("Secrets not supported by DCIM")
            return

        secrets = self.dcim.get_secrets(self.oob_info["info"])

        columns = ["id", "role", "name", "plaintext"]
        values = [[secret[col] for col in columns] for secret in secrets]
        return columns, values

    def set_secret(self):
        if not self.dcim.supports_secrets():
            LOG.fatal("Secrets not supported by DCIM")
            return

        r = self.dcim.set_secret(
            self.parsed_args.secret_role,
            self.oob_info["info"],
            self.parsed_args.secret_name,
            self.parsed_args.secret_plaintext,
        )

        if r.status_code >= 300:
            self._print("Error {}".format(r.text))

    def ipmitool(self):
        self._check_call(self._ipmitool_cmd(self.parsed_args.args))

    def set_ipmi_password(self):
        args = self.parsed_args

        stdout = self._ipmitool(["user", "list"]).split("\n")
        header = stdout[0]
        name_start = header.find("Name")
        found = False
        for line in stdout[1:]:
            uid = line[:name_start].strip()
            username = line[name_start : line.find(" ", name_start)]

            if username == self.username:
                found = True
                LOG.debug("ID of user {} is {}".format(username, uid))
                break

        if not found:
            self._print("User {} not found".format(self.username))
            return

        self._print(self._ipmitool(["user", "set", "password", uid, args.new_password]))

        if args.secret_role is not None:
            self._print("Updating {} NetBox secret".format(args.secret_role))
            r = self.dcim.set_secret(
                args.secret_role, self.oob_info["info"], username, args.new_password
            )
            if r.status_code >= 300:
                LOG.critical("Setting NetBox secret failed")
                LOG.critical("Status Code: %s\nResponse: %s", r.status_code, r.text)
            else:
                self._print("Successfully updated secret")

    def get_firmware(self):
        raise NotImplementedError("get-firmware")

    def firmware_upgrade(self):
        raise NotImplementedError("firmware-upgrade")

    def lenovo_rpc(self):
        raise NotImplementedError("lenovo-rpc")

    def clear_firmware_upgrade_logs(self):
        host = self.oob_info["ipmi"].replace("https://", "")
        sel_errors = self._get_sel_errors(host)
        if all(self._sel_is_firmware_upgrade(err) for err in sel_errors):
            self.clear_ipmi_logs()

    def _get_ipmi_address(self):
        args = self.parsed_args
        regex = {
            "ipv4": r"^IP Address\s*:\s*(?P<addr>\d+(\.\d+){3})",
            "mac": r"MAC Address\s*:\s*(?P<addr>[a-f0-9]{2}(\:[a-f0-9]{2}){5})",
        }.get(args.address_type)

        if regex is None:
            LOG.error("Unknown address type: %s", args.address_type)
            return ""

        stdout = self._ipmitool(["lan", "print"])

        m = next(re.finditer(regex, stdout, re.MULTILINE), None)
        if m is None:
            LOG.error("No IPMI address found")
            return

        addr = m.group("addr")
        if args.address_type == "mac":
            addr = addr.replace(":", "").upper()
            if args.domain:
                addr = "{}.{}".format(addr, args.domain.lstrip("."))
        if args.scheme:
            addr = "{}://{}".format(args.scheme, addr)

        return addr

    def refresh_ipmi_address(self):
        addr = self._get_ipmi_address()
        custom_fields = {"IPMI": addr}
        LOG.info("Patching custom fields: %s", custom_fields)
        if not self.dcim.set_custom_fields(self.oob_info, custom_fields):
            LOG.error("Failed to refresh IPMI")

    def get_ipmi_address(self):
        addr = self._get_ipmi_address()
        return ("address",), (addr,)

    def open_dcim(self):
        self._check_call([BROWSER_OPEN, self.dcim.oob_url(self.oob_info)])
