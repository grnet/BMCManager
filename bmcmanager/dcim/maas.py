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

import logging

from maas.client.bones import SessionAPI

from bmcmanager.dcim.base import DcimBase, DcimError

LOG = logging.getLogger(__name__)


class MaaS(DcimBase):
    def __init__(self, name, args):
        super(MaaS, self).__init__(name, args)
        self._session = None

        if not self.config.maas_api_url:
            raise DcimError("MaaS API URL is not set, see README.md")
        if not self.config.maas_api_key:
            raise DcimError("MaaS API Key is not set, see README.md")

    def session(self) -> SessionAPI:
        """
        Return a sessions to the MaaS server. Subsequent calls reuse the same
        connection
        """
        if self._session:
            return self._session

        LOG.info("Connecting to %s", self.config.maas_api_url)
        _, self._session = SessionAPI.connect(
            self.config.maas_api_url, apikey=self.config.maas_api_key
        )

        return self._session

    def _get_manufacturer(self, machine_data: dict) -> str:
        mainboard_vendor = machine_data["hardware_info"]["mainboard_vendor"].lower()
        if mainboard_vendor != "unknown":
            return mainboard_vendor

        return machine_data["hardware_info"]["system_vendor"].lower()

    def _get_device_type(self, machine_data: dict) -> str:
        mainboard_product = machine_data["hardware_info"]["mainboard_product"].lower()
        if mainboard_product != "unknown":
            return mainboard_product

        return machine_data["hardware_info"]["system_product"].lower()

    def get_oobs(self):
        for machine in self.session().Machines.read(hostname=[self.identifier]):
            power = self.session().Machine.power_parameters(
                system_id=machine["system_id"]
            )
            yield {
                "asset_tag": "",
                "ipmi": power["power_address"],
                "oob": self._get_manufacturer(machine),
                "info": {
                    "id": machine["system_id"],
                    "name": machine["hostname"],
                    "display_name": machine["hostname"],
                    "serial": machine["hardware_info"]["system_serial"],
                    "ipmi": power["power_address"],
                    "manufacturer": self._get_manufacturer(machine),
                    "device_type": self._get_device_type(machine),
                    "bios": machine["owner_data"].get("BIOS", ""),
                    "tsm": machine["owner_data"].get("TSM", ""),
                    "psu": machine["owner_data"].get("PSU", ""),
                    "site": machine["domain"]["name"],
                    "status": machine["status_name"],
                },
                "identifier": machine["hostname"],
                "custom_fields": machine["owner_data"],
            }

    def get_ipmi_credentials_from_dcim(self, oob_info):
        power = self.session().Machine.power_parameters(
            system_id=oob_info["info"]["id"]
        )
        return power["power_address"], power["power_user"], power["power_pass"]

    def set_custom_fields(self, oob_info, custom_fields):
        raise DcimError("not support by MaaS DCIM")

    def oob_url(self, oob_info):
        if not self.config.maas_ui_url:
            raise DcimError("MaaS UI URL is not set, see README.md")

        return "{}/MAAS/l/machine/{}".format(
            self.config.maas_ui_url, oob_info["info"]["id"]
        )
