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

from datetime import datetime
import json
import urllib

from bmcmanager.logs import log
from bmcmanager.firmwares.base import LatestFirmwareFetcher


TRACKED_FIRMWARE = {
    'ThinkServer System Manager (TSM) Update Bundle File - ThinkServer Systems': 'TSM',  # noqa
    'Firmware for Avago 9340-8i/ 9364-8i/ 9380-8e SAS3 RAID and RAID 720i/720ix AnyRAID Adapter - ThinkServer Systems': 'RAID',  # noqa
    'Firmware for Avago 9240-8i SAS RAID and ThinkServer 510i AnyRAID Adapter  - ThinkServer Systems': 'RAID',  # noqa
    'Firmware for LSI 9270CV-8i/ 9286CV-8e SAS RAID Card for Windows and Linux - ThinkServer Systems': 'RAID',  # noqa
    'Firmware Update for Delta DPS-750AB-21A PT750W Power Supply Unit (PSU) - ThinkServer RD350, RD450, RD550, RD650, TD350': 'PSU',  # noqa
    'Firmware Update for Delta DPS-750AB-20A TT750W Power Supply Unit (PSU) - ThinkServer RD350, RD450, RD550, RD650, TD350': 'PSU',  # noqa
    'Firmware Update for Liteon PS-2751-3L PT750W Power Supply Unit (PSU) - ThinkServer RD350, RD450, RD550, RD650, TD350': 'PSU',  # noqa
    'Firmware Update for Liteon PS-2551-6L-LF PT550W Power Supply Unit (PSU) - ThinkServer RD350, RD450, RD550, RD650, TD350': 'PSU',  # noqa
    'Firmware Update for Delta DPS-550AB-5A PT550W Power Supply Unit (PSU) - ThinkServer RD350, RD450, RD550, RD650, TD350': 'PSU',  # noqa
    'Firmware Update for Delta DPS-1100EBA PT1100W Power Supply Unit (PSU) - ThinkServer  RD450, RD550, RD650, TD350': 'PSU',  # noqa
}


LENOVO_URL = 'https://datacentersupport.lenovo.com/gr/en/api/v4/downloads/drivers?productId=servers/{}/{}'  # noqa


class LenovoBase(LatestFirmwareFetcher):
    model_name = 'model-name'       # replace in sub-classes, e.g. 'thinkserver'
    device_name = 'device-name'     # replace in sub-classes, e.g. 'rd550'
    extra_firmware = {
        # add here any extra firmware items to track
    }

    def get(self):
        url = LENOVO_URL.format(self.model_name, self.device_name)
        try:
            log.debug('GET {}'.format(url))
            response = json.loads(urllib.request.urlopen(url).read())
            items = response['body']['DownloadItems']
        except (json.JSONDecodeError, urllib.error.URLError) as e:
            log.error('Could not fetch URL: {}'.format(e))
            return {}, []
        except KeyError as e:
            log.error('Invalid data format: {}'.format(e))
            return {}, []

        tracked_firmware = {**TRACKED_FIRMWARE, **self.extra_firmware}

        result = []
        downloads = []
        for item in items:
            try:
                component = tracked_firmware.get(item['Title'])
                if component is None:
                    continue

                fw = next(filter(
                    lambda f: f['TypeString'] != 'TXT README', item['Files']))

                downloads.append(fw['URL'])

                timestamp = datetime.fromtimestamp(fw['Date']['Unix'] / 1000)
                result.append({
                    'component': component,
                    'name': item['Title'],
                    'version': item['SummaryInfo']['Version'],
                    'date': str(timestamp),
                    'file': fw['URL'],
                })

            except ValueError as e:
                log.error('Invalid data format: {}'.format(e))

            except KeyError as e:
                log.error('Missing information: {}'.format(e))

        return result, downloads


class RD550(LenovoBase):
    model_name = 'thinkserver'
    device_name = 'rd550'
    extra_firmware = {
        'BIOS Update Bundle File - ThinkServer RD550': 'BIOS',
    }


class RD350(LenovoBase):
    model_name = 'thinkserver'
    device_name = 'rd350'
    extra_firmware = {
        'ThinkServer BIOS Update Bundle File - ThinkServer RD350, RD450': 'BIOS',  # noqa
    }
